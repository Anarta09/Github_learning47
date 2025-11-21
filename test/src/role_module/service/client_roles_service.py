import requests
from fastapi import status
from typing import Union, List, Dict
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from utils.scripts.headers import Headers
from config import settings
from utils.token import get_current_admin_token
from custom_exeptions import CustomException, err_constants, Messages
import logging

# Schemas
from role_module.schema.request import CreateRoleModel
from role_module.schema.response import (
    RolesResponseModel,
    DeleteRolesResponseModel,
    ClientDeleteRolesResultModel,
)
# DB Models
from models.client_model import Client
from models.role_detail_model import RoleDetail
from models.role_log_model import RoleLog
# Services
from role_module.service.role_detail_service import RoleDetailService
from role_module.service.role_log_service import RoleLogService
# Helpers
from role_module.service import role_helpers

logger = logging.getLogger(__name__)

# ---------------- Main Service ----------------
class ClientRoleService:
    """
    Service for managing client roles in Keycloak and local DB.
    Handles creation, reactivation, deletion (soft), and policy management.
    """

    def __init__(self):
        self.admin_url = settings.ADMIN_URL.rstrip("/")
        self.realm = settings.REALM
        self.role_detail_service = RoleDetailService()
        self.role_log_service = RoleLogService()

    # -------- List All Roles for a Client --------
    def list_roles(self, client_id: str, clients: List[Dict]):
        """Fetch all roles for a specific client from Keycloak."""
        try:
            match = role_helpers.get_matching_client(client_id, clients)
            token = get_current_admin_token()
            headers = Headers.get_json_headers(token)

            url = f"{self.admin_url}/clients/{match['id']}/roles"
            resp = requests.get(url, headers=headers)
            resp.raise_for_status()

            return {"client_id": client_id, "roles": resp.json()}

        except CustomException as err:
            logger.error(f"client_role_service.py:list_roles ---> {err}", exc_info=True)
            raise err

        except Exception as err:
            logger.error(f"Exception while listing roles ---> {err}")
            raise CustomException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=Messages.LIST_ROLES_FAILED,
                details=err_constants.LIST_ROLES_FAILED
            )
    

    # -------- Create Roles (Universal Handling) --------
    def create_roles_universal(
        self,
        client_ids: Union[str, List[str]],
        roles: Union[CreateRoleModel, List[CreateRoleModel], str, List[str]],
        clients: List[Dict],
        db: Session,
    ) -> RolesResponseModel:
        """
        Create roles for one or multiple clients in Keycloak and update DB accordingly.
        Handles all combinations of (single/multiple) clients and roles.
        """
        try:
            client_ids, roles = role_helpers.normalize_role_inputs(client_ids, roles)
            token = get_current_admin_token()
            headers = Headers.get_json_headers(token)

            results = {}

            for cid in client_ids:
                client_match = role_helpers.get_matching_client(cid, clients)

                # Delegate all per-role logic to a helper
                client_result = role_helpers.process_roles_for_client(
                    db=db,
                    roles=roles,
                    client_match=client_match,
                    headers=headers,
                    role_detail_service=self.role_detail_service,
                    role_log_service=self.role_log_service,
                    admin_url=self.admin_url,
                )

                results[cid] = client_result

            return RolesResponseModel(results=results)

        except CustomException as err:
            logger.error(f"client_role_service.py:create_roles_universal ---> {err}", exc_info=True)
            raise err

        except Exception as err:
            logger.error(f"Exception while creating roles ---> {err}")
            raise CustomException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=Messages.CREATE_ROLES_FAILED,
                details=err_constants.ROLES_CREATION_FAILED
            )

    # -------- Delete Roles (Soft Delete + Logging + RoleLog Update) --------
    def delete_roles_for_clients(
        self,
        roles: List[Union[str, CreateRoleModel, Dict]],
        client_ids: List[str],
        clients: List[Dict],
        db: Session,
        updated_by: str = "system",
    ) -> DeleteRolesResponseModel:
        """
        Soft delete roles (mark as inactive in DB and RoleLog), remove them from Keycloak,
        and delete their corresponding authorization policies.
        Returns a single DeleteRolesResponseModel with results per client.
        """
        try:
            token = get_current_admin_token()
            headers = Headers.get_json_headers(token)
            client_results = []

            for client_display_id in client_ids:
                deleted_roles = []
                try:
                    # Lookup client in Keycloak
                    match = role_helpers.get_matching_client(client_display_id, clients)
                    client_uuid = match["id"]

                    # Lookup client in DB
                    client_record = db.query(Client).filter(Client.client_name == client_display_id).first()
                    if not client_record:
                        raise CustomException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            message=Messages.CLIENTS_NO_MATCH,
                            details=err_constants.CLIENT_NOT_FOUND
                        )

                    # Process each role via helper
                    for role_obj in roles:
                        role_name = role_helpers.safe_name(role_obj)
                        deletion_result = role_helpers.delete_role_full(
                            db=db,          
                            role_name=role_name,
                            client_display_id=client_display_id,  
                            clients=clients,
                            role_log_service=self.role_log_service,
                            role_detail_service=self.role_detail_service
                        )
                        deleted_roles.append(deletion_result)

                    # Append per-client result
                    client_results.append({
                        "client_id": client_display_id,
                        "deleted_roles": deleted_roles
                    })

                except CustomException as inner_err:
                    logger.error(f"client_role_service.py:delete_roles_for_clients ---> {inner_err}", exc_info=True)
                    client_results.append({
                        "client_id": client_display_id,
                        "deleted_roles": [{"error": str(inner_err)}]
                    })

                except Exception as inner_err:
                    logger.error(f"Exception while deleting roles for client '{client_display_id}' ---> {inner_err}")
                    client_results.append({
                        "client_id": client_display_id,
                        "deleted_roles": [{"error": str(inner_err)}]
                    })

            # Return all client results in a single DeleteRolesResponseModel
            return DeleteRolesResponseModel(
                 message="Role deletion completed (soft delete + policy cleanup applied)",
                results=client_results
                    )


        except CustomException as err:
            logger.error(f"client_role_service.py:delete_roles_for_clients ---> {err}", exc_info=True)
            raise err

        except Exception as err:
            logger.error(f"Exception while performing delete_roles_for_clients ---> {err}")
            raise CustomException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=Messages.DELETE_ROLES_FAILED,
                details=err_constants.KEYCLOAK_ROLE_DELETE_FAILED
            )
