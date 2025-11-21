from pydantic import BaseModel, Field
from typing import List,Optional

from config import settings


class CreateClientModel(BaseModel):
    clientId: str
    company_name: str
    email: str
    status: Optional[str] = "active"
    client_bucket_path: Optional[str] = None
    client_bucket_name: Optional[str] = None
    enabled: bool = True
    redirectUris: List[str] = Field(
        default_factory=lambda: [settings.DEFAULT_REDIRECT_URI]
    )
    publicClient: bool = False
    authorizationServicesEnabled: bool = True  # << enable resource server
    serviceAccountsEnabled: bool = True  # << required for confidential client
    directAccessGrantsEnabled: bool = True  # optional, if you want password grant

    import_from_client: Optional[str] = None  # clientId to import resources/scopes/permissions 


class UpdateClientModel(BaseModel):
    enabled: Optional[bool] = None
    redirectUris: Optional[List[str]] = None
    publicClient: Optional[bool] = None
    authorizationServicesEnabled: Optional[bool] = None
    serviceAccountsEnabled: Optional[bool] = None
    directAccessGrantsEnabled: Optional[bool] = None
    import_from_client: Optional[str] = None
