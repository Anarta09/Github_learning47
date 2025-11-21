import requests
from fastapi import HTTPException
from core.config import settings
from dependencies.auth_dep import get_admin_token

def create_policy_for_role(client_id: str, role_name: str, admin_url: str = settings.ADMIN_URL):
    """
    Create a Keycloak policy for a given role.
    """
    token = get_admin_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # Get role ID
    try:
        role_resp = requests.get(f"{admin_url}/clients/{client_id}/roles/{role_name}", headers=headers)
        role_resp.raise_for_status()
        role_id = role_resp.json().get("id")
        if not role_id:
            raise HTTPException(status_code=404, detail=f"Role '{role_name}' not found in Keycloak")
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch role '{role_name}': {str(e)}")

    # Create policy
    payload = {
        "name": role_name,
        "type": "role",
        "logic": "POSITIVE",
        "decisionStrategy": "UNANIMOUS",
        "roles": [{"id": role_id, "required": True}]
    }
    try:
        policy_url = f"{admin_url}/clients/{client_id}/authz/resource-server/policy"
        resp = requests.post(policy_url, headers=headers, json=payload)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"Warning: Could not create policy for role '{role_name}': {str(e)}")
