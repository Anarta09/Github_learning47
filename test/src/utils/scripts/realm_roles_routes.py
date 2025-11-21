import requests
from fastapi import APIRouter, HTTPException

from core.config import settings

from dependencies.auth_dep import get_admin_token
from schemas.role_schema import RoleModel


router = APIRouter()

ADMIN_URL = settings.ADMIN_URL


# ---------------- Realm Role Endpoints ----------------


@router.get(path="/get-realm-roles", tags=["Realm Role Operations"])
def list_roles():
    """
    List all realm roles in Keycloak.
    """
    token = get_admin_token()
    url = f"{ADMIN_URL}/roles"
    headers = {"Authorization": f"Bearer {token}"}

    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.json())

    roles = resp.json()
    # Return only key info
    return [
        {"name": role["name"], "description": role.get("description")} for role in roles
    ]


@router.post(path="/create-realm-role", tags=["Realm Role Operations"])
def create_role(role: RoleModel):
    """
    Create a new realm role in Keycloak.
    """
    token = get_admin_token()
    url = f"{ADMIN_URL}/roles"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    resp = requests.post(url, headers=headers, json=role.dict())
    if resp.status_code not in (201, 200):
        raise HTTPException(status_code=resp.status_code, detail=resp.json())

    return {"message": f"Role '{role.name}' created successfully"}


@router.delete(path="/delete-realm-role/{role_name}", tags=["Realm Role Operations"])
def delete_role(role_name: str):
    """
    Delete a realm role by name.
    """
    token = get_admin_token()
    url = f"{ADMIN_URL}/roles/{role_name}"
    headers = {"Authorization": f"Bearer {token}"}

    resp = requests.delete(url, headers=headers)
    if resp.status_code not in (204, 200):
        raise HTTPException(status_code=resp.status_code, detail=resp.json())

    return {"message": f"Role '{role_name}' deleted successfully"}
