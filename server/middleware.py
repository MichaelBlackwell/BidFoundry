"""Middleware for the FastAPI server.

Provides:
- Request/Response logging
- Request timing
- Request ID tracking
- Error rate monitoring
"""

import logging
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Optional

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from server.logging_config import set_request_context, clear_request_context


logger = logging.getLogger(__name__)


# ============================================================================
# Request ID Middleware
# ============================================================================


class RequestIdMiddleware(BaseHTTPMiddleware):
    """
    Middleware that assigns a unique ID to each request.

    The request ID is:
    - Generated if not provided in X-Request-ID header
    - Added to response headers
    - Available for logging via request.state.request_id
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get or generate request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id

        # Set logging context
        set_request_context(request_id=request_id)

        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            clear_request_context()


# ============================================================================
# Logging Middleware
# ============================================================================


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that logs HTTP requests and responses.

    Logs include:
    - Request method, path, and client IP
    - Response status code
    - Request duration in milliseconds
    - Request ID for correlation
    """

    # Paths to skip logging (health checks, etc.)
    SKIP_PATHS = {"/health", "/ws"}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip logging for certain paths
        if request.url.path in self.SKIP_PATHS:
            return await call_next(request)

        # Get request details
        method = request.method
        path = request.url.path
        client_ip = self._get_client_ip(request)
        request_id = getattr(request.state, "request_id", "unknown")

        # Time the request
        start_time = time.perf_counter()

        # Log request start
        logger.info(
            f"Request started: {method} {path}",
            extra={
                "http_method": method,
                "http_path": path,
                "client_ip": client_ip,
                "request_id": request_id,
            },
        )

        try:
            response = await call_next(request)
            duration_ms = (time.perf_counter() - start_time) * 1000

            # Log based on status code
            log_level = logging.INFO if response.status_code < 400 else logging.WARNING
            if response.status_code >= 500:
                log_level = logging.ERROR

            logger.log(
                log_level,
                f"Request completed: {method} {path} - {response.status_code} ({duration_ms:.2f}ms)",
                extra={
                    "http_method": method,
                    "http_path": path,
                    "http_status": response.status_code,
                    "duration_ms": duration_ms,
                    "request_id": request_id,
                },
            )

            # Add timing header
            response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"

            return response

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                f"Request failed: {method} {path} - {type(e).__name__}: {e}",
                extra={
                    "http_method": method,
                    "http_path": path,
                    "error": str(e),
                    "duration_ms": duration_ms,
                    "request_id": request_id,
                },
                exc_info=True,
            )
            raise

    def _get_client_ip(self, request: Request) -> str:
        """Get the client IP address from the request."""
        # Check for forwarded header (behind proxy)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        # Fall back to direct connection
        return request.client.host if request.client else "unknown"


# ============================================================================
# Metrics Middleware
# ============================================================================


@dataclass
class RequestMetrics:
    """Container for request metrics."""

    total_requests: int = 0
    total_errors: int = 0
    status_codes: dict = field(default_factory=lambda: defaultdict(int))
    endpoint_counts: dict = field(default_factory=lambda: defaultdict(int))
    endpoint_durations: dict = field(default_factory=lambda: defaultdict(list))
    last_reset: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def record_request(
        self,
        path: str,
        status_code: int,
        duration_ms: float,
    ) -> None:
        """Record metrics for a request."""
        self.total_requests += 1
        if status_code >= 400:
            self.total_errors += 1
        self.status_codes[status_code] += 1
        self.endpoint_counts[path] += 1

        # Keep last 100 durations per endpoint
        durations = self.endpoint_durations[path]
        durations.append(duration_ms)
        if len(durations) > 100:
            self.endpoint_durations[path] = durations[-100:]

    def get_stats(self) -> dict:
        """Get current metrics as a dictionary."""
        stats = {
            "total_requests": self.total_requests,
            "total_errors": self.total_errors,
            "error_rate": (
                self.total_errors / self.total_requests * 100
                if self.total_requests > 0
                else 0
            ),
            "status_codes": dict(self.status_codes),
            "endpoints": {},
            "since": self.last_reset.isoformat(),
        }

        # Calculate endpoint stats
        for path, durations in self.endpoint_durations.items():
            if durations:
                stats["endpoints"][path] = {
                    "count": self.endpoint_counts[path],
                    "avg_ms": sum(durations) / len(durations),
                    "min_ms": min(durations),
                    "max_ms": max(durations),
                }

        return stats

    def reset(self) -> None:
        """Reset all metrics."""
        self.total_requests = 0
        self.total_errors = 0
        self.status_codes.clear()
        self.endpoint_counts.clear()
        self.endpoint_durations.clear()
        self.last_reset = datetime.now(timezone.utc)


# Global metrics instance
_metrics = RequestMetrics()


def get_metrics() -> RequestMetrics:
    """Get the global metrics instance."""
    return _metrics


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware that collects request metrics.

    Tracks:
    - Total request count
    - Error count and rate
    - Status code distribution
    - Response times per endpoint
    """

    # Paths to skip metrics collection
    SKIP_PATHS = {"/health", "/metrics", "/ws"}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip metrics for certain paths
        if request.url.path in self.SKIP_PATHS:
            return await call_next(request)

        start_time = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start_time) * 1000

        # Record metrics
        _metrics.record_request(
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
        )

        return response


# ============================================================================
# Middleware Registration
# ============================================================================


def register_middleware(app: FastAPI) -> None:
    """
    Register all middleware with the FastAPI app.

    Order matters! Middleware is applied in reverse order of registration.
    Last registered = first to process request, last to process response.
    """
    # Register in reverse order of desired execution
    app.add_middleware(MetricsMiddleware)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(RequestIdMiddleware)


def add_metrics_endpoint(app: FastAPI) -> None:
    """Add a metrics endpoint to the FastAPI app."""

    @app.get("/metrics", tags=["monitoring"])
    async def get_request_metrics() -> dict:
        """
        Get request metrics.

        Returns aggregated metrics including:
        - Total request and error counts
        - Error rate percentage
        - Status code distribution
        - Per-endpoint statistics (count, avg/min/max response time)
        """
        return _metrics.get_stats()

    @app.post("/metrics/reset", tags=["monitoring"])
    async def reset_request_metrics() -> dict:
        """Reset all request metrics."""
        _metrics.reset()
        return {"status": "reset", "timestamp": datetime.now(timezone.utc).isoformat()}
