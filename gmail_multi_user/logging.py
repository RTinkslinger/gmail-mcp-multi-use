"""Structured logging for gmail-multi-user-mcp.

Provides JSON-formatted logging for production and human-readable
format for development.

Example:
    from gmail_multi_user.logging import get_logger, LogContext

    logger = get_logger(__name__)

    # Basic logging
    logger.info("Processing request", operation="search")

    # With context
    with LogContext(user_id="user_123", connection_id="conn_456"):
        logger.info("Searching messages", query="is:unread")
"""

from __future__ import annotations

import json
import logging
import os
import sys
import threading
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any

# Context variables for request tracing
_log_context: ContextVar[dict[str, Any] | None] = ContextVar("log_context", default=None)


class LogContext:
    """Context manager for adding context to log messages.

    Example:
        with LogContext(user_id="user_123", connection_id="conn_456"):
            logger.info("Processing request")
            # Log will include user_id and connection_id
    """

    def __init__(self, **kwargs: Any) -> None:
        """Initialize log context with key-value pairs."""
        self._context = kwargs
        self._token: Any = None

    def __enter__(self) -> LogContext:
        """Enter context, merging with existing context."""
        existing = _log_context.get()
        current = existing.copy() if existing else {}
        current.update(self._context)
        self._token = _log_context.set(current)
        return self

    def __exit__(self, *args: Any) -> None:
        """Exit context, restoring previous context."""
        if self._token is not None:
            _log_context.reset(self._token)


def get_context() -> dict[str, Any]:
    """Get the current logging context."""
    ctx = _log_context.get()
    return ctx.copy() if ctx else {}


def set_context(**kwargs: Any) -> None:
    """Set logging context values (use LogContext for scoped context)."""
    existing = _log_context.get()
    current = existing.copy() if existing else {}
    current.update(kwargs)
    _log_context.set(current)


def clear_context() -> None:
    """Clear all logging context."""
    _log_context.set({})


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging.

    Output format:
    {
        "timestamp": "2024-01-15T10:30:00.000Z",
        "level": "INFO",
        "logger": "gmail_multi_user.service",
        "message": "Searching messages",
        "operation": "search",
        "user_id": "user_123",
        "connection_id": "conn_456"
    }
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as JSON."""
        # Base fields
        log_entry: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add context from ContextVar
        context = get_context()
        if context:
            log_entry.update(context)

        # Add extra fields from the record
        # These are passed via logger.info("msg", extra={"key": "value"})
        # or via our custom adapter
        for key, value in record.__dict__.items():
            if key not in (
                "name", "msg", "args", "created", "filename", "funcName",
                "levelname", "levelno", "lineno", "module", "msecs",
                "pathname", "process", "processName", "relativeCreated",
                "stack_info", "exc_info", "exc_text", "thread", "threadName",
                "message", "taskName",
            ):
                # Include custom fields
                if not key.startswith("_"):
                    log_entry[key] = value

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, default=str)


class HumanFormatter(logging.Formatter):
    """Human-readable formatter for development.

    Output format:
    2024-01-15 10:30:00 INFO  [gmail_multi_user.service] Searching messages | operation=search user_id=user_123
    """

    COLORS = {
        "DEBUG": "\033[36m",     # Cyan
        "INFO": "\033[32m",      # Green
        "WARNING": "\033[33m",   # Yellow
        "ERROR": "\033[31m",     # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def __init__(self, use_colors: bool = True) -> None:
        """Initialize formatter with optional color support."""
        super().__init__()
        self.use_colors = use_colors and sys.stderr.isatty()

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record for human readability."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Color the level name
        level = record.levelname.ljust(5)
        if self.use_colors and record.levelname in self.COLORS:
            level = f"{self.COLORS[record.levelname]}{level}{self.RESET}"

        # Build base message
        parts = [f"{timestamp} {level} [{record.name}] {record.getMessage()}"]

        # Add context fields
        context = get_context()
        extra_fields: dict[str, Any] = {}
        extra_fields.update(context)

        # Add extra fields from record
        for key, value in record.__dict__.items():
            if key not in (
                "name", "msg", "args", "created", "filename", "funcName",
                "levelname", "levelno", "lineno", "module", "msecs",
                "pathname", "process", "processName", "relativeCreated",
                "stack_info", "exc_info", "exc_text", "thread", "threadName",
                "message", "taskName",
            ):
                if not key.startswith("_"):
                    extra_fields[key] = value

        if extra_fields:
            field_str = " ".join(f"{k}={v}" for k, v in extra_fields.items())
            parts.append(f"| {field_str}")

        result = " ".join(parts)

        # Add exception info if present
        if record.exc_info:
            result += f"\n{self.formatException(record.exc_info)}"

        return result


class StructuredLoggerAdapter(logging.LoggerAdapter):
    """Logger adapter that supports keyword arguments for structured logging.

    Example:
        logger.info("Searching messages", query="is:unread", max_results=10)
    """

    def __init__(self, logger: logging.Logger, extra: dict[str, Any] | None = None) -> None:
        """Initialize the adapter."""
        super().__init__(logger, extra or {})

    def process(
        self, msg: str, kwargs: dict[str, Any]
    ) -> tuple[str, dict[str, Any]]:
        """Process the logging call to add extra fields."""
        # Move non-standard kwargs to extra
        extra = kwargs.get("extra", {})
        extra.update(self.extra or {})

        # Extract our custom fields (not standard logging kwargs)
        standard_kwargs = {"exc_info", "stack_info", "stacklevel", "extra"}
        for key in list(kwargs.keys()):
            if key not in standard_kwargs:
                extra[key] = kwargs.pop(key)

        kwargs["extra"] = extra
        return msg, kwargs

    def debug(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log debug message with optional structured fields."""
        self.log(logging.DEBUG, msg, *args, **kwargs)

    def info(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log info message with optional structured fields."""
        self.log(logging.INFO, msg, *args, **kwargs)

    def warning(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log warning message with optional structured fields."""
        self.log(logging.WARNING, msg, *args, **kwargs)

    def error(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log error message with optional structured fields."""
        self.log(logging.ERROR, msg, *args, **kwargs)

    def critical(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log critical message with optional structured fields."""
        self.log(logging.CRITICAL, msg, *args, **kwargs)


# Module-level configuration
_configured = False
_lock = threading.Lock()


def configure_logging(
    level: str | int = "INFO",
    json_format: bool | None = None,
    stream: Any = None,
) -> None:
    """Configure the logging system.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL) or int.
        json_format: Use JSON format. If None, auto-detect based on
            GMAIL_MCP_LOG_FORMAT env var or whether running in TTY.
        stream: Output stream. Defaults to stderr.

    Environment variables:
        GMAIL_MCP_LOG_LEVEL: Set log level
        GMAIL_MCP_LOG_FORMAT: "json" or "human"
    """
    global _configured

    with _lock:
        if _configured:
            return

        # Determine level
        env_level = os.environ.get("GMAIL_MCP_LOG_LEVEL", "").upper()
        if env_level:
            level = env_level
        if isinstance(level, str):
            level = getattr(logging, level, logging.INFO)

        # Determine format
        if json_format is None:
            env_format = os.environ.get("GMAIL_MCP_LOG_FORMAT", "").lower()
            if env_format == "json":
                json_format = True
            elif env_format == "human":
                json_format = False
            else:
                # Auto-detect: use human format in TTY, JSON otherwise
                json_format = not (stream or sys.stderr).isatty()

        # Create handler
        handler = logging.StreamHandler(stream or sys.stderr)
        handler.setLevel(level)

        # Set formatter
        if json_format:
            handler.setFormatter(StructuredFormatter())
        else:
            handler.setFormatter(HumanFormatter())

        # Configure root logger for our packages
        for package in ("gmail_multi_user", "gmail_mcp_server"):
            logger = logging.getLogger(package)
            logger.setLevel(level)
            logger.addHandler(handler)
            logger.propagate = False

        _configured = True


def get_logger(name: str) -> StructuredLoggerAdapter:
    """Get a structured logger for the given name.

    Args:
        name: Logger name (typically __name__).

    Returns:
        StructuredLoggerAdapter that supports keyword arguments.

    Example:
        logger = get_logger(__name__)
        logger.info("Processing request", user_id="user_123", operation="search")
    """
    # Auto-configure with defaults if not already configured
    if not _configured:
        configure_logging()

    return StructuredLoggerAdapter(logging.getLogger(name))


# Convenience re-exports
DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL
