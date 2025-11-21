import time
import logging
from fastapi import status
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Tuple,Optional
from utils.scripts.headers import Headers
from custom_exeptions import CustomException, err_constants,Messages
from utils.token import get_current_admin_token
from models.client_model import Client as ClientModel
from models.client_logs_model import ClientLogs
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


# ------------------ Client Payload ------------------
def prepare_client_payload(client_data) -> Tuple[dict, str]:
    """Prepare Keycloak client payload. Returns payload and import_from_client if any."""
    try:
        payload = client_data.dict(
            exclude={
                "client_name",
                "company_name",
                "email",
                "client_bucket_path",
                "client_bucket_name",
                "status",
            }
        )
        payload["authorizationServicesEnabled"] = True
        if hasattr(client_data, "client_name"):
            payload["name"] = client_data.client_name
        import_from_client = payload.pop("import_from_client", None)
        return payload, import_from_client

    except CustomException as err:
        logger.error(f"client_service:prepare_client_payload ---> {err}", exc_info=True)
        raise err

    except Exception as err:
        logger.error(f"Exception while preparing client payload ---> {err}")
        raise CustomException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=Messages.ERROR_PREPARING_CLIENT_PAYLOAD,
            details=err_constants.ERROR_PREPARING_CLIENT_PAYLOAD
        )


# ------------------ Database Client ------------------
def fetch_db_client(db: Session, client_id: str):
    """Get a client from the DB by clientId."""
    try:
        return db.query(ClientModel).filter(ClientModel.display_client_id == client_id).first()

    except CustomException as err:
        logger.error(f"client_service:fetch_db_client ---> {err}", exc_info=True)
        raise err

    except Exception as err:
        logger.error(f"Exception while fetching DB client ---> {err}")
        raise CustomException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=Messages.ERROR_FETCHING_DB_CLIENT,
            details=err_constants.ERROR_FETCHING_DB_CLIENT
        )


def create_or_reactivate_db_client(
    db: Session, client_data, client_uuid: str, existing_client: ClientModel = None
) -> Tuple[ClientModel, str]:
    """
    Create a new client in DB or reactivate an existing one.
    - If client exists (active or inactive), it is reactivated and given the new UUID.
    - If client doesn't exist, a new one is created.
    Returns: (db_client, action)
    """
    try:
        if not existing_client:
            existing_client = (
                db.query(ClientModel)
                .filter(ClientModel.client_name == client_data.clientId)
                .first()
            )

        if existing_client:
            existing_client.is_active = True
            existing_client.client_uuid = client_uuid
            existing_client.last_updated_at = datetime.now(timezone.utc)
            existing_client.last_updated_by = "system"
            db.commit()
            db.refresh(existing_client)
            logger.info(
                "Reactivated existing client '%s' with new UUID '%s'",
                existing_client.client_name,
                client_uuid,
            )
            return existing_client, "REACTIVATE"

        db_client = ClientModel(
            client_name=getattr(client_data, "clientId", client_data.clientId),
            company_name=getattr(client_data, "company_name", "default_company"),
            email=getattr(client_data, "email", "default@example.com"),
            client_bucket_path=getattr(client_data, "client_bucket_path", None),
            client_bucket_name=getattr(client_data, "client_bucket_name", None),
            client_uuid=client_uuid,
            client_mapper={},
            created_at=datetime.now(timezone.utc),
            created_by="system",
            is_active=True,
        )
        db.add(db_client)
        db.commit()
        db.refresh(db_client)

        db_client.display_client_id = f"cli-{db_client.id}"
        db.commit()
        db.refresh(db_client)

        logger.info(
            "Created new client '%s' with UUID '%s'",
            db_client.client_name,
            client_uuid,
        )
        return db_client, "CREATE"

    except CustomException as err:
        logger.error(f"client_service:create_or_reactivate_db_client ---> {err}", exc_info=True)
        raise err

    except Exception as err:
        logger.error(f"Exception while creating/reactivating DB client ---> {err}")
        raise CustomException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=Messages.ERROR_CREATING_DB_CLIENT,
            details=err_constants.ERROR_CREATING_DB_CLIENT
        )


# ------------------ UUID Fetch ------------------
def fetch_client_uuid(service, client_id: str, headers: dict, retries: int = 5, delay: float = 0.5) -> str:
    """Fetch client UUID from Keycloak, with retries."""
    try:
        for _ in range(retries):
            clients_list = service.safe_request(
                "GET", f"{service.admin_url}/clients?clientId={client_id}", headers=headers
            ).json()
            if clients_list:
                return clients_list[0]["id"]
            time.sleep(delay)
        raise CustomException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=Messages.CLIENT_UUID_FETCH_FAILED,
            details=err_constants.CLIENT_UUID_FETCH_FAILED
        )

    except CustomException as err:
        logger.error(f"client_service:fetch_client_uuid ---> {err}", exc_info=True)
        raise err

    except Exception as err:
        logger.error(f"Exception while fetching client UUID ---> {err}")
        raise CustomException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=Messages.ERROR_FETCHING_CLIENT_UUID,
            details=err_constants.ERROR_FETCHING_CLIENT_UUID
        )


# ------------------ Resource Fetch ------------------
def get_client_resources(service, source_client_id: str) -> dict:
    """Fetch resources, scopes, policies, and permissions from a source client."""
    try:
        token = get_current_admin_token()
        headers = Headers.get_json_headers(token)

        clients_list = service.safe_request(
            "GET",
            f"{service.admin_url}/clients?clientId={source_client_id}",
            headers=headers,
        ).json()
        if not clients_list:
            raise CustomException(
                status_code=status.HTTP_404_NOT_FOUND,
                message=Messages.SOURCE_CLIENT_NOT_FOUND,
                details=err_constants.SOURCE_CLIENT_NOT_FOUND
            )

        client_uuid = clients_list[0]["id"]

        resources = service.safe_request(
            "GET",
            f"{service.admin_url}/clients/{client_uuid}/authz/resource-server/resource",
            headers=headers,
        ).json()
        scopes = service.safe_request(
            "GET",
            f"{service.admin_url}/clients/{client_uuid}/authz/resource-server/scope",
            headers=headers,
        ).json()
        policies = service.safe_request(
            "GET",
            f"{service.admin_url}/clients/{client_uuid}/authz/resource-server/policy",
            headers=headers,
        ).json()
        permissions = service.safe_request(
            "GET",
            f"{service.admin_url}/clients/{client_uuid}/authz/resource-server/permission",
            headers=headers,
        ).json()

        logger.warning(
            f"[IMPORT DEBUG] resources={len(resources)}, "
            f"scopes={len(scopes)}, policies={len(policies)}, permissions={len(permissions)}"
        )



        return {"resources": resources, "scopes": scopes, "policies": policies, "permissions": permissions}

    except CustomException as err:
        logger.error(f"client_service:get_client_resources ---> {err}", exc_info=True)
        raise err

    except Exception as err:
        logger.error(f"Exception while fetching client resources ---> {err}")
        raise CustomException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=Messages.RESOURCE_FETCH_FAILED,
            details=err_constants.RESOURCE_FETCH_FAILED
        )


# ------------------ Resource Import ------------------
def post_resource_item(service, target_client_uuid, endpoint, item, headers):
    """Post a single resource item to Keycloak."""
    try:
        item_copy = {k: v for k, v in item.items() if k not in ["id", "_id", "owner", "ownerManagedAccess"]}
        if "scopes" in item_copy and isinstance(item_copy["scopes"], list):
            item_copy["scopes"] = [{"name": s["name"]} for s in item_copy["scopes"] if "name" in s]

        name = item_copy.get("name")
        if not name:
            raise CustomException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message=Messages.RESOURCE_NAME_MISSING,
                details=err_constants.RESOURCE_NAME_MISSING
            )

        base_url = f"{service.admin_url}/clients/{target_client_uuid}/authz/resource-server/{endpoint}"
        check_url = f"{base_url}?name={name}"

        check_resp = service.safe_request("GET", check_url, headers=headers)
        if check_resp.status_code == 200 and isinstance(check_resp.json(), list) and check_resp.json():
            return
        service.safe_request("POST", base_url, headers=headers, json=item_copy)
        time.sleep(0.2)

    except CustomException as err:
        logger.error(f"client_service:post_resource_item ---> {err}", exc_info=True)
        raise err

    except Exception as err:
        logger.error(f"Exception while posting resource item ---> {err}")
        raise CustomException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=Messages.RESOURCE_POST_FAILED,
            details=err_constants.RESOURCE_POST_FAILED
        )


def import_resources_to_client(service, target_client_uuid: str, data: dict, max_workers=3):
    """Import resources to a target client using multithreading."""
    try:
        if not data:
            logger.info("import_resources_to_client: no data provided, skipping")
            return

        token = get_current_admin_token()
        headers = Headers.get_json_headers(token)

        endpoints = {"resources": "resource", "scopes": "scope", "policies": "policy", "permissions": "permission"}

        for key, endpoint in endpoints.items():
            items = data.get(key, [])
            if not items:
                continue

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {
                    executor.submit(post_resource_item, service, target_client_uuid, endpoint, item, headers): item
                    for item in items
                }

                for future in as_completed(futures):
                    item = futures[future]
                    try:
                        future.result()
                    except CustomException as err:
                        logger.error(f"client_service:import_resources_to_client worker ---> {err}", exc_info=True)
                        raise err
                    except Exception as err:
                        logger.error(f"Exception while importing resource to client ---> {err}")
                        raise CustomException(
                            status_code=500,
                            message=Messages.THREAD_WORKER_EXCEPTION,
                            details=err_constants.THREAD_WORKER_EXCEPTION
                        )

        logger.info("import_resources_to_client: completed import for client_uuid=%s", target_client_uuid)

    except CustomException as err:
        logger.error(f"client_service:import_resources_to_client ---> {err}", exc_info=True)
        raise err

    except Exception as err:
        logger.error(f"Exception while importing resources to client ---> {err}")
        raise CustomException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=Messages.ERROR_IMPORTING_RESOURCES,
            details=err_constants.ERROR_IMPORTING_RESOURCES
        )


# ------------------ Client Processing Helpers ------------------
def fetch_existing_clients(service, headers: dict):
    """Fetch all existing clients from Keycloak."""
    try:
        url = f"{service.admin_url}/clients"
        response = service.safe_request("GET", url, headers=headers)
        if response.status_code != 200:
            raise CustomException(
                status_code=response.status_code,
                message=Messages.KEYCLOAK_CLIENTS_REQUEST_FAILED,
                details=err_constants.KEYCLOAK_CLIENTS_FETCH_FAILED
            )
        return response.json()

    except CustomException as err:
        logger.error(f"client_service:fetch_existing_clients ---> {err}", exc_info=True)
        raise err

    except Exception as err:
        logger.error(f"Exception while fetching existing clients ---> {err}")
        raise CustomException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=Messages.CLIENTS_EXISTING_FETCH_FAILED,
            details=err_constants.ERROR_FETCHING_EXISTING_CLIENTS
        )


def process_single_client(service, client_data, db: Session, results: list):
    """Process a single client: payload, DB, Keycloak, and resource import."""
    client_id = client_data.clientId if hasattr(client_data, "clientId") else client_data.get("clientId")

    try:
        payload, import_from_client = prepare_client_payload(client_data)

        db_client = fetch_db_client(db, client_id)
        if db_client and db_client.is_active:
            results.append({
                "client_id": client_id,
                "status": "failed",
                "message": err_constants.CLIENT_ALREADY_ACTIVE,
            })
            return

        token = get_current_admin_token()
        if not token:
            raise CustomException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                message=Messages.ADMIN_TOKEN_UNAVAILABLE,
                details=err_constants.ERROR_ADMIN_TOKEN_FETCH
            )
        headers_base = Headers.get_json_headers(token)

        resp = service.safe_request("POST", f"{service.admin_url}/clients", headers=headers_base, json=payload)
        if resp.status_code == 401:
            token = get_current_admin_token()
            headers_base = Headers.get_json_headers(token)
            resp = service.safe_request("POST", f"{service.admin_url}/clients", headers=headers_base, json=payload)

        if resp.status_code not in (200, 201):
            raise CustomException(
                status_code=resp.status_code,
                message=Messages.CLIENT_CREATION_FAILED,
                details=err_constants.CLIENT_CREATION_FAILED
            )

        client_uuid = fetch_client_uuid(service, client_id, headers_base)
        db_client, action = create_or_reactivate_db_client(db, client_data, client_uuid, db_client)
        log_client_action(db=db, client_id=db_client.id, client_uuid=client_uuid, action=action)

        if import_from_client:
            imported_data = get_client_resources(service, import_from_client)
            import_resources_to_client(service, db_client.client_uuid, imported_data, max_workers=3)

        results.append({
            "client_id": client_id,
            "status": "success",
            "message": "Client created/reactivated successfully"
        })

    except CustomException as err:
        logger.error(f"client_service:process_single_client ---> {err}", exc_info=True)
        raise err

    except Exception as err:
        logger.error(f"Exception while processing single client ---> {err}",exc_info=True)
        raise CustomException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=Messages.ERROR_PROCESSING_SINGLE_CLIENT,
            details=err_constants.ERROR_PROCESSING_SINGLE_CLIENT
        )
    

def log_client_action(
        db: Session,
        client_id: Optional[int],
        action: str,
        client_uuid: Optional[str] = None,
        performed_by: str = "system",
        error_logs: Optional[str] = None,
        is_active: bool = True,
    ):
        """Save a log entry for any client action (create, delete, etc.) in the database."""
        try:
            log_entry = ClientLogs(
                client_id=client_id,
                client_uuid=client_uuid,
                action=action,
                error_logs=error_logs,
                performed_at=datetime.now(timezone.utc),
                performed_by=performed_by,
                is_active=is_active,
            )
            db.add(log_entry)
            db.commit()
            db.refresh(log_entry)
            logger.debug(f"log_client_action: logged {action} for client_id={client_id} uuid={client_uuid}")
            return True

        except CustomException as err:
            logger.error(f"client_service:log_client_action ---> {err}", exc_info=True)
            raise err
        except Exception as err:
            logger.error(f"Exception while logging client action ---> {err}")
            raise CustomException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=Messages.CLIENT_LOG_FAILED,
                details=err_constants.DB_SAVE_CLIENT_FAILED
            )


PROTECTED_SCOPES = ["acr", "profile", "email", "roles", "web-origins"]
def delete_client_scopes(service, client_uuid: str, protected_scopes=PROTECTED_SCOPES):
    """Delete all client-specific scopes for a client except protected scopes."""
    try:
        token = get_current_admin_token()
        headers = Headers.get_json_headers(token)

        # Fetch default and optional client scopes
        default_scopes = service.safe_request(
            "GET", f"{service.admin_url}/clients/{client_uuid}/default-client-scopes", headers=headers
        ).json()

        optional_scopes = service.safe_request(
            "GET", f"{service.admin_url}/clients/{client_uuid}/optional-client-scopes", headers=headers
        ).json()

        client_scopes = default_scopes + optional_scopes

        for scope in client_scopes:
            scope_name = scope.get("name")
            if not scope_name or scope_name in protected_scopes:
                continue

            scope_id = scope.get("id")
            if not scope_id:
                continue

            # Detach from client
            endpoint_type = "default-client-scopes" if scope in default_scopes else "optional-client-scopes"
            service.safe_request(
                "DELETE",
                f"{service.admin_url}/clients/{client_uuid}/{endpoint_type}/{scope_id}",
                headers=headers
            )
            logger.info("Deleted client scope '%s' for client_uuid='%s'", scope_name, client_uuid)

            # Delete from global scopes
            service.safe_request(
                "DELETE",
                f"{service.admin_url}/client-scopes/{scope_id}",
                headers=headers
            )
            logger.info(f"Deleted global scope '{scope_name}' from realm")

    except Exception as err:
        logger.error(f"Exception while deleting client scopes ---> {err}")
        raise CustomException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=Messages.CLIENT_SCOPES_DELETION_FAILED,
            details=err_constants.CLIENT_SCOPE_DELETE_FAILED
        )
    
