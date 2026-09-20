"""Structured logging configuration for Aegis Sentinel."""

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional

SENSITIVE_PATTERNS = (
    "authorization",
    "bearer",
    "token",
    "secret",
    "key",
    "password",
    "credential",
    "aws_secret_access_key",
    "aws_session_token",
)


class RedactingFormatter(logging.Formatter):
    """Logging formatter that sanitizes sensitive data from log records."""

    def __init__(self, json_format: bool = False) -> None:
        super().__init__()
        self.json_format = json_format

    def sanitize_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively redact sensitive key-value pairs."""
        sanitized = {}
        for k, v in data.items():
            k_lower = str(k).lower()
            if any(pattern in k_lower for pattern in SENSITIVE_PATTERNS):
                sanitized[k] = "[REDACTED]"
            elif isinstance(v, dict):
                sanitized[k] = self.sanitize_dict(v)
            elif isinstance(v, list):
                sanitized[k] = [
                    self.sanitize_dict(item) if isinstance(item, dict) else item
                    for item in v
                ]
            else:
                sanitized[k] = v
        return sanitized

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat()
        log_data: Dict[str, Any] = {
            "timestamp": timestamp,
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Include custom extra fields if provided
        if hasattr(record, "event_data") and isinstance(record.event_data, dict):
            log_data["data"] = self.sanitize_dict(record.event_data)

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        if self.json_format:
            return json.dumps(log_data)
        else:
            data_str = f" | {json.dumps(log_data['data'])}" if "data" in log_data else ""
            exc_str = f"\n{log_data['exception']}" if "exception" in log_data else ""
            return f"[{timestamp}] [{record.levelname:<7}] [{record.name}] {record.getMessage()}{data_str}{exc_str}"


def setup_logging(
    log_level: str = "INFO",
    json_format: bool = False,
    stream: Optional[Any] = None,
) -> logging.Logger:
    """Initialize root and application logging."""
    if stream is None:
        stream = sys.stderr

    level = getattr(logging, log_level.upper(), logging.INFO)

    root_logger = logging.getLogger("aegis_sentinel")
    root_logger.setLevel(level)

    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()

    handler = logging.StreamHandler(stream)
    handler.setLevel(level)
    handler.setFormatter(RedactingFormatter(json_format=json_format))
    root_logger.addHandler(handler)

    # Do not propagate to root logger to avoid double logging
    root_logger.propagate = False

    return root_logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a logger within the aegis_sentinel hierarchy."""
    if name:
        return logging.getLogger(f"aegis_sentinel.{name}")
    return logging.getLogger("aegis_sentinel")


def log_event(
    logger: logging.Logger,
    level: int,
    message: str,
    event_data: Optional[Dict[str, Any]] = None,
) -> None:
    """Log an event with structured metadata attached."""
    extra = {"event_data": event_data} if event_data else {}
    logger.log(level, message, extra=extra)
