import datetime
import logging
import traceback
from typing import Any, Dict, Union

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from starlette.exceptions import HTTPException as StarletteHTTPException

from gc_registry.settings import settings

logger = logging.getLogger(__name__)


class ErrorResponse(Exception):
    """Standardised error response format."""

    def __init__(
        self,
        status_code: int,
        message: str,
        *,
        request: Request | None = None,
        details: dict[str, Any] | None = None,
        error_type: str = "error",
        exc: Exception | None = None,  # <- the original exception
        include_stack: bool = False,  # default off unless caller opts-in
    ) -> None:
        self.timestamp = (
            datetime.datetime.now()
        )  # use local timezone for error timestamp
        self.status_code = status_code
        self.message = message
        self.error_type = error_type
        self.details = details or {}

        # Light-weight request context
        if request:
            self.details.update(
                {
                    "method": request.method,
                    "path": request.url.path,
                    "endpoint": (
                        f"{request.scope['endpoint'].__module__}."
                        f"{request.scope['endpoint'].__name__}"
                        if request.scope.get("endpoint")
                        else None
                    ),
                }
            )

        # Add stack trace only when explicitly requested **and** we have a real
        # exception object with a traceback.
        if include_stack and exc and exc.__traceback__:
            tb_exc = traceback.TracebackException.from_exception(exc)
            stack_frames = tb_exc.stack  # type: ignore[attr-defined]

            if stack_frames:  # Defensive: could still be empty
                last = stack_frames[-1]
                self.details["source_location"] = {
                    "file": last.filename,
                    "line": last.lineno,
                    "function": last.name,
                }

            self.details["stack"] = tb_exc.format().splitlines()  # type: ignore[attr-defined]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status_code": self.status_code,
            "error_message": self.message,
            "details": self.details,
            "error_type": self.error_type,
        }


def _extract_value(body: Any, path: tuple[Any, ...]) -> Any:
    """
    Walk the request body using the error location to fetch the offending value
    ('body', 'foo', 0, 'bar') → body['foo'][0]['bar']
    """
    try:
        cur = body
        for part in path[1:]:
            if isinstance(cur, dict):
                cur = cur.get(part)
            elif isinstance(cur, list):
                cur = cur[part]
            else:
                return None
        return cur
    except Exception:
        return None


def format_validation_error(
    exc: RequestValidationError,
    request: Request,
) -> ErrorResponse:
    body = exc.body
    enriched: list[dict[str, Any]] = []

    for err in exc.errors():
        loc_tuple: tuple[Any, ...] = err["loc"]
        # Ensure ctx is JSON-serializable (no raw Error types)
        ctx = err.get("ctx", {})
        if ctx and isinstance(ctx, dict):
            ctx = {
                k: (str(v) if isinstance(v, BaseException) else v)
                for k, v in ctx.items()
            }
        enriched.append(
            {
                "location": " -> ".join(str(x) for x in loc_tuple),
                "field": loc_tuple[-1] if len(loc_tuple) > 1 else None,
                "invalid_value": _extract_value(body, loc_tuple),
                "message": err["msg"],
                "type": err["type"],
                "ctx": ctx,
            }
        )

    return ErrorResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        message="Validation error",
        request=request,
        details={"errors": enriched},
        error_type="validation_error",
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    error_response = format_validation_error(exc, request)
    logger.warning("Validation error", extra=error_response.to_dict())
    return JSONResponse(
        status_code=error_response.status_code,
        content=error_response.to_dict(),
    )


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> Union[Response, JSONResponse]:
    """Handle HTTP exceptions."""
    error_response = ErrorResponse(
        status_code=exc.status_code, message=str(exc.detail), error_type="http_error"
    )
    logger.warning(f"HTTP error: {error_response.to_dict()}")
    return JSONResponse(
        status_code=error_response.status_code, content=error_response.to_dict()
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    # Only expose the stack trace outside PROD
    show_stack = settings.ENVIRONMENT != "PROD"
    error_response = ErrorResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        message=str(exc),
        request=request,
        details={"exception_type": type(exc).__name__},
        error_type="server_error",
        include_stack=show_stack,
    )
    logger.error("Unhandled exception", exc_info=True, extra=error_response.to_dict())
    return JSONResponse(
        status_code=error_response.status_code,
        content=error_response.to_dict(),
    )
