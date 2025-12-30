"""Custom exception classes and handlers for the server.

Provides consistent error responses across all API endpoints with
proper error codes, messages, and HTTP status codes.
"""

from typing import Any, Optional

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel


# ============================================================================
# Exception Classes
# ============================================================================


class APIError(Exception):
    """
    Base exception for API errors.

    Provides a consistent structure for all API errors:
    - HTTP status code
    - Error code (machine-readable)
    - Human-readable message
    - Optional additional details
    """

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code: str = "INTERNAL_ERROR"
    message: str = "An internal error occurred"

    def __init__(
        self,
        message: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ):
        self.message = message or self.__class__.message
        self.details = details or {}
        super().__init__(self.message)

    def to_response(self) -> dict[str, Any]:
        """Convert exception to API response format."""
        return {
            "code": self.error_code,
            "message": self.message,
            "details": self.details,
        }


class NotFoundError(APIError):
    """Resource not found error."""

    status_code = status.HTTP_404_NOT_FOUND
    error_code = "NOT_FOUND"
    message = "Resource not found"


class ProfileNotFoundError(NotFoundError):
    """Company profile not found error."""

    error_code = "PROFILE_NOT_FOUND"
    message = "Company profile not found"

    def __init__(self, profile_id: str):
        super().__init__(
            message=f"Company profile not found: {profile_id}",
            details={"profileId": profile_id},
        )


class DocumentNotFoundError(NotFoundError):
    """Document not found error."""

    error_code = "DOCUMENT_NOT_FOUND"
    message = "Document not found"

    def __init__(self, document_id: str):
        super().__init__(
            message=f"Document not found: {document_id}",
            details={"documentId": document_id},
        )


class GenerationNotFoundError(NotFoundError):
    """Generation request not found error."""

    error_code = "GENERATION_NOT_FOUND"
    message = "Generation request not found"

    def __init__(self, request_id: str):
        super().__init__(
            message=f"Generation request not found: {request_id}",
            details={"requestId": request_id},
        )


class ShareLinkNotFoundError(NotFoundError):
    """Share link not found error."""

    error_code = "SHARE_LINK_NOT_FOUND"
    message = "Share link not found"


class ConflictError(APIError):
    """Resource conflict error."""

    status_code = status.HTTP_409_CONFLICT
    error_code = "CONFLICT"
    message = "Resource conflict"


class GenerationInProgressError(ConflictError):
    """Generation already in progress error."""

    error_code = "GENERATION_IN_PROGRESS"
    message = "Generation already in progress"

    def __init__(self, request_id: str):
        super().__init__(
            message=f"Generation already in progress for request: {request_id}",
            details={"requestId": request_id},
        )


class ValidationError(APIError):
    """Validation error."""

    status_code = status.HTTP_400_BAD_REQUEST
    error_code = "VALIDATION_ERROR"
    message = "Validation error"


class InvalidConfigError(ValidationError):
    """Invalid swarm configuration error."""

    error_code = "INVALID_CONFIG"
    message = "Invalid swarm configuration"


class AuthenticationError(APIError):
    """Authentication error."""

    status_code = status.HTTP_401_UNAUTHORIZED
    error_code = "AUTHENTICATION_ERROR"
    message = "Authentication required"


class PasswordRequiredError(AuthenticationError):
    """Password required for share link error."""

    error_code = "PASSWORD_REQUIRED"
    message = "This share link requires a password"

    def __init__(self):
        super().__init__(details={"requiresPassword": True})


class InvalidPasswordError(AuthenticationError):
    """Invalid password error."""

    error_code = "INVALID_PASSWORD"
    message = "Invalid password"


class ResourceExpiredError(APIError):
    """Resource expired error."""

    status_code = status.HTTP_410_GONE
    error_code = "RESOURCE_EXPIRED"
    message = "Resource has expired"


class ShareLinkExpiredError(ResourceExpiredError):
    """Share link expired error."""

    error_code = "SHARE_LINK_EXPIRED"
    message = "This share link has expired"


class ServiceError(APIError):
    """Service-level error."""

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code = "SERVICE_ERROR"
    message = "Service error"


class ExportError(ServiceError):
    """Document export error."""

    error_code = "EXPORT_FAILED"
    message = "Document export failed"

    def __init__(self, document_id: str, format: str, reason: str):
        super().__init__(
            message=f"Failed to export document: {reason}",
            details={"documentId": document_id, "format": format},
        )


class WebSocketError(ServiceError):
    """WebSocket connection error."""

    error_code = "WS_CONNECTION_FAILED"
    message = "WebSocket connection failed"


class ServiceUnavailableError(APIError):
    """Service unavailable error."""

    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    error_code = "SERVICE_UNAVAILABLE"
    message = "Service temporarily unavailable"


class AgentsUnavailableError(ServiceUnavailableError):
    """Agent system unavailable error."""

    error_code = "AGENTS_UNAVAILABLE"
    message = "Agent system is not available"


class OperationError(APIError):
    """Operation failed error."""

    status_code = status.HTTP_400_BAD_REQUEST
    error_code = "OPERATION_FAILED"
    message = "Operation failed"


class PauseError(OperationError):
    """Failed to pause generation error."""

    error_code = "PAUSE_FAILED"

    def __init__(self, request_id: str):
        super().__init__(
            message=f"Cannot pause generation {request_id}. It may not be running.",
            details={"requestId": request_id},
        )


class ResumeError(OperationError):
    """Failed to resume generation error."""

    error_code = "RESUME_FAILED"

    def __init__(self, request_id: str):
        super().__init__(
            message=f"Cannot resume generation {request_id}. It may not be paused.",
            details={"requestId": request_id},
        )


class CancelError(OperationError):
    """Failed to cancel generation error."""

    error_code = "CANCEL_FAILED"

    def __init__(self, request_id: str):
        super().__init__(
            message=f"Cannot cancel generation {request_id}. It may already be complete.",
            details={"requestId": request_id},
        )


# ============================================================================
# Exception Handlers
# ============================================================================


async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    """Handle APIError exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.to_response()},
    )


async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    import logging
    import traceback

    logger = logging.getLogger(__name__)
    logger.error(f"Unexpected error: {exc}", exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "details": {},
            }
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers with the FastAPI app."""
    # Register API error handler
    app.add_exception_handler(APIError, api_error_handler)

    # Note: Generic handler should be last resort
    # Uncomment to enable catching all unhandled exceptions:
    # app.add_exception_handler(Exception, generic_error_handler)
