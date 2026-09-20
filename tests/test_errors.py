"""Unit tests for exception hierarchy and error handling."""

import unittest

from src.errors.exceptions import (
    ConfigError,
    ExternalServiceError,
    InfrastructureError,
    InternalError,
    PolicyError,
    SentinelError,
    TimeoutError,
    ValidationError,
)


class TestErrors(unittest.TestCase):
    """Test suite for Sentinel error classes."""

    def test_base_sentinel_error(self) -> None:
        """Verify SentinelError properties and serialization."""
        err = SentinelError("Something broke", code="CUSTOM_CODE", details={"key": "val"})
        self.assertEqual(err.message, "Something broke")
        self.assertEqual(err.code, "CUSTOM_CODE")
        self.assertEqual(err.details, {"key": "val"})

        err_dict = err.to_dict()
        self.assertEqual(
            err_dict,
            {
                "error": {
                    "code": "CUSTOM_CODE",
                    "message": "Something broke",
                    "details": {"key": "val"},
                }
            },
        )

    def test_subclass_codes_and_defaults(self) -> None:
        """Verify all error subclasses inherit correctly and have proper error codes."""
        test_cases = [
            (ConfigError("Config missing", {"file": ".env"}), "CONFIG_ERROR"),
            (ValidationError("Bad input", {"field": "port"}), "VALIDATION_ERROR"),
            (PolicyError("Scale request denied by policy", {"rule": "cooldown"}), "POLICY_ERROR"),
            (InfrastructureError("K8s node failed", {"node": "node-1"}), "INFRASTRUCTURE_ERROR"),
            (ExternalServiceError("Bedrock timeout", {"service": "bedrock"}), "EXTERNAL_SERVICE_ERROR"),
            (TimeoutError("Scale up timed out", {"timeout": 300}), "TIMEOUT_ERROR"),
            (InternalError("Unexpected crash"), "INTERNAL_ERROR"),
        ]

        for err_instance, expected_code in test_cases:
            with self.subTest(err=err_instance.__class__.__name__):
                self.assertIsInstance(err_instance, SentinelError)
                self.assertEqual(err_instance.code, expected_code)
                self.assertEqual(err_instance.to_dict()["error"]["code"], expected_code)


if __name__ == "__main__":
    unittest.main()
