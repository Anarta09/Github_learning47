from sqlalchemy import create_engine,text
from sqlalchemy.orm import sessionmaker, declarative_base

from config import settings

DATABASE_URL = settings.POSTGRES_DATABASE_URL

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

from models import user_model, lender_model # <-- ADD THIS LINE


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        db.execute(text("SET search_path TO public"))
        yield db
    finally:
        db.close()
