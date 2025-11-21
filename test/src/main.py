from fastapi import FastAPI
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

from core.startup_script import lifespan
from core.logging_config import setup_logging, get_logger
from middlewares.logging_middleware import assign_req_id
from middlewares.register_exception import register_exception_handlers
from api_routes import api_router  # corrected path

# -------------------------------------------------------------------
# Setup logging before anything else
# -------------------------------------------------------------------
setup_logging()
logger = get_logger(__name__)

# -------------------------------------------------------------------
# FastAPI Application
# -------------------------------------------------------------------
app = FastAPI(
    title="Key-Cloak APIs",
    description="APIs for management of Keycloak permissions, resources, roles, and mappers",
    version="Python 3.11.13",
    lifespan=lifespan,
)

# -------------------------------------------------------------------
# Middleware configuration
# -------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request ID middleware for tracing
app.middleware("http")(assign_req_id)

# Register global exception handlers
register_exception_handlers(app)

# -------------------------------------------------------------------
# Include routers
# -------------------------------------------------------------------
app.include_router(api_router)

# -------------------------------------------------------------------
# Application entry point
# -------------------------------------------------------------------
if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        host="0.0.0.0",
        port=8000,
        reload=True,
        access_log=False,
        log_level="info",
    )

