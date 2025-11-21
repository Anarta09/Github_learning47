from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from database.db import Base

class RoleLog(Base):
    __tablename__ = "role_logs"
    __table_args__ = {"schema": "public"}  # <-- set schema

    id = Column(Integer, primary_key=True, index=True)
    role_id = Column(
        Integer,
        ForeignKey("public.role_details.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False
    )
    client_id = Column(
        Integer,
        ForeignKey("client_details.id", ondelete="CASCADE", onupdate="CASCADE"),  # keep table as-is
        nullable=False
    )
    action = Column(String(255), nullable=False)
    error_logs = Column(Text, nullable=True)
    performed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    performed_by = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
