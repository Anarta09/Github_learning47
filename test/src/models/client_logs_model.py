from sqlalchemy import Column, Integer, String, Boolean, TIMESTAMP, Text, ForeignKey
from sqlalchemy.orm import relationship
from database.db import Base
from models.client_model import Client

class ClientLogs(Base):
    __tablename__ = "client_logs"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(
        Integer,
        ForeignKey("client_details.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=True
    )
    action = Column(String, nullable=False)
    error_logs = Column(Text, nullable=True)
    performed_at = Column(TIMESTAMP, nullable=False)
    performed_by = Column(String, nullable=True)
    is_active = Column(Boolean, nullable=False)
    client_uuid = Column(String, nullable=True)

    client = relationship("Client", back_populates="logs")
