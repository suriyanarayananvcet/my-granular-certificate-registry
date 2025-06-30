import logging
from typing import Any, Dict, Optional

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


class ErrorResponse:
    """Standardized error response format."""

    def __init__(
        self,
        status_code: int,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        error_type: Optional[str] = None,
    ):
        self.status_code = status_code
        self.message = message
        self.details = details or {}
        self.error_type = error_type or "error"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status_code": self.status_code,
            "message": self.message,
            "details": self.details,
            "error_type": self.error_type,
        }


def format_validation_error(error: RequestValidationError) -> ErrorResponse:
    """Format Pydantic validation errors into a user-friendly format."""
    details = {}
    for err in error.errors():
        loc = " -> ".join(str(x) for x in err["loc"])
        details[loc] = {"message": err["msg"], "type": err["type"]}

    return ErrorResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        message="Validation error occurred",
        details=details,
        error_type="validation_error",
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors."""
    error_response = format_validation_error(exc)
    logger.warning(f"Validation error: {error_response.to_dict()}")
    return JSONResponse(
        status_code=error_response.status_code, content=error_response.to_dict()
    )


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Handle HTTP exceptions."""
    error_response = ErrorResponse(
        status_code=exc.status_code, message=str(exc.detail), error_type="http_error"
    )
    logger.warning(f"HTTP error: {error_response.to_dict()}")
    return JSONResponse(
        status_code=error_response.status_code, content=error_response.to_dict()
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all other exceptions."""
    error_response = ErrorResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        message="An unexpected error occurred",
        details={"error": str(exc)},
        error_type="server_error",
    )
    logger.error(f"Unexpected error: {error_response.to_dict()}", exc_info=True)
    return JSONResponse(
        status_code=error_response.status_code, content=error_response.to_dict()
    )
