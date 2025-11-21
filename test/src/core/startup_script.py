from contextlib import asynccontextmanager
from fastapi import FastAPI
from core.logging_config import get_logger
from dependencies.auth_dep import get_admin_token
from utils.token import start_token_scheduler, stop_token_scheduler

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events with proper logging"""
    # Startup
    logger.info("=" * 50)
    logger.info("Running @asynccontextmanager before starting the application")
    logger.info("=" * 50)

    try:
        # Start the background token scheduler
        start_token_scheduler()
        logger.info("Admin token scheduler started successfully")

        # Optional: you can fetch or log the initial token if required
        # token = get_admin_token()
        # logger.debug(f"Initial admin token fetched: {token}")

        logger.info("Application startup completed successfully")

    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}", exc_info=True)
        raise

    # Application running
    yield

    # Shutdown
    try:
        stop_token_scheduler()
        logger.info("Admin token scheduler stopped successfully")
    except Exception as e:
        logger.error(f"Error while stopping token scheduler: {e}", exc_info=True)

    logger.info("APPLICATION SHUTTING DOWN")
    logger.info("Cleanup completed")
