from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

# from app.core.db import Base
from database.db import Base


class Lender(Base):
    __tablename__ = "lender"

    lender_id = Column(String, primary_key=True, index=True)
    lender_name = Column(String, nullable=False)
    lender_address = Column(String, nullable=True)
    lender_postal_code = Column(String, nullable=True)

    # Backref to users
    users = relationship("User", back_populates="lender")
