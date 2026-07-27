"""Centralized logging configuration.

Provides a single :func:`configure_logging` entry point invoked once at
application startup, plus :func:`get_logger` for consistent, named
loggers throughout the codebase. Supports both human-readable console
output (for local development) and structured JSON output (for staging /
production log aggregation).
"""

from __future__ import annotations

import json
import logging
import logging.config
import sys
from datetime import datetime, timezone
from typing import Any

from app.core.config import get_settings


class JSONLogFormatter(logging.Formatter):
    """Render log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:  # noqa: A003
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        extra_fields = getattr(record, "extra_fields", None)
        if extra_fields:
            payload.update(extra_fields)

        return json.dumps(payload, default=str)


def configure_logging() -> None:
    """Configure root logging handlers and levels for the process.

    Idempotent: safe to call multiple times (e.g. once from ``main.py``
    and once from a test fixture) without duplicating handlers.
    """
    settings = get_settings()

    formatter_key = "json" if settings.LOG_JSON else "console"

    logging_config: dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "console": {
                "format": (
                    "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
                ),
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "json": {
                "()": JSONLogFormatter,
            },
        },
        "handlers": {
            "default": {
                "class": "logging.StreamHandler",
                "formatter": formatter_key,
                "stream": sys.stdout,
            },
        },
        "root": {
            "handlers": ["default"],
            "level": settings.LOG_LEVEL.upper(),
        },
        "loggers": {
            "uvicorn": {"level": settings.LOG_LEVEL.upper(), "propagate": True},
            "uvicorn.error": {"level": settings.LOG_LEVEL.upper(), "propagate": True},
            "uvicorn.access": {"level": settings.LOG_LEVEL.upper(), "propagate": True},
            "sqlalchemy.engine": {
                "level": "INFO" if settings.DB_ECHO_SQL else "WARNING",
                "propagate": True,
            },
        },
    }

    logging.config.dictConfig(logging_config)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger.

    Args:
        name: Typically ``__name__`` of the calling module.

    Returns:
        A standard library :class:`logging.Logger` configured according
        to the application-wide logging setup.
    """
    return logging.getLogger(name)
