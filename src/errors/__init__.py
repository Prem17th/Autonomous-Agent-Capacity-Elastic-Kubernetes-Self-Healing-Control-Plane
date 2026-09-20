"""Errors module for Aegis Sentinel."""

from src.errors.exceptions import (
    ConfigError,
    ExternalServiceError,
    InfrastructureError,
    InternalError,
    SentinelError,
    TimeoutError,
    ValidationError,
)

__all__ = [
    "SentinelError",
    "ConfigError",
    "ValidationError",
    "InfrastructureError",
    "ExternalServiceError",
    "TimeoutError",
    "InternalError",
]

