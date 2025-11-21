from sqlalchemy import Column, Integer, String, Boolean, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship

from database.db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    email = Column(String, nullable=False)
    user_id = Column(String, nullable=False, unique=True)
    created_at = Column(TIMESTAMP, nullable=False)
    modified_at = Column(TIMESTAMP, nullable=False)
    client_name = Column(String, nullable=True)
    org_id = Column(Integer, nullable=True)

    lender_id = Column(String, ForeignKey("lender.lender_id"), nullable=True)

    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    last_activity = Column(String, nullable=True)
    role = Column(String, nullable=True)
    client_ids = Column(ARRAY(Integer), nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    kc_client = Column(String, nullable=True)

    # Relationship with lender
    lender = relationship("Lender", back_populates="users")
