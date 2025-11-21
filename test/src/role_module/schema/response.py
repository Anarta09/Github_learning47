from pydantic import BaseModel
from typing import List, Dict, Optional

# ---------------- COMMON MODELS ----------------

class RoleBaseModel(BaseModel):
    name: str


class RoleCreatedModel(RoleBaseModel):
    description: Optional[str] = None


class RoleReactivatedModel(RoleBaseModel):
    description: Optional[str] = None


class RoleFailedModel(BaseModel):
    name: str
    reason: str


# ---------------- CREATE ROLES RESPONSE ----------------

class ClientRolesResultModel(BaseModel):
    created: List[RoleCreatedModel] = []
    reactivated: List[RoleReactivatedModel] = []
    failed: List[RoleFailedModel] = []


class RolesResponseModel(BaseModel):
    results: Dict[str, ClientRolesResultModel]


# ---------------- DELETE ROLES RESPONSE ----------------

class ClientDeleteRolesResultModel(BaseModel):
    client_id: str
    deleted_roles: List[Dict]


class DeleteRolesResponseModel(BaseModel):
    message: str
    results: List[ClientDeleteRolesResultModel] = []

class RoleDeletedModel(BaseModel):
    name: str
    reason: Optional[str] = None 