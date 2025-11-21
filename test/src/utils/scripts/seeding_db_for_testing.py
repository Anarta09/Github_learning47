from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlalchemy.orm import Session
from database.db import create_table, get_db
from database.models.lender_model import Lender
from database.models.user_model import User
from core.logging_config import get_logger
from datetime import datetime
import random

logger = get_logger(__name__)


def seed_database():
    """Insert 100 records into Lender and User tables"""
    db: Session = next(get_db())
    try:
        # Insert 100 lenders
        lenders = []
        for i in range(1, 101):
            lenders.append(
                Lender(
                    lender_id=f"L{i:03d}",
                    lender_name=f"Lender {i}",
                    lender_address=f"Address {i}",
                    lender_postal_code=f"{100000 + i}",
                )
            )
        db.bulk_save_objects(lenders)
        db.commit()
        logger.info("✅ Inserted 100 lenders")

        # Insert 100 users
        users = []
        for i in range(1, 101):
            users.append(
                User(
                    name=f"user{i}",
                    email=f"user{i}@example.com",
                    user_id=f"UID{i:03d}",
                    created_at=datetime.utcnow(),
                    modified_at=datetime.utcnow(),
                    client_ids=[random.randint(1, 10) for _ in range(3)],
                    is_active=True,
                    lender_id=f"L{i:03d}",  # Associate user with lender
                )
            )
        db.bulk_save_objects(users)
        db.commit()
        logger.info("✅ Inserted 100 users")
    except Exception as e:
        db.rollback()
        logger.error(f"Error seeding database: {str(e)}", exc_info=True)
        raise
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events with proper logging"""
    logger.info("=" * 50)
    logger.info("Running @asynccontextmanager before starting the application")
    logger.info("=" * 50)

    try:
        # Create tables if they don't exist
        logger.info("Creating database tables...")
        create_table()
        logger.info("Database tables created successfully")

        # Seed database
        logger.info("Seeding database with initial data...")
        seed_database()
        logger.info("Database seeding completed")

        logger.info("Application startup completed successfully")
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}", exc_info=True)
        raise

    yield

    logger.info("APPLICATION SHUTTING DOWN")
    logger.info("Cleanup completed")
