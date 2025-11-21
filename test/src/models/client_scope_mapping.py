from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database.db import Base
from database.models.client_model import Client

class ClientScopeMapping(Base):
    __tablename__ = "client_scope_mapping"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("client_details.id"), nullable=False)
    scope_id = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)

    client = relationship("Client", backref="scopes")
