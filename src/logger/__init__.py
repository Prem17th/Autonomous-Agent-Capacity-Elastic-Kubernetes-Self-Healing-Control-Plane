"""Logging package for Aegis Sentinel."""

from src.logger.logger import get_logger, log_event, setup_logging

__all__ = ["setup_logging", "get_logger", "log_event"]
