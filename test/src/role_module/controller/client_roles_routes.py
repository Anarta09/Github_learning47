from fastapi import APIRouter, Depends, Body, status
from typing import List, Dict, Union
from sqlalchemy.orm import Session

# ---------------- Dependencies ----------------
from dependencies.client_dep import fetch_clients
from database.db import get_db

# ---------------- Schemas ----------------
from role_module.schema.request import (
    CreateRolesForMultipleClientsModel,
    DeleteRolesForMultipleClientsModel,
)
from role_module.schema.response import (
    RolesResponseModel,
    DeleteRolesResponseModel,
)

# ---------------- Service ----------------
from role_module.service.client_roles_service import ClientRoleService

router = APIRouter()
client_role_service = ClientRoleService()


# ------------------ List All Roles for a Client ------------------
@router.get(
    "/clients/{client_id}/roles",
    tags=["Client Role Operations"],
    summary="List all roles for a specific client",
)
def list_all_roles(
    client_name: str,
    clients: List[Dict] = Depends(fetch_clients),
):
    return client_role_service.list_roles(client_name, clients)


# ------------------ Create Roles ------------------
@router.post(
    "/roles/create",
    tags=["Client Role Operations"],
    response_model=RolesResponseModel,
    status_code=status.HTTP_201_CREATED,
    summary="Create roles across one or multiple clients",
)
def create_roles_universal_route(
    payload: CreateRolesForMultipleClientsModel,
    clients: List[Dict] = Depends(fetch_clients),
    db: Session = Depends(get_db),
):
    return client_role_service.create_roles_universal(
        client_ids=payload.clients,
        roles=payload.roles,
        clients=clients,
        db=db,
    )


# ------------------ Delete Roles ------------------
@router.delete(
    "/roles/clients",
    tags=["Client Role Operations"],
    response_model=DeleteRolesResponseModel,
    summary="Delete roles for one or more clients",
)
def delete_roles_for_clients_route(
    payload: DeleteRolesForMultipleClientsModel,
    clients: List[Dict] = Depends(fetch_clients),
    db: Session = Depends(get_db),
):
    return client_role_service.delete_roles_for_clients(
        roles=payload.roles,
        client_ids=payload.clients,
        clients=clients,
        db=db,
    )
