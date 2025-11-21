import json
import time
import logging
import requests
from requests.exceptions import ConnectionError, Timeout, RequestException
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, before_sleep_log
from typing import Optional, List, Dict
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import status
from config import settings
from client_creation_module.schema.request import CreateClientModel
from models.client_model import Client as ClientModel
from models.client_logs_model import ClientLogs
from models.role_detail_model import RoleDetail
from utils.token import get_current_admin_token
from utils.scripts.headers import Headers
from client_creation_module.service import client_helpers
from custom_exeptions import CustomException, err_constants, Messages
from role_module.service import role_helpers
from role_module.service.role_log_service import RoleLogService

logger = logging.getLogger(__name__)


class ClientService:
    """ Service class for managing Keycloak clients and synchronizing them with the local database.
    Handles client creation, reactivation, deletion, and retrieval operations with robust
    error handling, logging, and retry mechanisms."""

    def __init__(self):
        try:
            self.admin_url = settings.ADMIN_URL
            self.role_log_service = RoleLogService()
        except CustomException as err:
            logger.error(f"client_service:__init__ ---> {err}", exc_info=True)
            raise err
        except Exception as err:
            logger.error(f"Exception while initializing ClientService ---> {err}")
            raise CustomException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=Messages.CLIENTSERVICE_INIT_FAILED,
                details=err_constants.INTERNAL_SERVER_ERROR
            )

    # ------------------ Safe HTTP Requests ------------------
    @retry(
        stop=stop_after_attempt(5),  # Retry up to 5 times
        wait=wait_exponential(multiplier=1, min=1, max=16),  # Exponential backoff
        retry=retry_if_exception_type((requests.ConnectionError, requests.Timeout, requests.RequestException)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True  # Raise exception if all retries fail
    )
    def safe_request(self, method: str, url: str, **kwargs):
        """
        Execute HTTP request with automatic retries using Tenacity.
        Raises CustomException in a standardized format if the request fails.
        """
        try:
            resp = requests.request(method, url, timeout=15, **kwargs)
            resp.raise_for_status()
            return resp

        except (requests.ConnectionError, requests.Timeout, requests.RequestException) as e:
            # Trigger Tenacity retry
            logger.warning(f"safe_request connection error: {e}. Retrying...")
            raise

        except Exception as err:
            # Wrap any unexpected exception in CustomException
            logger.error(f"Unexpected exception in safe_request ---> {err}", exc_info=True)
            raise CustomException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                message=Messages.SAFE_REQUEST_EXECUTION_FAILED,
                details=err_constants.INTERNAL_SERVER_ERROR
            )

    # ------------------ Get Clients ------------------
    def get_clients(self, clients: Optional[List[Dict]] = None, search: Optional[str] = None):
        """ Get all Keycloak clients or filter them by a search keyword."""
        try:
            token = get_current_admin_token()
            if not token:
                raise CustomException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    message=Messages.ADMIN_TOKEN_UNAVAILABLE,
                    details=err_constants.ERROR_ADMIN_TOKEN_FETCH
                )

            headers = Headers.get_json_headers(token)
            url = f"{self.admin_url}/clients"
            response = self.safe_request("GET", url, headers=headers)

            if response.status_code != 200:
                raise CustomException(
                    status_code=response.status_code,
                    message=Messages.CLIENTS_FETCH_FAILED,
                    details=err_constants.KEYCLOAK_CLIENTS_FETCH_FAILED
                )

            fetched_clients = response.json()
            clients_to_return = clients if clients is not None else fetched_clients
            
            if search:
                search_lower = search.lower()
                clients_to_return = [
                    c for c in clients_to_return
                    if search_lower in c.get("clientId", "").lower()
                    or search_lower in c.get("name", "").lower()
                    or search_lower in c.get("id", "").lower()
                ]
                
                if not clients_to_return:
                    raise CustomException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        message=Messages.CLIENTS_NO_MATCH,
                        details=err_constants.CLIENT_SEARCH_NO_RESULTS
                    )
                    
            return clients_to_return

        except CustomException as err:
            logger.error(f"client_service:get_clients ---> {err}", exc_info=True)
            raise err
        except Exception as err:
            logger.error(f"Exception while fetching clients ---> {err}")
            raise CustomException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=Messages.CLIENTS_FETCH_FAILED,
                details=err_constants.KEYCLOAK_CLIENTS_FETCH_FAILED
            )

    # ------------------ Create or Reactivate Clients ------------------
    def create_clients(self, client_data_list: List[CreateClientModel], db: Session):
        """Create or reactivate multiple clients in Keycloak and DB."""
        try:
            results = []
            token = get_current_admin_token()
            if not token:
                raise CustomException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    message=Messages.ADMIN_TOKEN_UNAVAILABLE,
                    details=err_constants.ERROR_ADMIN_TOKEN_FETCH
                )

            headers_base = Headers.get_json_headers(token)
            client_helpers.fetch_existing_clients(self, headers_base)

            for client_data in client_data_list:
                client_helpers.process_single_client(self, client_data, db, results)

            return True

        except CustomException as err:
            logger.error(f"client_service:create_clients ---> {err}", exc_info=True)
            raise err
        except Exception as err:
            logger.error(f"Exception while creating or reactivating clients ---> {err}")
            raise CustomException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message=Messages.CLIENT_CREATION_FAILED,
                details=err_constants.CLIENT_CREATION_FAILED
            )

    # ------------------ Delete Clients ------------------
    def delete_clients(self, client_ids, clients, db: Session):
     
        """Delete clients from Keycloak and mark them inactive in the database, including their client-specific scopes."""
        try:
            results = []
            for client_id in client_ids:
                try:
                    matching_client = next((c for c in clients if c.get("clientId") == client_id), None)
                    if not matching_client:
                        raise CustomException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            message=Messages.CLIENT_NOT_FOUND_KEYCLOAK,
                            details=err_constants.CLIENT_NOT_FOUND_KEYCLOAK
                        )

                    db_client = db.query(ClientModel).filter(
                        ClientModel.client_name == client_id,
                        ClientModel.is_active == True
                    ).first()

                    # Mark client inactive in DB
                    if db_client:
                        db_client.is_active = False
                        db_client.last_updated_at = datetime.now(timezone.utc)
                        db_client.last_updated_by = "system"
                        db.commit()
                        client_helpers.log_client_action(
                            db=db,
                            client_id=db_client.id,
                            client_uuid=matching_client["id"],
                            action="DELETE",
                            is_active=False,
                        )

                        role_helpers.deactivate_roles_for_deleted_client(client_id=db_client.client_name, db=db,role_log_service= self.role_log_service)

                    # ----------------- Delete client-specific scopes first -----------------
                    try:
                        client_helpers.delete_client_scopes(self, client_uuid=matching_client["id"])
                    except CustomException as scope_err:
                        logger.error(
                            f"Failed to delete client scopes for client {client_id} ---> {scope_err}"
                        )

                    # Delete the client from Keycloak
                    token = get_current_admin_token()
                    headers = Headers.get_json_headers(token)
                    resp = self.safe_request(
                        "DELETE", f"{self.admin_url}/clients/{matching_client['id']}", headers=headers
                    )

                    if resp.status_code not in (200, 204):
                        raise CustomException(
                            status_code=resp.status_code,
                            message=Messages.KEYCLOAK_CLIENT_DELETE_FAILED,
                            details=err_constants.CLIENT_KEYCLOAK_DELETE_FAILED
                        )

                    results.append({
                        "client_id": client_id,
                        "status": "success",
                        "message": f"Client '{client_id}' deleted successfully.",
                    })

                except CustomException as err:
                    logger.error(f"client_service:delete_clients (inner) ---> {err}", exc_info=True)
                    results.append({
                        "client_id": client_id,
                        "status": "failed",
                        "message": err.message
                    })
                except Exception as err:
                    logger.error(f"Exception while deleting client {client_id} ---> {err}")
                    results.append({
                        "client_id": client_id,
                        "status": "failed",
                        "message": str(err)
                    })
            return results

        except CustomException as err:
            logger.error(f"client_service:delete_clients ---> {err}", exc_info=True)
            raise err
        except Exception as err:
            logger.error(f"Exception while deleting clients ---> {err}")
            raise CustomException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=Messages.CLIENT_DELETION_FAILED,
                details=err_constants.CLIENT_KEYCLOAK_DELETE_FAILED
            )

