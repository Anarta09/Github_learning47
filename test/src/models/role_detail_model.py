from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from database.db import Base

class RoleDetail(Base):
    __tablename__ = "role_details"
    __table_args__ = {"schema": "public"}  # <-- set schema

    id = Column(Integer, primary_key=True, index=True)
    role_uuid = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)
    role_name = Column(String(255), nullable=False)
    client_id = Column(
        Integer,
        ForeignKey("client_details.id", ondelete="CASCADE", onupdate="CASCADE"),  # keep table as-is
        nullable=False
    )
    client_uuid = Column(UUID(as_uuid=True), nullable=True)
    client_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now(), nullable=True)
    created_by = Column(String(255), nullable=True)
    updated_by = Column(String(255), nullable=True)
