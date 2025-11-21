from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, JSON
from sqlalchemy.sql import func
from database.db import Base  # your declarative base

class ClientScopeLogs(Base):
    __tablename__ = "client_scope_logs"

    id = Column(Integer, primary_key=True, index=True)
    client_uuid = Column(Integer, nullable=True)
    client_id = Column(Integer, nullable=True)
    client_name = Column(String(255), nullable=True)
    action = Column(String(255), nullable=False)
    error_logs = Column(Text, nullable=True)
    performed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    performed_by = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    client_mapping_details = Column(JSON, nullable=True)
    operation = Column(Text, nullable=True)  # e.g., "Single Scope Operation" or "Bulk Mapper Operation"
