import requests
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

import jwt
from jwt.jwks_client import PyJWKClient
from jwt.exceptions import PyJWTError

from config import settings

# --- Keycloak Configuration ---
KEYCLOAK_ISSUER = settings.KEYCLOAK_ISSUER
JWKS_URL = settings.JWKS_URL
CLIENT_ID = settings.CLIENT_ID
TOKEN_URL = settings.TOKEN_URL
CLIENT_SECRET = settings.CLIENT_SECRET


# PyJWT-specific JWKS client
jwks_client = PyJWKClient(JWKS_URL)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# --- Admin token flow ---
# def get_admin_token():
#     data = {
#         "grant_type": "client_credentials",
#         "client_id": CLIENT_ID,
#         "client_secret": CLIENT_SECRET,
#     }
#     resp = requests.post(TOKEN_URL, data=data)
#     if resp.status_code != 200:
#         raise HTTPException(status_code=400, detail="Admin token request failed")
#     return resp.json()["access_token"]


import logging
logger = logging.getLogger(__name__)

def get_admin_token():
    data = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }
    resp = requests.post(TOKEN_URL, data=data)
    if resp.status_code != 200:
        raise HTTPException(status_code=400, detail="Admin token request failed")

    token = resp.json()["access_token"]
    # print(f"Admin Token: {token}")
    return token


# --- OAuth2 Flow Endpoints ---
def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience="account",
            issuer=KEYCLOAK_ISSUER,
        )
        return payload
    except PyJWTError as e:
        # Catch any PyJWT-specific errors (invalid token, expired, etc.)
        raise HTTPException(status_code=401, detail=f"Token is invalid or expired: {e}")
    except Exception as e:
        # Catch other potential errors
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred: {e}"
        )


def require_role(role: str):
    def role_checker(payload: dict = Depends(get_current_user)):
        # Check realm roles
        realm_roles = payload.get("realm_access", {}).get("roles", [])
        # Check client roles
        client_roles = (
            payload.get("resource_access", {}).get(CLIENT_ID, {}).get("roles", [])
        )
        if role not in realm_roles and role not in client_roles:
            raise HTTPException(status_code=403, detail="Not enough permissions")
        return payload

    return role_checker
