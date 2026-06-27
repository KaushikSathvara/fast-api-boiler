"""Application exception hierarchy and FastAPI exception handlers.

All custom exceptions inherit from `AppException` and map to HTTP status codes.
Exception handlers return the standard `APIResponse` envelope.
"""

from typing import Any, ClassVar

import structlog
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from starlette.responses import JSONResponse

__all__: list[str] = [
    "AppException",
    "NotFoundError",
    "ConflictError",
    "UnprocessableEntityError",
    "UnauthorizedError",
    "ForbiddenError",
    "ServiceUnavailableError",
    "register_exception_handlers",
]

logger = structlog.get_logger(__name__)


# ── Exception Hierarchy ──────────────────────────────────────────────────────


class AppException(Exception):
    """Base application exception.

    All subclasses define a `status_code` class variable that maps to an HTTP
    status code.
    """

    status_code: ClassVar[int] = 500
    message: str
    detail: dict[str, Any] | None

    def __init__(
        self,
        message: str = "An unexpected error occurred",
        detail: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.detail = detail
        super().__init__(message)


class NotFoundError(AppException):
    """Resource not found (404)."""

    status_code: ClassVar[int] = 404

    def __init__(
        self,
        message: str = "Resource not found",
        detail: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, detail=detail)


class ConflictError(AppException):
    """Resource conflict (409)."""

    status_code: ClassVar[int] = 409

    def __init__(
        self,
        message: str = "Resource already exists",
        detail: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, detail=detail)


class UnprocessableEntityError(AppException):
    """Unprocessable entity (422)."""

    status_code: ClassVar[int] = 422

    def __init__(
        self,
        message: str = "Unprocessable entity",
        detail: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, detail=detail)


class UnauthorizedError(AppException):
    """Unauthorized access (401)."""

    status_code: ClassVar[int] = 401

    def __init__(
        self,
        message: str = "Unauthorized",
        detail: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, detail=detail)


class ForbiddenError(AppException):
    """Forbidden access (403)."""

    status_code: ClassVar[int] = 403

    def __init__(
        self,
        message: str = "Forbidden",
        detail: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, detail=detail)


class ServiceUnavailableError(AppException):
    """Service unavailable (503)."""

    status_code: ClassVar[int] = 503

    def __init__(
        self,
        message: str = "Service unavailable",
        detail: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, detail=detail)


# ── Exception Handlers ───────────────────────────────────────────────────────


def _build_error_response(
    status_code: int,
    message: str,
    errors: list[dict[str, str]] | None = None,
    request_id: str | None = None,
) -> JSONResponse:
    """Build a standardized JSON error response."""
    from app.core.logging import request_id_ctx_var

    resolved_request_id = request_id or request_id_ctx_var.get("")
    body: dict[str, Any] = {
        "success": False,
        "data": None,
        "message": message,
        "errors": errors,
        "request_id": resolved_request_id or None,
    }
    return JSONResponse(status_code=status_code, content=body)


async def _app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle all AppException subclasses."""
    errors = [exc.detail] if exc.detail else None
    return _build_error_response(
        status_code=exc.status_code,
        message=exc.message,
        errors=[{k: str(v) for k, v in d.items()} for d in errors] if errors else None,
    )


async def _validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Handle Pydantic / FastAPI validation errors (422)."""
    errors: list[dict[str, str]] = []
    for error in exc.errors():
        loc = " → ".join(str(part) for part in error.get("loc", []))
        errors.append({"field": loc, "message": error.get("msg", "Validation error")})
    return _build_error_response(
        status_code=422,
        message="Validation error",
        errors=errors,
    )


async def _http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI/Starlette HTTPException with envelope wrapper."""
    return _build_error_response(
        status_code=exc.status_code,
        message=str(exc.detail) if exc.detail else "HTTP error",
    )


async def _unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all handler — log the traceback, never leak it to the client."""
    logger.exception("unhandled_exception", exc_type=type(exc).__name__, path=request.url.path)
    return _build_error_response(
        status_code=500,
        message="Internal server error",
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers on the FastAPI application."""
    app.add_exception_handler(AppException, _app_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, _validation_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(HTTPException, _http_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, _unhandled_exception_handler)  # type: ignore[arg-type]
