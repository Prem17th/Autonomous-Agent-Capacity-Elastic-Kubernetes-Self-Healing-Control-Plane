"""Error types and central exception handling for Aegis Sentinel."""

from typing import Any, Dict, Optional


class SentinelError(Exception):
    """Base exception class for all Aegis Sentinel errors."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        """Serialize error to dictionary structure."""
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
            }
        }

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(code={self.code!r}, message={self.message!r}, details={self.details!r})"


class ConfigError(SentinelError):
    """Raised when configuration is missing, invalid, or cannot be loaded."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message=message, code="CONFIG_ERROR", details=details)


class ValidationError(SentinelError):
    """Raised when input validation fails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message=message, code="VALIDATION_ERROR", details=details)


class PolicyError(SentinelError):
    """Raised when a recovery or autoscaling safety policy is violated."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message=message, code="POLICY_ERROR", details=details)


class InfrastructureError(SentinelError):
    """Raised when infrastructure operations (Kubernetes, nodes, capacity) fail."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message=message, code="INFRASTRUCTURE_ERROR", details=details)


class ExternalServiceError(SentinelError):
    """Raised when interactions with external services (Aegis API, AWS Bedrock) fail."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message=message, code="EXTERNAL_SERVICE_ERROR", details=details)


class TimeoutError(SentinelError):
    """Raised when an operation or recovery loop times out."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message=message, code="TIMEOUT_ERROR", details=details)


class InternalError(SentinelError):
    """Raised for unexpected internal server errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message=message, code="INTERNAL_ERROR", details=details)
