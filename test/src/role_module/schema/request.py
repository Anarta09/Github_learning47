from pydantic import BaseModel, RootModel
from typing import Optional, List, Dict


# ---- Request Models ----
class RoleModel(BaseModel):
    name: str
    description: Optional[str] = None
    source: str = "AnnovaHealthCare"  # "realm" or "client", default to "client" for backwards compatibility
    clientId: Optional[str] = None  # required only for client roles


class CreateRoleModel(BaseModel):
    name: str
    description: Optional[str] = None


class CreateRolesModel(BaseModel):
    roles: List[CreateRoleModel]


class CreateRoleForMultipleClientsModel(BaseModel):
    role: CreateRoleModel
    clients: List[str]  # human-readable client IDs


class CreateRolesForMultipleClientsModel(BaseModel):
    roles: List[CreateRoleModel]
    clients: List[str]


class DeleteRolesForMultipleClientsModel(BaseModel):
    roles: List[str]  # just need name, description optional
    clients: List[str]


