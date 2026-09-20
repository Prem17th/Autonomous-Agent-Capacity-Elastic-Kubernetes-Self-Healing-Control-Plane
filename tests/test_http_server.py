"""Unit and integration tests for Phase 5 Streamable HTTP transport and authentication."""

import copy
import json
import logging
import unittest
import urllib.error
import urllib.request
from typing import Any, Dict, Optional

from src.autoscaler.policy import RecoveryPolicyEngine
from src.autoscaler.recovery_tracker import recovery_tracker
from src.autoscaler.simulated_provider import SimulatedAutoscalerProvider
from src.bedrock.mock_reasoner import MockBedrockReasoner
from src.bedrock.orchestrator import SentinelRecoveryReasoner
from src.config.settings import Settings
from src.errors.exceptions import ConfigError
from src.kubernetes.adapter import KubernetesAdapter
from src.kubernetes.client import MockKubernetesClient
from src.server.http_server import HttpMCPServer
from src.server.mcp_server import MCPServer
from tests.fixtures.k8s_fixtures import (
    DEPLOYMENT_PENDING,
    DEPLOYMENT_RUNNING,
    EVENTS_LIST,
    NODES_LIST,
    POD_PENDING_CPU,
    POD_PENDING_QUOTA,
    POD_RUNNING,
    SAMPLE_NAMESPACE,
)


class TestHttpServer(unittest.TestCase):
    """Test suite for HttpMCPServer and authentication validation."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.api_key = "sentinel-test-secret-token-12345"
        cls.settings = Settings(
            environment="test",
            mcp_transport="http",
            mcp_http_host="127.0.0.1",
            mcp_http_port=0,  # OS assigned ephemeral port
            sentinel_api_key=cls.api_key,
            bedrock_mock_mode=True,
        )

        recovery_tracker.clear()
        cls.mock_client = MockKubernetesClient(
            deployments=copy.deepcopy([DEPLOYMENT_RUNNING, DEPLOYMENT_PENDING]),
            pods=copy.deepcopy([POD_RUNNING, POD_PENDING_CPU, POD_PENDING_QUOTA]),
            events=copy.deepcopy(EVENTS_LIST),
            nodes=copy.deepcopy(NODES_LIST),
            connected=True,
        )
        cls.adapter = KubernetesAdapter(cls.mock_client)
        cls.provider = SimulatedAutoscalerProvider(adapter=cls.adapter, provision_delay_seconds=0.01)
        cls.policy_engine = RecoveryPolicyEngine()
        cls.mock_reasoner = MockBedrockReasoner()
        cls.orchestrator = SentinelRecoveryReasoner(primary_reasoner=cls.mock_reasoner)

        cls.mcp_server = MCPServer(
            settings=cls.settings,
            adapter=cls.adapter,
            autoscaler_provider=cls.provider,
            policy_engine=cls.policy_engine,
            reasoner=cls.orchestrator,
        )

        cls.http_server = HttpMCPServer(
            settings=cls.settings,
            mcp_server=cls.mcp_server,
            host="127.0.0.1",
            port=0,
            api_key=cls.api_key,
        )
        cls.http_server.start(threaded=True)
        cls.host, cls.port = cls.http_server.server_address
        cls.base_url = f"http://{cls.host}:{cls.port}"

    @classmethod
    def tearDownClass(cls) -> None:
        cls.http_server.stop()

    def _make_http_request(
        self,
        path: str = "/mcp",
        data: Optional[Dict[str, Any]] = None,
        raw_body: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        method: str = "POST",
    ) -> Tuple[int, Dict[str, Any]]:
        """Helper to issue HTTP requests to the test server."""
        url = f"{self.base_url}{path}"
        req_headers = {"Content-Type": "application/json"}
        if headers:
            req_headers.update(headers)

        body_bytes = None
        if raw_body is not None:
            body_bytes = raw_body.encode("utf-8")
        elif data is not None:
            body_bytes = json.dumps(data).encode("utf-8")

        req = urllib.request.Request(url, data=body_bytes, headers=req_headers, method=method)
        try:
            with urllib.request.urlopen(req) as resp:
                resp_body = resp.read().decode("utf-8")
                return resp.status, json.loads(resp_body) if resp_body else {}
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8")
            try:
                parsed = json.loads(err_body)
            except Exception:
                parsed = {"raw": err_body}
            return e.code, parsed

    # 1. HTTP health / startup behavior
    def test_http_health_endpoint(self) -> None:
        """Verify GET /health returns HTTP 200 with service health payload."""
        status, data = self._make_http_request(path="/health", method="GET")
        self.assertEqual(status, 200)
        self.assertEqual(data.get("status"), "ok")
        self.assertEqual(data.get("service"), "nasiko-sentinel")
        self.assertIn("components", data)

    # 2. Valid MCP initialize request
    def test_http_initialize_request(self) -> None:
        """Verify valid MCP initialize request returns server capabilities."""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "dronahq-agent", "version": "1.0"},
            },
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}
        status, data = self._make_http_request(data=payload, headers=headers)
        self.assertEqual(status, 200)
        self.assertEqual(data.get("id"), 1)
        result = data.get("result", {})
        self.assertEqual(result.get("protocolVersion"), "2024-11-05")
        self.assertIn("serverInfo", result)

    # 3. Valid tools/list
    def test_http_tools_list(self) -> None:
        """Verify valid tools/list request returns all 14 registered MCP tools."""
        payload = {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
        headers = {"Authorization": f"Bearer {self.api_key}"}
        status, data = self._make_http_request(data=payload, headers=headers)
        self.assertEqual(status, 200)
        tools = data.get("result", {}).get("tools", [])
        self.assertEqual(len(tools), 14)
        tool_names = {t["name"] for t in tools}
        self.assertIn("diagnose_capacity", tool_names)
        self.assertIn("request_scale_up", tool_names)
        self.assertIn("reason_recovery", tool_names)

    # 4. Valid tools/call
    def test_http_tools_call_diagnose_capacity(self) -> None:
        """Verify valid tools/call over HTTP returns structured tool results."""
        payload = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "diagnose_capacity",
                "arguments": {"pod_name": "agent-pending-cpu", "namespace": SAMPLE_NAMESPACE},
            },
        }
        headers = {"X-Sentinel-API-Key": self.api_key}
        status, data = self._make_http_request(data=payload, headers=headers)
        self.assertEqual(status, 200)
        self.assertEqual(data.get("id"), 3)
        content = data.get("result", {}).get("content", [])
        self.assertTrue(len(content) > 0)
        parsed_result = json.loads(content[0]["text"])
        self.assertEqual(parsed_result["classification"], "insufficient_cpu")

    # 5. Missing authentication
    def test_http_missing_authentication_rejected(self) -> None:
        """Verify requests missing authentication headers return HTTP 401."""
        payload = {"jsonrpc": "2.0", "id": 4, "method": "tools/list"}
        status, data = self._make_http_request(data=payload, headers={})
        self.assertEqual(status, 401)
        self.assertIn("error", data)
        self.assertEqual(data["error"]["code"], -32001)

    # 6. Invalid authentication
    def test_http_invalid_authentication_rejected(self) -> None:
        """Verify invalid API key in Bearer or Header returns HTTP 401."""
        payload = {"jsonrpc": "2.0", "id": 5, "method": "tools/list"}
        headers = {"Authorization": "Bearer invalid-wrong-secret-key"}
        status, data = self._make_http_request(data=payload, headers=headers)
        self.assertEqual(status, 401)

        headers_custom = {"X-Sentinel-API-Key": "completely-wrong-key"}
        status2, data2 = self._make_http_request(data=payload, headers=headers_custom)
        self.assertEqual(status2, 401)

    # 7. Correct authentication with alternative header
    def test_http_x_api_key_header(self) -> None:
        """Verify standard X-API-Key header works as well as Bearer token."""
        payload = {"jsonrpc": "2.0", "id": 6, "method": "ping"}
        headers = {"X-API-Key": self.api_key}
        status, data = self._make_http_request(data=payload, headers=headers)
        self.assertEqual(status, 200)
        self.assertEqual(data.get("id"), 6)

    # 8. Malformed JSON
    def test_http_malformed_json(self) -> None:
        """Verify malformed JSON string returns JSON-RPC Parse Error (-32700)."""
        raw_broken = "{\"jsonrpc\": \"2.0\", \"method\": \"ping\", broken"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        status, data = self._make_http_request(raw_body=raw_broken, headers=headers)
        self.assertEqual(status, 200)
        self.assertIn("error", data)
        self.assertEqual(data["error"]["code"], -32700)

    # 9. Invalid JSON-RPC request
    def test_http_invalid_jsonrpc_request(self) -> None:
        """Verify missing method field returns Invalid Request error (-32600)."""
        payload = {"jsonrpc": "2.0", "id": 7}  # Missing method
        headers = {"Authorization": f"Bearer {self.api_key}"}
        status, data = self._make_http_request(data=payload, headers=headers)
        self.assertEqual(status, 200)
        self.assertEqual(data["error"]["code"], -32600)

    # 10. Unknown method
    def test_http_unknown_method(self) -> None:
        """Verify unknown method returns Method Not Found (-32601)."""
        payload = {"jsonrpc": "2.0", "id": 8, "method": "non_existent_method"}
        headers = {"Authorization": f"Bearer {self.api_key}"}
        status, data = self._make_http_request(data=payload, headers=headers)
        self.assertEqual(status, 200)
        self.assertEqual(data["error"]["code"], -32601)

    # 11. Unknown tool
    def test_http_unknown_tool(self) -> None:
        """Verify unregistered tool call returns Invalid Params (-32602)."""
        payload = {
            "jsonrpc": "2.0",
            "id": 9,
            "method": "tools/call",
            "params": {"name": "unregistered_custom_tool", "arguments": {}},
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}
        status, data = self._make_http_request(data=payload, headers=headers)
        self.assertEqual(status, 200)
        self.assertEqual(data["error"]["code"], -32602)

    # 12. Existing tool validation still works over HTTP
    def test_http_tool_validation_error(self) -> None:
        """Verify tool argument validation failure returns structured validation error."""
        payload = {
            "jsonrpc": "2.0",
            "id": 10,
            "method": "tools/call",
            "params": {
                "name": "get_agent_status",
                "arguments": {},  # Missing required agent_id
            },
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}
        status, data = self._make_http_request(data=payload, headers=headers)
        self.assertEqual(status, 200)
        self.assertEqual(data["error"]["code"], -32602)
        self.assertIn("agent_id", data["error"]["message"].lower())

    # 13. RecoveryPolicyEngine cannot be bypassed over HTTP
    def test_http_policy_engine_enforcement(self) -> None:
        """Verify scaling requests over HTTP are strictly governed by RecoveryPolicyEngine."""
        # Requesting 5 nodes (> max 2 limit)
        payload = {
            "jsonrpc": "2.0",
            "id": 11,
            "method": "tools/call",
            "params": {
                "name": "request_scale_up",
                "arguments": {"node_pool": "default", "target_nodes": 5},
            },
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}
        status, data = self._make_http_request(data=payload, headers=headers)
        self.assertEqual(status, 200)
        content = data.get("result", {}).get("content", [])
        parsed = json.loads(content[0]["text"])
        self.assertEqual(parsed["status"], "POLICY_DENIED")
        self.assertFalse(parsed["allowed"])
        self.assertEqual(parsed["reason"], "MAX_NODES_PER_REQUEST_EXCEEDED")

    # 14. API key never appears in logs/errors
    def test_api_key_not_leaked(self) -> None:
        """Verify API key is never exposed in error responses or safe dict settings."""
        # Check safe dict settings
        safe_dict = self.settings.to_dict(safe=True)
        self.assertEqual(safe_dict["sentinel_api_key"], "[REDACTED]")

        # Issue invalid request and verify key is not in error payload
        payload = {"jsonrpc": "2.0", "id": 12, "method": "invalid"}
        headers = {"Authorization": f"Bearer {self.api_key}"}
        _, data = self._make_http_request(data=payload, headers=headers)
        dumped = json.dumps(data)
        self.assertNotIn(self.api_key, dumped)

    # 15. Server fails safely when API key missing in non-test environment
    def test_http_server_fails_safely_without_key_in_prod(self) -> None:
        """Verify HttpMCPServer raises ConfigError if started in production without SENTINEL_API_KEY."""
        prod_settings = Settings(
            environment="production",
            mcp_transport="http",
            sentinel_api_key=None,
        )
        with self.assertRaises(ConfigError):
            HttpMCPServer(settings=prod_settings, host="127.0.0.1", port=9999, api_key=None)
