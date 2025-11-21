from sqlalchemy import Column, Integer, String, Boolean, TIMESTAMP
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from database.db import Base

class Client(Base):
    __tablename__ = "client_details"
    __table_args__ = {"extend_existing": True}  # <-- prevents duplicate table definition

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    display_client_id = Column(String, nullable=False, unique=True)  # no default
    client_name = Column(String, nullable=False)
    company_name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    client_bucket_path = Column(String, nullable=True)
    client_bucket_name = Column(String, nullable=True)
    client_uuid = Column(String, nullable=False, unique=True)  # from Keycloak
    client_mapper = Column(JSONB, nullable=True)
    last_updated_at = Column(TIMESTAMP, nullable=True)
    last_updated_by = Column(String, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False)
    created_by = Column(String, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)

    # Relationship with client logs
    logs = relationship(
        "ClientLogs",
        back_populates="client",
        cascade="all, delete-orphan"
    )
