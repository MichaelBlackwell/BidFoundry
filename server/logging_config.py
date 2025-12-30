"""Structured logging configuration for the server.

Provides consistent logging format with request context, timing information,
and structured output for log aggregation systems.
"""

import logging
import sys
import time
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any, Optional
import json

from server.config import settings


# Context variables for request tracking
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
connection_id_var: ContextVar[Optional[str]] = ContextVar("connection_id", default=None)


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs structured JSON logs.

    Includes:
    - Timestamp in ISO format
    - Log level
    - Logger name
    - Message
    - Request/connection context when available
    - Extra fields
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        log_data: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add request context if available
        request_id = request_id_var.get()
        if request_id:
            log_data["request_id"] = request_id

        connection_id = connection_id_var.get()
        if connection_id:
            log_data["connection_id"] = connection_id

        # Add location info for errors
        if record.levelno >= logging.ERROR:
            log_data["location"] = {
                "file": record.pathname,
                "line": record.lineno,
                "function": record.funcName,
            }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add any extra fields
        extra_fields = {
            k: v
            for k, v in record.__dict__.items()
            if k not in {
                "name", "msg", "args", "created", "filename", "funcName",
                "levelname", "levelno", "lineno", "module", "msecs",
                "pathname", "process", "processName", "relativeCreated",
                "stack_info", "exc_info", "exc_text", "thread", "threadName",
                "message", "asctime",
            }
        }
        if extra_fields:
            log_data["extra"] = extra_fields

        return json.dumps(log_data)


class ConsoleFormatter(logging.Formatter):
    """
    Human-readable console formatter with colors.

    Uses ANSI color codes for different log levels:
    - DEBUG: Dim/Gray
    - INFO: Default
    - WARNING: Yellow
    - ERROR: Red
    - CRITICAL: Bold Red
    """

    COLORS = {
        "DEBUG": "\033[90m",      # Gray
        "INFO": "\033[0m",        # Default
        "WARNING": "\033[33m",    # Yellow
        "ERROR": "\033[31m",      # Red
        "CRITICAL": "\033[1;31m", # Bold Red
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        """Format log record for console output."""
        # Get timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Build context string
        context_parts = []
        request_id = request_id_var.get()
        if request_id:
            context_parts.append(f"req={request_id[:8]}")
        connection_id = connection_id_var.get()
        if connection_id:
            context_parts.append(f"conn={connection_id[:8]}")
        context_str = f" [{', '.join(context_parts)}]" if context_parts else ""

        # Get color for level
        color = self.COLORS.get(record.levelname, "")

        # Format message
        message = record.getMessage()

        # Build output
        output = f"{timestamp} {color}{record.levelname:8}{self.RESET} {record.name}{context_str}: {message}"

        # Add exception if present
        if record.exc_info:
            output += f"\n{self.formatException(record.exc_info)}"

        return output


def setup_logging(
    log_level: str = "INFO",
    json_output: bool = False,
    log_file: Optional[str] = None,
) -> None:
    """
    Configure logging for the application.

    Args:
        log_level: Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_output: If True, output structured JSON logs
        log_file: Optional file path for log output
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers
    root_logger.handlers.clear()

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))

    # Set formatter based on output mode
    if json_output:
        console_handler.setFormatter(StructuredFormatter())
    else:
        console_handler.setFormatter(ConsoleFormatter())

    root_logger.addHandler(console_handler)

    # Add file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_handler.setFormatter(StructuredFormatter())  # Always JSON for files
        root_logger.addHandler(file_handler)

    # Configure specific loggers
    _configure_library_loggers()


def _configure_library_loggers() -> None:
    """Configure log levels for third-party libraries."""
    # Reduce noise from common libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("websockets").setLevel(logging.WARNING)

    # Keep our application logs at the configured level
    logging.getLogger("server").setLevel(logging.DEBUG if settings.debug else logging.INFO)


class RequestContextLogger:
    """
    Context manager for logging with request context.

    Usage:
        with RequestContextLogger(request_id="req_123"):
            logger.info("Processing request")
    """

    def __init__(
        self,
        request_id: Optional[str] = None,
        connection_id: Optional[str] = None,
    ):
        self.request_id = request_id
        self.connection_id = connection_id
        self._tokens: list = []

    def __enter__(self) -> "RequestContextLogger":
        if self.request_id:
            self._tokens.append(request_id_var.set(self.request_id))
        if self.connection_id:
            self._tokens.append(connection_id_var.set(self.connection_id))
        return self

    def __exit__(self, *args) -> None:
        for token in self._tokens:
            try:
                if hasattr(token, "var"):
                    token.var.reset(token)
            except ValueError:
                pass


def set_request_context(
    request_id: Optional[str] = None,
    connection_id: Optional[str] = None,
) -> None:
    """Set the current request context for logging."""
    if request_id:
        request_id_var.set(request_id)
    if connection_id:
        connection_id_var.set(connection_id)


def clear_request_context() -> None:
    """Clear the current request context."""
    request_id_var.set(None)
    connection_id_var.set(None)


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the given name."""
    return logging.getLogger(name)
