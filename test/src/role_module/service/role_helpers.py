import requests
from datetime import datetime, timezone
from fastapi import status
from config import settings
from dependencies.auth_dep import get_admin_token
from models.client_model import Client
from models.role_detail_model import RoleDetail
from models.role_log_model import RoleLog
from utils.scripts.headers import Headers
from sqlalchemy.orm import Session
from role_module.service.role_detail_service import RoleDetail
from custom_exeptions import CustomException, err_constants,Messages
from role_module.schema.response import DeleteRolesResponseModel
from role_module.schema.response import RoleDeletedModel
from role_module.service.role_log_service import RoleLogService
from client_creation_module.service import client_helpers
from typing import List,Dict
import logging

# Request models
from role_module.schema.request import CreateRoleModel
# Response models
from role_module.schema.response import (
    RoleFailedModel,
    RoleCreatedModel,
    RoleReactivatedModel,
    ClientRolesResultModel,
)

logger = logging.getLogger(__name__)


def safe_name(obj) -> str:
    """Safely extract a role name from a dict, Pydantic model, or string."""
    if isinstance(obj, dict) and "name" in obj:
        return obj["name"]
    return getattr(obj, "name", str(obj))


def get_matching_client(client_id: str, clients: list) -> dict:
    """Fetch a matching Keycloak client dict from list of clients."""
    try:
        match = next((c for c in clients if c["clientId"] == client_id), None)
        if not match:
            raise CustomException(
                status_code=status.HTTP_404_NOT_FOUND,
                message=Messages.CLIENTS_NO_MATCH,
                details=err_constants.CLIENT_NOT_FOUND
            )
        return match

    except CustomException as err:
        logger.error(f"role_helpers.py:get_matching_client ---> {err}", exc_info=True)
        raise err

    except Exception as err:
        logger.error(f"Exception while fetching matching client ---> {err}")
        raise CustomException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=Messages.CLIENTS_NO_MATCH,
            details=err_constants.CLIENT_NOT_FOUND
        )


def store_or_reactivate_role_in_db(db, role_name, client, role_detail_service, role_log_service, role_uuid=None, created_by="system"):
    """Insert or reactivate a role in the local DB and log the event."""
    try:
        client_record = db.query(Client).filter(Client.client_name == client["clientId"]).first()
        if not client_record:
            raise CustomException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message=Messages.CLIENTS_NO_MATCH,
                details=err_constants.CLIENT_NOT_FOUND
            )

        existing_role = db.query(RoleDetail).filter(
            RoleDetail.role_name == role_name,
            RoleDetail.client_id == client_record.id
        ).first()

        if existing_role:
            if not existing_role.is_active:
                existing_role.is_active = True
                existing_role.updated_at = datetime.now(timezone.utc)
                existing_role.updated_by = created_by
                if role_uuid:
                    existing_role.role_uuid = role_uuid
                db.commit()
            action = "reactivated"
        else:
            existing_role = role_detail_service.create_role_detail(
                db=db,
                role_name=role_name,
                client_id=client_record.id,
                client_uuid=client.get("uuid") or client_record.client_uuid,
                client_name=client_record.client_name,
                created_by=created_by,
            )

            existing_role.updated_at = None
            existing_role.updated_by = None

            if role_uuid:
                existing_role.role_uuid = role_uuid
                db.commit()
            action = "created"

        # Log action
        try:
            role_log_service.log_action(
                db=db,
                role_id=existing_role.id,
                client_id=client_record.id,
                action=action.upper(),
                performed_by=created_by,
            )
        except Exception as log_err:
            logger.warning(f"Could not log role action: {log_err}")

        return existing_role, action

    except CustomException as err:
        logger.error(f"role_helpers.py:store_or_reactivate_role_in_db ---> {err}", exc_info=True)
        raise err

    except Exception as err:
        logger.error(f"Exception while storing/reactivating role in DB ---> {err}")
        raise CustomException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=Messages.DB_INSERT_FAILED,
            details=err_constants.DB_INSERT_FAILED
        )


def create_policy_for_role(client_id: str, role_name: str) -> bool:
    """Create an authorization policy in Keycloak for a specific role."""
    admin_url = settings.ADMIN_URL.rstrip("/")
    try:
        token = get_admin_token()
        headers = Headers.get_json_headers(token)

        # Find Role ID
        role_search_url = f"{admin_url}/clients/{client_id}/roles?search={role_name}"
        role_resp = requests.get(role_search_url, headers=headers)
        role_resp.raise_for_status()
        role_list = role_resp.json()
        role_id = next((r["id"] for r in role_list if r["name"] == role_name), None)

        if not role_id:
            logger.warning(f"Role '{role_name}' not found for client '{client_id}', skipping policy")
            return False

        # Ensure authorization enabled
        client_url = f"{admin_url}/clients/{client_id}"
        c_resp = requests.get(client_url, headers=headers)
        c_resp.raise_for_status()
        client_data = c_resp.json()
        if not client_data.get("authorizationServicesEnabled"):
            client_data["authorizationServicesEnabled"] = True
            requests.put(client_url, headers=headers, json=client_data).raise_for_status()
            logger.info(f"Authorization enabled for '{client_id}'")

        # Create Policy
        policy_payload = {
            "name": f"{role_name}_policy",
            "type": "role",
            "logic": "POSITIVE",
            "decisionStrategy": "UNANIMOUS",
            "roles": [{"id": role_id}],
        }
        policy_url = f"{admin_url}/clients/{client_id}/authz/resource-server/policy/role"
        p_resp = requests.post(policy_url, headers=headers, json=policy_payload)
        p_resp.raise_for_status()
        logger.info(f"Policy '{role_name}_policy' created for '{client_id}'")
        return True

    except CustomException as err:
        logger.error(f"role_helpers.py:create_policy_for_role ---> {err}", exc_info=True)
        raise err

    except Exception as err:
        logger.error(f"Exception while creating policy for role '{role_name}' ---> {err}")
        raise CustomException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=Messages.KEYCLOAK_POLICY_CREATE_FAILED,
            details=err_constants.KEYCLOAK_POLICY_CREATE_FAILED
        )


def delete_policy_for_role(client_id: str, role_name: str) -> bool:
    """Delete the authorization policy in Keycloak corresponding to a role."""
    admin_url = settings.ADMIN_URL.rstrip("/")
    policy_name = f"{role_name}_policy"

    try:
        token = get_admin_token()
        headers = Headers.get_json_headers(token)

        list_url = f"{admin_url}/clients/{client_id}/authz/resource-server/policy"
        resp = requests.get(list_url, headers=headers)
        resp.raise_for_status()
        policies = resp.json()

        policy = next((p for p in policies if p["name"] == policy_name), None)
        if not policy:
            logger.warning(f"Policy '{policy_name}' not found for client '{client_id}'")
            return False

        delete_url = f"{list_url}/{policy['id']}"
        del_resp = requests.delete(delete_url, headers=headers)
        del_resp.raise_for_status()
        logger.info(f"Policy '{policy_name}' deleted for '{client_id}'")
        return True

    except CustomException as err:
        logger.error(f"role_helpers.py:delete_policy_for_role ---> {err}", exc_info=True)
        raise err

    except Exception as err:
        logger.error(f"Exception while deleting policy '{policy_name}' for client '{client_id}' ---> {err}")
        raise CustomException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=Messages.KEYCLOAK_POLICY_DELETE_FAILED,
            details=err_constants.KEYCLOAK_POLICY_DELETE_FAILED
        )


def normalize_role_inputs(client_ids, roles):
    """Normalize single vs multiple client/role inputs into lists."""
    try:
        if isinstance(client_ids, str):
            client_ids = [client_ids]
        if isinstance(roles, (str, CreateRoleModel)):
            roles = [roles]
        return client_ids, roles

    except Exception as err:
        logger.error(f"Exception while normalizing role inputs ---> {err}")
        raise CustomException(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=Messages.INVALID_INPUT,
            details=err_constants.INVALID_INPUT
        )


def fetch_role_uuid(base_url, headers, role_name):
    """Fetch role UUID from Keycloak safely."""
    try:
        resp = requests.get(f"{base_url}/{role_name}", headers=headers)
        return resp.json().get("id") if resp.ok else None

    except Exception as err:
        logger.error(f"Exception while fetching role UUID ---> {err}")
        return None


def create_policy_safe(client_id, role_name):
    """Attempt to create a policy for a role, but don't fail the main flow."""
    try:
        create_policy_for_role(client_id, role_name)
    except Exception as err:
        logger.warning(f"Policy creation failed for role '{role_name}': {err}")


def process_role_creation(role, client, url, headers, db, role_detail_service, role_log_service):
    """Handles Keycloak creation/reactivation + DB store for a single role."""
    role_name = safe_name(role)
    try:
        response = requests.post(url, headers=headers, json={"name": role_name})

        if response.status_code == 409:
            role_uuid = fetch_role_uuid(url, headers, role_name)
            db_entry, action = store_or_reactivate_role_in_db(
                db, role_name, client, role_detail_service, role_log_service, role_uuid
            )
        else:
            response.raise_for_status()
            role_uuid = fetch_role_uuid(url, headers, role_name)
            db_entry, action = store_or_reactivate_role_in_db(
                db, role_name, client, role_detail_service, role_log_service, role_uuid
            )
            create_policy_safe(client["id"], role_name)

        return action, role_name, db_entry, None

    except CustomException as err:
        logger.error(f"role_helpers.py:process_role_creation ---> {err}", exc_info=True)
        raise err

    except Exception as err:
        logger.error(f"Exception while processing role creation ---> {err}")
        raise CustomException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=Messages.ROLE_CREATION_FAILED,
            details=err_constants.ROLES_CREATION_FAILED
        )


def process_roles_for_client(db, roles, client_match, headers, role_detail_service, role_log_service, admin_url):
    """Process all roles for a single client and return ClientRolesResultModel."""
    try:
        url = f"{admin_url}/clients/{client_match['id']}/roles"
        created, reactivated, failed = [], [], []

        for role in roles:
            role_name = safe_name(role)
            role_description = getattr(role, "description", None)

            try:
                action, name, entry, reason = process_role_creation(
                    role=role,
                    client=client_match,
                    url=url,
                    headers=headers,
                    db=db,
                    role_detail_service=role_detail_service,
                    role_log_service=role_log_service,
                )

                final_uuid = getattr(entry, "role_uuid", None) if entry else None
                model_kwargs = {
                    "name": name,
                    "description": role_description,
                    **({"role_uuid": final_uuid} if final_uuid else {}),
                }

                if action == "created":
                    created.append(RoleCreatedModel(**model_kwargs))
                elif action == "reactivated":
                    reactivated.append(RoleReactivatedModel(**model_kwargs))
                else:
                    failed.append(RoleFailedModel(name=name, reason=reason))

            except CustomException as inner_err:
                logger.error(f"role_helpers.py:process_roles_for_client ---> {inner_err}", exc_info=True)
                failed.append(RoleFailedModel(name=role_name, reason=str(inner_err)))

            except Exception as inner_err:
                logger.error(f"Exception while processing roles for client ---> {inner_err}")
                failed.append(RoleFailedModel(name=role_name, reason=str(inner_err)))

        return ClientRolesResultModel(created=created, reactivated=reactivated, failed=failed)

    except CustomException as err:
        logger.error(f"role_helpers.py:process_roles_for_client ---> {err}", exc_info=True)
        raise err

    except Exception as err:
        logger.error(f"Exception while processing roles for client ---> {err}")
        raise CustomException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=Messages.ROLE_PROCESSING_FAILED,
            details=err_constants.ROLE_PROCESSING_FAILED
        )

def delete_role_full(
    db,
    client_display_id: str,
    clients: List[Dict],
    role_name: str,
    role_detail_service,
    role_log_service
):
    """
    Fully delete a role:
    - Soft delete in DB
    - Update RoleLog
    - Delete role in Keycloak
    - Delete authorization policy in Keycloak
    - Return DeleteRolesResponseModel
    """

    try:
        # --------------------------
        # 0) MATCH CLIENT IN KEYCLOAK
        # --------------------------
        match = get_matching_client(client_display_id, clients)
        if not match:
            raise CustomException(
                status_code=status.HTTP_404_NOT_FOUND,
                message=Messages.CLIENTS_NO_MATCH,
                details=err_constants.CLIENT_NOT_FOUND
            )
        client_uuid = match["id"]  # Keycloak client UUID

        # --------------------------
        # 1) FETCH CLIENT RECORD FROM DB
        # --------------------------
        client_record = db.query(Client).filter(Client.client_name == client_display_id).first()
        if not client_record:
            raise CustomException(
                status_code=status.HTTP_404_NOT_FOUND,
                message=Messages.CLIENTS_NO_MATCH,
                details=err_constants.CLIENT_NOT_FOUND_DB
            )

        # --------------------------
        # 2) FETCH ROLE FROM DB
        # --------------------------
        role_record = db.query(RoleDetail).filter(
            RoleDetail.role_name == role_name,
            RoleDetail.client_uuid == client_record.client_uuid
        ).first()

        if not role_record:
            return DeleteRolesResponseModel(
                message=Messages.ROLE_NOT_FOUND,
                results=err_constants.ROLE_NOT_FOUND
            )

        # --------------------------
        # 3) SOFT DELETE IN DB
        # --------------------------
        role_record.is_active = False
        role_record.updated_at = datetime.now(timezone.utc)
        role_record.updated_by = "system"
        db.commit()

        # --------------------------
        # 4) DELETE ROLE IN KEYCLOAK
        # --------------------------
        token = get_admin_token()
        headers = Headers.get_json_headers(token)
        from urllib.parse import quote
        delete_url = f"{settings.ADMIN_URL.rstrip('/')}/clients/{client_uuid}/roles/{quote(role_name)}"
        kc_resp = requests.delete(delete_url, headers=headers)

        if kc_resp.status_code not in (200, 204, 404):
            raise CustomException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=Messages.KEYCLOAK_ROLE_DELETE_FAILED,
                details=err_constants.KEYCLOAK_ROLE_DELETE_FAILED
            )

        # --------------------------
        # 5) DELETE AUTH POLICY
        # --------------------------
        try:
            delete_policy_for_role(client_uuid, role_name)
        except requests.HTTPError as pol_err:
            if pol_err.response.status_code == 404:
                logger.info(f"Policy '{role_name}_policy' not found for client '{client_uuid}', skipping deletion")
            else:
                logger.warning(f"Policy delete failed for {role_name} ---> {pol_err}")

        # --------------------------
        # 6) LOG ACTION
        # --------------------------
        try:
            role_log_service.deactivate_logs(
                db=db,
                role_id=role_record.id,
                client_id=client_record.id,
                updated_by="system"
            )        



            role_log_service.log_action(
                db=db,
                role_id=role_record.id,
                client_id=client_record.id,  # Use DB integer ID here
                action="DELETED",
                performed_by="system",
                is_active=False
            )
        except Exception as log_err:
            logger.warning(f"Could not log role delete: {log_err}")

        # --------------------------
        # 7) RETURN RESULT MODEL
        # --------------------------
        return {
            "client_id": str(client_record.id),  # Convert to string
            "deleted_roles": [{"role_name": role_name}]  # List of dicts
            }


    except CustomException as err:
        logger.error(f"role_helpers.py:delete_role_full ---> {err}", exc_info=True)
        raise err

    except Exception as err:
        logger.error(f"Exception during full role deletion ---> {err}")
        raise CustomException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=Messages.ROLE_DELETE_FAILED,
            details=err_constants.KEYCLOAK_ROLE_DELETE_FAILED
        )


def deactivate_roles_for_deleted_client(
    client_id: str, 
    db: Session,
    role_log_service: RoleLogService,
    updated_by: str = "system",
):
    """Deactivate all roles and their logs in DB when a client is deleted."""
    try:
        client_record = db.query(Client).filter(Client.client_name == client_id).first()
        if not client_record:
            raise CustomException(
                status_code=status.HTTP_404_NOT_FOUND,
                message=Messages.CLIENTS_NO_MATCH,
                details=err_constants.CLIENT_NOT_FOUND
            )

        # Fetch all active roles for this client
        roles = db.query(RoleDetail).filter(
            RoleDetail.client_id == client_record.id,
            RoleDetail.is_active == True
        ).all()

        if not roles:
            return {"message": f"No active roles found for client '{client_id}'."}

        role_ids = [role.id for role in roles]

        #  Deactivate roles
        for role in roles:
            role.is_active = False
            role.updated_at = datetime.now(timezone.utc)
            role.updated_by = updated_by

        # Deactivate existing logs for these roles
        db.query(RoleLog).filter(
            RoleLog.role_id.in_(role_ids),
            RoleLog.is_active == True
        ).update(
            {"is_active": False},
            synchronize_session=False
        )


        # Create new logs for CLIENT_DEACTIVATED (inactive)
        for role in roles:
            role_log_service.log_action(
                db=db,
                role_id=role.id,
                client_id=client_record.id,
                action="CLIENT_DEACTIVATED",
                performed_by=updated_by,
                is_active=False  
            )

        db.commit()

        return {"message": f"All roles and logs deactivated for deleted client '{client_id}'."}

    except CustomException as err:
        logger.error(f"role_helpers.py:deactivate_roles_for_deleted_client ---> {err}", exc_info=True)
        raise err

    except Exception as err:
        logger.error(f"Exception while deactivating roles for deleted client ---> {err}")
        raise CustomException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=Messages.DEACTIVATE_ROLES_FAILED,
            details=err_constants.DB_REACTIVATE_CLIENT_FAILED
        )

