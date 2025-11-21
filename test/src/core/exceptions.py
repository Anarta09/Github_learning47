from fastapi import HTTPException
from typing import Optional, Dict, Any
from core.logging_config import get_logger

logger = get_logger(__name__)


class BaseAPIException(HTTPException):
    def __init__(
        self, status_code: int, detail: str, headers: Optional[Dict[str, Any]] = None
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)


class KeyNotFoundException(BaseAPIException):
    def __init__(self, detail: str = "Encryption key not found"):
        super().__init__(status_code=404, detail=detail)


class DecryptionFailedException(BaseAPIException):
    def __init__(self, detail: str = "Decryption failed"):
        super().__init__(status_code=400, detail=detail)


class EncryptionFailedException(BaseAPIException):
    def __init__(self, detail: str = "Encryption failed"):
        super().__init__(status_code=400, detail=detail)


class KeyRotationException(BaseAPIException):
    def __init__(self, detail: str = "Key rotation failed"):
        super().__init__(status_code=500, detail=detail)


class ConfigurationException(BaseAPIException):
    def __init__(self, detail: str = "Configuration error"):
        super().__init__(status_code=500, detail=detail)


class ValidationException(BaseAPIException):
    def __init__(self, detail: str = "Validation failed"):
        super().__init__(status_code=422, detail=detail)
