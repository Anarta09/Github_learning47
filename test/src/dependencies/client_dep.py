from fastapi import HTTPException
from typing import List, Dict
import requests

from config import settings

from dependencies.auth_dep import get_admin_token

REALM = settings.REALM
ADMIN_URL = f"{settings.KEYCLOAK_BASE_URL}/admin/realms/{REALM}"


def fetch_clients() -> List[Dict]:
    """
    Dependency that fetches and parses clients from Keycloak.
    """
    token = get_admin_token()
    url = f"{ADMIN_URL}/clients"
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.json())

    client_details = resp.json()
    # Example: only return id and clientId
    parsed_clients = [
        {"id": client["id"], "clientId": client["clientId"]}
        for client in client_details
    ]
    return parsed_clients
