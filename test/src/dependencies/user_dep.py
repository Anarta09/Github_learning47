from fastapi import Depends
from services.user_crud_service import UserService


def fetch_users(service: UserService = Depends()):
    """
    Dependency to fetch all users from Keycloak.
    """
    return service.list_users()
