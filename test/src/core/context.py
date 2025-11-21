from contextvars import ContextVar
from typing import Optional

# Context variable to store request ID across async calls
request_id_context: ContextVar[Optional[str]] = ContextVar("request_id", default=None)


def get_request_id() -> str:
    """Get current request ID from context"""
    return request_id_context.get() or "unknown"


def set_request_id(request_id: str) -> None:
    """Set request ID in context"""
    request_id_context.set(request_id)
