import requests
from fastapi import HTTPException
from config import settings
from dependencies.auth_dep import get_admin_token


def apply_authz_config_to_client(
    client_uuid: str, authz_config: dict, realm: str = settings.REALM
):
    """
    Apply authorization configuration (resources, scopes, policies) to a Keycloak client
    in one go using the import API.

    :param client_uuid: UUID of the Keycloak client
    :param authz_config: Full authorization configuration dict (resources, scopes, policies, etc.)
    :param realm: Keycloak realm
    """
    token = get_admin_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    import_url = (
        f"{settings.ADMIN_URL}/clients/{client_uuid}/authz/resource-server/import"
    )

    resp = requests.post(import_url, headers=headers, json=authz_config)

    if resp.status_code not in (200, 201, 204):
        raise HTTPException(
            status_code=resp.status_code,
            detail=f"Failed to import authorization config: {resp.text}",
        )

    return {"message": "Authorization configuration imported successfully"}
