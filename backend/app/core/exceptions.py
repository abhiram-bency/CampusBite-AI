"""Common exception hierarchy and centralized exception handling.

Domain services and repositories should raise the exceptions defined
here (or subclasses of them) instead of raising raw
``HTTPException``/``Exception`` instances. This keeps error semantics
consistent across WhatsApp, React, and future mobile/kiosk consumers of
the API.
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import get_logger

logger = get_logger(__name__)


class AppError(Exception):
    """Base class for all application-raised errors.

    Attributes:
        message: Human-readable error message.
        status_code: HTTP status code to return to API clients.
        error_code: Stable machine-readable identifier for the error,
            useful for the WhatsApp bot and frontend to branch on.
        details: Optional structured context about the error.
    """

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code: str = "internal_error"

    def __init__(
        self,
        message: str = "An unexpected error occurred.",
        *,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.details = details or {}
        super().__init__(message)


class NotFoundError(AppError):
    """Raised when a requested resource does not exist."""

    status_code = status.HTTP_404_NOT_FOUND
    error_code = "not_found"

    def __init__(self, message: str = "Resource not found.", **kwargs: Any) -> None:
        super().__init__(message, **kwargs)


class ValidationAppError(AppError):
    """Raised for domain-level validation failures (not request parsing)."""

    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    error_code = "validation_error"

    def __init__(self, message: str = "Validation failed.", **kwargs: Any) -> None:
        super().__init__(message, **kwargs)


class ConflictError(AppError):
    """Raised when an operation conflicts with the current state (e.g.
    duplicate registration number, double-booking a pickup slot)."""

    status_code = status.HTTP_409_CONFLICT
    error_code = "conflict"

    def __init__(self, message: str = "Resource conflict.", **kwargs: Any) -> None:
        super().__init__(message, **kwargs)


class UnauthorizedError(AppError):
    """Raised when authentication is missing or invalid."""

    status_code = status.HTTP_401_UNAUTHORIZED
    error_code = "unauthorized"

    def __init__(self, message: str = "Authentication required.", **kwargs: Any) -> None:
        super().__init__(message, **kwargs)


class ForbiddenError(AppError):
    """Raised when an authenticated actor lacks permission for an action."""

    status_code = status.HTTP_403_FORBIDDEN
    error_code = "forbidden"

    def __init__(self, message: str = "Permission denied.", **kwargs: Any) -> None:
        super().__init__(message, **kwargs)


class ServiceUnavailableError(AppError):
    """Raised when a required downstream dependency is unavailable
    (e.g. PostgreSQL, Redis, WhatsApp Cloud API, an LLM provider)."""

    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    error_code = "service_unavailable"

    def __init__(
        self, message: str = "A required service is unavailable.", **kwargs: Any
    ) -> None:
        super().__init__(message, **kwargs)


def _error_response(
    *, status_code: int, error_code: str, message: str, details: dict[str, Any] | None = None
) -> JSONResponse:
    """Build a consistent JSON error envelope for all API clients."""
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": error_code,
                "message": message,
                "details": details or {},
            }
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Attach centralized exception handlers to the FastAPI application.

    Called once during application startup from :mod:`app.main`.
    """

    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        logger.warning(
            "Handled application error",
            extra={
                "extra_fields": {
                    "path": request.url.path,
                    "error_code": exc.error_code,
                    "message": exc.message,
                }
            },
        )
        return _error_response(
            status_code=exc.status_code,
            error_code=exc.error_code,
            message=exc.message,
            details=exc.details,
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        logger.info(
            "Request validation failed",
            extra={"extra_fields": {"path": request.url.path, "errors": exc.errors()}},
        )
        return _error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="request_validation_error",
            message="The request payload failed validation.",
            details={"errors": exc.errors()},
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        return _error_response(
            status_code=exc.status_code,
            error_code="http_error",
            message=str(exc.detail),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(
            "Unhandled exception",
            extra={"extra_fields": {"path": request.url.path}},
        )
        return _error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="internal_error",
            message="An unexpected error occurred. Please try again later.",
        )
