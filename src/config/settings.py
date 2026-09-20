"""Configuration management for Aegis Sentinel."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, Set

from src.errors.exceptions import ConfigError

VALID_ENVIRONMENTS: Set[str] = {"development", "staging", "production", "test"}
VALID_LOG_LEVELS: Set[str] = {"DEBUG", "INFO", "WARNING", "WARN", "ERROR", "CRITICAL"}
VALID_MCP_TRANSPORTS: Set[str] = {"stdio", "sse", "http"}

SENSITIVE_KEY_SUBSTRINGS: Set[str] = {
    "SECRET",
    "KEY",
    "TOKEN",
    "PASSWORD",
    "AUTH",
    "CREDENTIAL",
    "BEARER",
}


def load_dotenv(dotenv_path: Optional[Path] = None) -> None:
    """Parse a simple .env file and set environment variables if not already set."""
    if dotenv_path is None:
        dotenv_path = Path(".env")

    if not dotenv_path.is_file():
        return

    try:
        with open(dotenv_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, _, val = line.partition("=")
                    key = key.strip()
                    val = val.strip().strip("'\"")
                    if key and key not in os.environ:
                        os.environ[key] = val
    except Exception as e:
        raise ConfigError(f"Failed to load .env file from {dotenv_path}: {e}") from e


@dataclass(frozen=True)
class Settings:
    """Application runtime configuration."""

    environment: str = "development"
    log_level: str = "INFO"
    app_name: str = "aegis-sentinel"
    app_version: str = "0.1.0"
    mcp_server_host: str = "127.0.0.1"
    mcp_server_port: int = 8000
    mcp_transport: str = "stdio"

    # HTTP Network Transport Configuration
    mcp_http_host: str = "127.0.0.1"
    mcp_http_port: int = 8000
    sentinel_api_key: Optional[str] = None

    # AWS & Bedrock Configuration
    aws_region: Optional[str] = None
    bedrock_model_id: Optional[str] = None
    bedrock_max_tokens: int = 1024
    bedrock_temperature: float = 0.0
    bedrock_timeout_seconds: int = 15
    bedrock_mock_mode: bool = True

    # Kubernetes & Aegis Endpoints
    kubernetes_namespace: Optional[str] = None
    aegis_endpoint: Optional[str] = None

    def validate(self) -> None:
        """Validate configuration settings."""
        if self.environment.lower() not in VALID_ENVIRONMENTS:
            raise ConfigError(
                f"Invalid ENVIRONMENT '{self.environment}'. Must be one of: {sorted(VALID_ENVIRONMENTS)}",
                details={"environment": self.environment},
            )

        log_level_upper = self.log_level.upper()
        if log_level_upper not in VALID_LOG_LEVELS:
            raise ConfigError(
                f"Invalid LOG_LEVEL '{self.log_level}'. Must be one of: {sorted(VALID_LOG_LEVELS)}",
                details={"log_level": self.log_level},
            )

        if not (1 <= self.mcp_server_port <= 65535):
            raise ConfigError(
                f"Invalid MCP_SERVER_PORT {self.mcp_server_port}. Must be between 1 and 65535",
                details={"mcp_server_port": self.mcp_server_port},
            )

        if self.mcp_transport.lower() not in VALID_MCP_TRANSPORTS:
            raise ConfigError(
                f"Invalid MCP_TRANSPORT '{self.mcp_transport}'. Must be one of: {sorted(VALID_MCP_TRANSPORTS)}",
                details={"mcp_transport": self.mcp_transport},
            )

        if not (1 <= self.mcp_http_port <= 65535):
            raise ConfigError(
                f"Invalid MCP_HTTP_PORT {self.mcp_http_port}. Must be between 1 and 65535",
                details={"mcp_http_port": self.mcp_http_port},
            )

        if self.mcp_transport == "http" and self.environment != "test":
            if not self.sentinel_api_key:
                raise ConfigError(
                    "SENTINEL_API_KEY is required when MCP_TRANSPORT is set to 'http' outside test environment",
                    details={"mcp_transport": self.mcp_transport, "environment": self.environment},
                )

        if self.bedrock_max_tokens <= 0:
            raise ConfigError(
                f"Invalid BEDROCK_MAX_TOKENS {self.bedrock_max_tokens}. Must be greater than 0",
                details={"bedrock_max_tokens": self.bedrock_max_tokens},
            )

        if not (0.0 <= self.bedrock_temperature <= 1.0):
            raise ConfigError(
                f"Invalid BEDROCK_TEMPERATURE {self.bedrock_temperature}. Must be between 0.0 and 1.0",
                details={"bedrock_temperature": self.bedrock_temperature},
            )

        if self.bedrock_timeout_seconds <= 0:
            raise ConfigError(
                f"Invalid BEDROCK_TIMEOUT_SECONDS {self.bedrock_timeout_seconds}. Must be greater than 0",
                details={"bedrock_timeout_seconds": self.bedrock_timeout_seconds},
            )

    @classmethod
    def from_env(cls, dotenv_path: Optional[Path] = None) -> "Settings":
        """Load settings from environment variables and optional .env file."""
        load_dotenv(dotenv_path)

        environment = os.getenv("ENVIRONMENT", "development").strip().lower()
        log_level = os.getenv("LOG_LEVEL", "INFO").strip().upper()
        if log_level == "WARN":
            log_level = "WARNING"
        app_name = os.getenv("APP_NAME", "aegis-sentinel").strip()
        app_version = os.getenv("APP_VERSION", "0.1.0").strip()
        mcp_server_host = os.getenv("MCP_SERVER_HOST", "127.0.0.1").strip()
        
        raw_port = os.getenv("MCP_SERVER_PORT", "8000").strip()
        try:
            mcp_server_port = int(raw_port)
        except ValueError as e:
            raise ConfigError(
                f"MCP_SERVER_PORT must be an integer, got '{raw_port}'",
                details={"raw_port": raw_port},
            ) from e

        mcp_http_host = os.getenv("MCP_HTTP_HOST", mcp_server_host).strip()
        raw_http_port = os.getenv("MCP_HTTP_PORT", str(mcp_server_port)).strip()
        try:
            mcp_http_port = int(raw_http_port)
        except ValueError as e:
            raise ConfigError(
                f"MCP_HTTP_PORT must be an integer, got '{raw_http_port}'",
                details={"raw_http_port": raw_http_port},
            ) from e

        sentinel_api_key = os.getenv("SENTINEL_API_KEY")

        mcp_transport = os.getenv("MCP_TRANSPORT", "stdio").strip().lower()

        aws_region = os.getenv("AWS_REGION")
        bedrock_model_id = os.getenv("BEDROCK_MODEL_ID")

        raw_max_tokens = os.getenv("BEDROCK_MAX_TOKENS", "1024").strip()
        try:
            bedrock_max_tokens = int(raw_max_tokens)
        except ValueError as e:
            raise ConfigError(
                f"BEDROCK_MAX_TOKENS must be an integer, got '{raw_max_tokens}'",
                details={"raw_max_tokens": raw_max_tokens},
            ) from e

        raw_temp = os.getenv("BEDROCK_TEMPERATURE", "0.0").strip()
        try:
            bedrock_temperature = float(raw_temp)
        except ValueError as e:
            raise ConfigError(
                f"BEDROCK_TEMPERATURE must be a float, got '{raw_temp}'",
                details={"raw_temp": raw_temp},
            ) from e

        raw_timeout = os.getenv("BEDROCK_TIMEOUT_SECONDS", "15").strip()
        try:
            bedrock_timeout_seconds = int(raw_timeout)
        except ValueError as e:
            raise ConfigError(
                f"BEDROCK_TIMEOUT_SECONDS must be an integer, got '{raw_timeout}'",
                details={"raw_timeout": raw_timeout},
            ) from e

        raw_mock = os.getenv("BEDROCK_MOCK_MODE", "true").strip().lower()
        bedrock_mock_mode = raw_mock in {"true", "1", "yes", "on"}

        kubernetes_namespace = os.getenv("KUBERNETES_NAMESPACE")
        aegis_endpoint = os.getenv("AEGIS_ENDPOINT")

        settings = cls(
            environment=environment,
            log_level=log_level,
            app_name=app_name,
            app_version=app_version,
            mcp_server_host=mcp_server_host,
            mcp_server_port=mcp_server_port,
            mcp_transport=mcp_transport,
            mcp_http_host=mcp_http_host,
            mcp_http_port=mcp_http_port,
            sentinel_api_key=sentinel_api_key.strip() if sentinel_api_key else None,
            aws_region=aws_region.strip() if aws_region else None,
            bedrock_model_id=bedrock_model_id.strip() if bedrock_model_id else None,
            bedrock_max_tokens=bedrock_max_tokens,
            bedrock_temperature=bedrock_temperature,
            bedrock_timeout_seconds=bedrock_timeout_seconds,
            bedrock_mock_mode=bedrock_mock_mode,
            kubernetes_namespace=kubernetes_namespace.strip() if kubernetes_namespace else None,
            aegis_endpoint=aegis_endpoint.strip() if aegis_endpoint else None,
        )
        settings.validate()
        return settings

    def to_dict(self, safe: bool = True) -> Dict[str, Any]:
        """Convert settings to dictionary, redacting sensitive keys when safe=True."""
        data: Dict[str, Any] = {
            "environment": self.environment,
            "log_level": self.log_level,
            "app_name": self.app_name,
            "app_version": self.app_version,
            "mcp_server_host": self.mcp_server_host,
            "mcp_server_port": self.mcp_server_port,
            "mcp_transport": self.mcp_transport,
            "mcp_http_host": self.mcp_http_host,
            "mcp_http_port": self.mcp_http_port,
            "sentinel_api_key": self.sentinel_api_key,
            "aws_region": self.aws_region,
            "bedrock_model_id": self.bedrock_model_id,
            "bedrock_max_tokens": self.bedrock_max_tokens,
            "bedrock_temperature": self.bedrock_temperature,
            "bedrock_timeout_seconds": self.bedrock_timeout_seconds,
            "bedrock_mock_mode": self.bedrock_mock_mode,
            "kubernetes_namespace": self.kubernetes_namespace,
            "aegis_endpoint": self.aegis_endpoint,
        }
        if safe:
            # Redact any potentially sensitive keys
            for k in list(data.keys()):
                upper_key = k.upper()
                if any(secret in upper_key for secret in SENSITIVE_KEY_SUBSTRINGS):
                    if data[k] is not None:
                        data[k] = "[REDACTED]"
        return data


def get_settings() -> Settings:
    """Convenience singleton-like loader for settings."""
    return Settings.from_env()

