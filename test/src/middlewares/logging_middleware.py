import time
import uuid
from fastapi import Request
from core.logging_config import get_logger
from core.context import set_request_id

logger = get_logger(__name__)


async def assign_req_id(request: Request, call_next):
    """Middleware to log HTTP requests and responses"""

    # Generate request ID for tracking
    request_id = str(uuid.uuid4())[:8]
    start_time = time.time()

    # Set request ID in both request state AND context
    request.state.request_id = request_id
    set_request_id(request_id)  # Add this line

    # Log request
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Client: {request.client.host if request.client else 'unknown'}"
    )

    try:
        response = await call_next(request)

        # Calculate response time
        process_time = time.time() - start_time

        # Log response
        logger.info(
            f"{request.method} {request.url.path} - "
            f"Status: {response.status_code} - Time: {process_time:.3f}s"
        )

        return response

    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            f"{request.method} {request.url.path} - "
            f"ERROR: {str(e)} - Time: {process_time:.3f}s",
            exc_info=True,
        )
        raise
