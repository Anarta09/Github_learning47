from fastapi import APIRouter
from client_creation_module.controller import client_crud_routes
from role_module.controller import client_roles_routes

api_router = APIRouter()
api_router.include_router(client_crud_routes.router)
api_router.include_router(client_roles_routes.router)
