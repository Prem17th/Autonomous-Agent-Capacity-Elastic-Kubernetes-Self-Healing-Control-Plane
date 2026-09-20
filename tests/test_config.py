"""Unit tests for configuration loading and validation."""

import os
import unittest
from unittest.mock import patch

from src.config.settings import Settings, get_settings
from src.errors.exceptions import ConfigError


class TestConfig(unittest.TestCase):
    """Test suite for Settings."""

    def test_default_settings(self) -> None:
        """Verify default settings instantiation."""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings.from_env()
            self.assertEqual(settings.environment, "development")
            self.assertEqual(settings.log_level, "INFO")
            self.assertEqual(settings.app_name, "aegis-sentinel")
            self.assertEqual(settings.app_version, "0.1.0")
            self.assertEqual(settings.mcp_server_host, "127.0.0.1")
            self.assertEqual(settings.mcp_server_port, 8000)
            self.assertEqual(settings.mcp_transport, "stdio")
            self.assertIsNone(settings.aws_region)
            self.assertIsNone(settings.bedrock_model_id)
            self.assertIsNone(settings.kubernetes_namespace)
            self.assertIsNone(settings.aegis_endpoint)

    def test_environment_overrides(self) -> None:
        """Verify environment variables correctly override defaults."""
        custom_env = {
            "ENVIRONMENT": "production",
            "LOG_LEVEL": "DEBUG",
            "APP_NAME": "custom-sentinel",
            "APP_VERSION": "1.2.3",
            "MCP_SERVER_HOST": "0.0.0.0",
            "MCP_SERVER_PORT": "9000",
            "MCP_TRANSPORT": "http",
            "SENTINEL_API_KEY": "custom-secret-key",
            "AWS_REGION": "us-east-1",
            "BEDROCK_MODEL_ID": "anthropic.claude-3-5-sonnet",
            "KUBERNETES_NAMESPACE": "test-ns",
            "AEGIS_ENDPOINT": "http://aegis.local:8080",
        }
        with patch.dict(os.environ, custom_env, clear=True):
            settings = Settings.from_env()
            self.assertEqual(settings.environment, "production")
            self.assertEqual(settings.log_level, "DEBUG")
            self.assertEqual(settings.app_name, "custom-sentinel")
            self.assertEqual(settings.app_version, "1.2.3")
            self.assertEqual(settings.mcp_server_host, "0.0.0.0")
            self.assertEqual(settings.mcp_server_port, 9000)
            self.assertEqual(settings.mcp_transport, "http")
            self.assertEqual(settings.sentinel_api_key, "custom-secret-key")
            self.assertEqual(settings.aws_region, "us-east-1")
            self.assertEqual(settings.bedrock_model_id, "anthropic.claude-3-5-sonnet")
            self.assertEqual(settings.kubernetes_namespace, "test-ns")
            self.assertEqual(settings.aegis_endpoint, "http://aegis.local:8080")

    def test_invalid_environment_raises_error(self) -> None:
        """Verify invalid environment raises ConfigError."""
        with patch.dict(os.environ, {"ENVIRONMENT": "invalid_env"}, clear=True):
            with self.assertRaises(ConfigError):
                Settings.from_env()

    def test_invalid_log_level_raises_error(self) -> None:
        """Verify invalid log level raises ConfigError."""
        with patch.dict(os.environ, {"LOG_LEVEL": "INVALID_LEVEL"}, clear=True):
            with self.assertRaises(ConfigError):
                Settings.from_env()

    def test_invalid_port_string_raises_error(self) -> None:
        """Verify non-integer port raises ConfigError."""
        with patch.dict(os.environ, {"MCP_SERVER_PORT": "not-a-port"}, clear=True):
            with self.assertRaises(ConfigError):
                Settings.from_env()

    def test_invalid_port_range_raises_error(self) -> None:
        """Verify out-of-range port raises ConfigError."""
        with patch.dict(os.environ, {"MCP_SERVER_PORT": "99999"}, clear=True):
            with self.assertRaises(ConfigError):
                Settings.from_env()

    def test_invalid_transport_raises_error(self) -> None:
        """Verify unsupported MCP transport raises ConfigError."""
        with patch.dict(os.environ, {"MCP_TRANSPORT": "invalid_transport"}, clear=True):
            with self.assertRaises(ConfigError):
                Settings.from_env()

    def test_to_dict_safe_redaction(self) -> None:
        """Verify to_dict(safe=True) produces expected structure."""
        settings = Settings()
        data = settings.to_dict(safe=True)
        self.assertIn("environment", data)
        self.assertEqual(data["environment"], "development")
        self.assertIn("mcp_server_port", data)
        self.assertEqual(data["mcp_server_port"], 8000)


if __name__ == "__main__":
    unittest.main()

