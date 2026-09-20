"""Unit tests for structured logging and redaction."""

import io
import json
import logging
import unittest

from src.logger.logger import RedactingFormatter, get_logger, log_event, setup_logging


class TestLogging(unittest.TestCase):
    """Test suite for logging configuration and security filters."""

    def test_redacting_formatter_plain_text(self) -> None:
        """Verify redacting formatter redacts sensitive tokens in plain text mode."""
        stream = io.StringIO()
        formatter = RedactingFormatter(json_format=False)
        handler = logging.StreamHandler(stream)
        handler.setFormatter(formatter)

        logger = logging.getLogger("test_plain")
        logger.setLevel(logging.INFO)
        logger.handlers.clear()
        logger.addHandler(handler)

        sensitive_data = {
            "api_key": "secret123",
            "bearer_token": "token456",
            "safe_param": "healthy",
        }
        log_event(logger, logging.INFO, "Event occurred", sensitive_data)

        output = stream.getvalue()
        self.assertIn("Event occurred", output)
        self.assertIn("[REDACTED]", output)
        self.assertNotIn("secret123", output)
        self.assertNotIn("token456", output)
        self.assertIn("healthy", output)

    def test_redacting_formatter_nested_structures(self) -> None:
        """Verify redaction works on nested dictionaries and lists."""
        formatter = RedactingFormatter()
        nested_data = {
            "user_profile": {
                "password": "mypassword",
                "nested_token": "secret_token",
                "username": "alice",
            },
            "credentials": {
                "raw_blob": "hidden",
            },
            "user_list": [
                {"secret_key": "topsecret", "name": "admin"},
                "plain_string",
            ],
            "normal_field": 12345,
        }

        sanitized = formatter.sanitize_dict(nested_data)
        self.assertEqual(sanitized["user_profile"]["password"], "[REDACTED]")
        self.assertEqual(sanitized["user_profile"]["nested_token"], "[REDACTED]")
        self.assertEqual(sanitized["user_profile"]["username"], "alice")
        self.assertEqual(sanitized["credentials"], "[REDACTED]")
        self.assertEqual(sanitized["user_list"][0]["secret_key"], "[REDACTED]")
        self.assertEqual(sanitized["user_list"][0]["name"], "admin")
        self.assertEqual(sanitized["normal_field"], 12345)

    def test_redacting_formatter_json(self) -> None:
        """Verify JSON output format."""
        stream = io.StringIO()
        formatter = RedactingFormatter(json_format=True)
        handler = logging.StreamHandler(stream)
        handler.setFormatter(formatter)

        logger = logging.getLogger("test_json")
        logger.setLevel(logging.INFO)
        logger.handlers.clear()
        logger.addHandler(handler)

        log_event(logger, logging.INFO, "JSON log message", {"token": "secret_abc", "service": "sentinel"})

        output = stream.getvalue().strip()
        parsed = json.loads(output)
        self.assertEqual(parsed["message"], "JSON log message")
        self.assertEqual(parsed["level"], "INFO")
        self.assertEqual(parsed["data"]["token"], "[REDACTED]")
        self.assertEqual(parsed["data"]["service"], "sentinel")

    def test_setup_logging(self) -> None:
        """Verify setup_logging configures root nasiko_sentinel logger."""
        stream = io.StringIO()
        logger = setup_logging(log_level="DEBUG", stream=stream)
        self.assertEqual(logger.level, logging.DEBUG)
        
        child = get_logger("child")
        self.assertEqual(child.name, "nasiko_sentinel.child")


if __name__ == "__main__":
    unittest.main()
