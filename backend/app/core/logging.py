"""Structured JSON logging for the AI-Based Text Summarization API.

Configures the root Python logger to emit JSON-formatted records.
Call setup_logging() once at application startup (inside the lifespan handler).
"""

import logging
import json
import sys
from datetime import datetime, timezone

from app.core.config import settings


class _JSONFormatter(logging.Formatter):
    """Emit log records as single-line JSON objects."""

    SENSITIVE_FIELDS = {"password", "hashed_password", "secret_key", "token", "api_key"}

    def format(self, record: logging.LogRecord) -> str:
        message: dict = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Attach any extra fields passed via logger.info("...", extra={...})
        for key, value in record.__dict__.items():
            if key not in {
                "args", "created", "exc_info", "exc_text", "filename",
                "funcName", "levelname", "levelno", "lineno", "message",
                "module", "msecs", "msg", "name", "pathname", "process",
                "processName", "relativeCreated", "stack_info", "thread",
                "threadName",
            } and not key.startswith("_"):
                # Never log sensitive field values
                if key.lower() in self.SENSITIVE_FIELDS:
                    message[key] = "***REDACTED***"
                else:
                    message[key] = value

        if record.exc_info:
            message["exception"] = self.formatException(record.exc_info)

        return json.dumps(message)


def setup_logging() -> None:
    """Configure root logger. Call once at application startup."""
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_JSONFormatter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)

    # Quiet noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("asyncpg").setLevel(logging.WARNING)
