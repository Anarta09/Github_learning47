from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from core.logging_config import get_logger
from core.exceptions import BaseAPIException
from fastapi.exceptions import RequestValidationError
from custom_exeptions import CustomException
logger = get_logger(__name__)


# Exception Handlers Registration
def register_exception_handlers(app: FastAPI):

    @app.exception_handler(BaseAPIException)
    async def handle_api_exception(request: Request, exc: BaseAPIException):
        request_id = getattr(request.state, "request_id", "unknown")
        logger.error(
            f"[{request_id}] API Exception: {exc.__class__.__name__} - {exc.detail}"
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.__class__.__name__,
                "message": exc.detail,
                "request_id": request_id,
            },
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        request_id = getattr(request.state, "request_id", "unknown")
        logger.warning(f"[{request_id}] Validation Error: {exc.errors()}")
        return JSONResponse(
            status_code=422,
            content={
                "error": "ValidationError",
                "message": exc.errors(),
                "request_id": request_id,
            },
        )

    @app.exception_handler(Exception)
    async def handle_generic_exception(request: Request, exc: Exception):
        request_id = getattr(request.state, "request_id", "unknown")
        logger.error(f"[{request_id}] Unhandled Exception: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "InternalServerError",
                "message": "An unexpected error occurred",
                "request_id": request_id,
            },
        )
    @app.exception_handler(CustomException)
    async def handle_custom_exceptions(request, exc):
        logger.error(f'Custom Exception handler.....{type(exc)}, {exc}')
        return exc.to_response()    
