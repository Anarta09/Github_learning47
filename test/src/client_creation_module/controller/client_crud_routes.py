from fastapi import APIRouter, Depends, Body, status
from typing import List, Dict
from sqlalchemy.orm import Session

from client_creation_module.schema.request import CreateClientModel
from dependencies.client_dep import fetch_clients
from client_creation_module.service.client_crud_service import ClientService
from role_module.service.client_roles_service import ClientRoleService
from database.db import get_db

router = APIRouter()
client_service = ClientService()
client_role_service = ClientRoleService()


# -------------------- GET CLIENTS --------------------
@router.get(
    "/get-clients",
    tags=["Client Operations"],
    summary="Fetch active clients (with optional search)",
)
def get_clients(
    search: str | None = None,
    clients: List[Dict] = Depends(fetch_clients),
):
    return client_service.get_clients(clients=clients, search=search)


# -------------------- CREATE CLIENTS --------------------
@router.post(
    "/create-clients-with-config",
    tags=["Client Operations"],
    summary="Create one or multiple Keycloak clients",
    status_code=status.HTTP_201_CREATED,
)
def create_clients_with_config(
    client_data: List[CreateClientModel] = Body(...),
    db: Session = Depends(get_db),
):
    return client_service.create_clients(client_data_list=client_data, db=db)


# -------------------- DELETE CLIENTS --------------------
@router.delete(
    "/delete-clients",
    tags=["Client Operations"],
    summary="Delete one or multiple clients",
    status_code=status.HTTP_200_OK,
)
def delete_clients_route(
    client_ids: List[str] = Body(...),
    clients: List[Dict] = Depends(fetch_clients),
    db: Session = Depends(get_db),
):  

    return client_service.delete_clients(client_ids=client_ids, clients=clients, db=db)
