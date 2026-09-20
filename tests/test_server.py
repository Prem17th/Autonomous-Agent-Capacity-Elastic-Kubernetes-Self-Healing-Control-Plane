"""Unit tests for MCP server protocol, tools dispatching, and health check."""

import json
import unittest

from src.config.settings import Settings
from src.kubernetes.adapter import KubernetesAdapter
from src.kubernetes.client import MockKubernetesClient
from src.server.health import get_health_status
from src.server.mcp_server import (
    INTERNAL_ERROR,
    INVALID_PARAMS,
    INVALID_REQUEST,
    METHOD_NOT_FOUND,
    MCPServer,
)
from tests.fixtures.k8s_fixtures import (
    DEPLOYMENT_RUNNING,
    EVENTS_LIST,
    NODES_LIST,
    POD_PENDING_CPU,
    POD_RUNNING,
    SAMPLE_AGENT_ID,
    SAMPLE_NAMESPACE,
)


class TestMCPServer(unittest.TestCase):
    """Test suite for MCPServer protocol and dispatching."""

    def setUp(self) -> None:
        self.settings = Settings()
        self.client = MockKubernetesClient(
            deployments=[DEPLOYMENT_RUNNING],
            pods=[POD_RUNNING, POD_PENDING_CPU],
            events=EVENTS_LIST,
            nodes=NODES_LIST,
            connected=True,
        )
        self.adapter = KubernetesAdapter(self.client)
        self.server = MCPServer(self.settings, adapter=self.adapter)

    def test_health_status_structure(self) -> None:
        """Verify health check response contents and dependency separation."""
        status = get_health_status(self.settings, k8s_connected=True)
        self.assertEqual(status["status"], "ok")
        self.assertEqual(status["service"], "aegis-sentinel")
        self.assertEqual(status["version"], "0.1.0")
        self.assertEqual(status["environment"], "development")
        self.assertEqual(status["phase"], 4)
        self.assertIn("components", status)
        self.assertEqual(status["components"]["config"], "ready")
        self.assertEqual(status["components"]["mcp_server_foundation"], "ready")
        self.assertEqual(status["components"]["deterministic_diagnosis"], "ready")
        self.assertEqual(status["components"]["controlled_autoscaling"], "ready")
        self.assertEqual(status["components"]["bedrock_reasoning"], "ready")
        # External dependencies separation
        self.assertIn("dependencies", status)
        self.assertEqual(status["dependencies"]["kubernetes"]["status"], "connected")
        self.assertEqual(status["dependencies"]["autoscaler"]["status"], "ready")
        self.assertEqual(status["dependencies"]["bedrock"]["status"], "ready")
        # Roadmap alignment
        self.assertEqual(status["roadmap"]["phase_3"], "controlled_autoscaling (completed)")
        self.assertEqual(status["roadmap"]["phase_4"], "bedrock_reasoning (completed)")

    def test_health_status_disconnected_k8s(self) -> None:
        """Verify Sentinel service remains status=ok even when Kubernetes is unreachable."""
        status = get_health_status(self.settings, k8s_connected=False)
        self.assertEqual(status["status"], "ok")
        self.assertEqual(status["dependencies"]["kubernetes"]["status"], "unreachable")
        self.assertIn("Live Kubernetes integration is implemented but has not yet been validated", status["dependencies"]["kubernetes"]["detail"])

    def test_mcp_initialize(self) -> None:
        """Verify MCP initialize method."""
        req = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0"},
            },
        }
        res = self.server.handle_request(req)
        self.assertIsNotNone(res)
        self.assertEqual(res["jsonrpc"], "2.0")
        self.assertEqual(res["id"], 1)
        self.assertIn("result", res)
        self.assertEqual(res["result"]["serverInfo"]["name"], "aegis-sentinel")
        self.assertEqual(res["result"]["serverInfo"]["version"], "0.1.0")
        self.assertIn("tools", res["result"]["capabilities"])

    def test_mcp_ping(self) -> None:
        """Verify MCP ping method."""
        req = {"jsonrpc": "2.0", "id": "req-ping-1", "method": "ping"}
        res = self.server.handle_request(req)
        self.assertIsNotNone(res)
        self.assertEqual(res["id"], "req-ping-1")
        self.assertEqual(res["result"], {})

    def test_mcp_tools_list(self) -> None:
        """Verify MCP tools/list returns registered tools."""
        req = {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
        res = self.server.handle_request(req)
        self.assertIsNotNone(res)
        tools = res["result"]["tools"]
        tool_names = [t["name"] for t in tools]

        # Phase 2 observation tools
        self.assertIn("get_health", tool_names)
        self.assertIn("get_agent_status", tool_names)
        self.assertIn("get_pending_pods", tool_names)
        self.assertIn("get_pod_events", tool_names)
        self.assertIn("get_node_capacity", tool_names)
        self.assertIn("diagnose_capacity", tool_names)

        # Phase 3 autoscaling & recovery tools
        self.assertIn("request_scale_up", tool_names)
        self.assertIn("wait_for_capacity", tool_names)
        self.assertIn("get_autoscaler_status", tool_names)
        self.assertIn("get_node_pool_status", tool_names)
        self.assertIn("get_recovery_status", tool_names)
        self.assertIn("verify_agent_recovery", tool_names)
        self.assertIn("retry_agent", tool_names)

        # Phase 4 AI reasoning tool
        self.assertIn("reason_recovery", tool_names)

    def test_mcp_tools_call_health(self) -> None:
        """Verify executing get_health via tools/call."""
        req = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "get_health", "arguments": {}},
        }
        res = self.server.handle_request(req)
        self.assertIsNotNone(res)
        self.assertIn("content", res["result"])
        text_content = res["result"]["content"][0]["text"]
        payload = json.loads(text_content)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["phase"], 4)

    def test_mcp_tools_call_get_agent_status(self) -> None:
        """Verify executing get_agent_status via MCP tools/call."""
        req = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "get_agent_status",
                "arguments": {"agent_id": SAMPLE_AGENT_ID, "namespace": SAMPLE_NAMESPACE},
            },
        }
        res = self.server.handle_request(req)
        self.assertIsNotNone(res)
        payload = json.loads(res["result"]["content"][0]["text"])
        self.assertTrue(payload["found"])
        self.assertEqual(payload["agent_id"], SAMPLE_AGENT_ID)
        self.assertEqual(payload["deployment"]["status"], "Running")

    def test_mcp_tools_call_get_pending_pods(self) -> None:
        """Verify executing get_pending_pods via MCP tools/call."""
        req = {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {
                "name": "get_pending_pods",
                "arguments": {"namespace": SAMPLE_NAMESPACE},
            },
        }
        res = self.server.handle_request(req)
        self.assertIsNotNone(res)
        payload = json.loads(res["result"]["content"][0]["text"])
        self.assertEqual(payload["count"], 1)
        self.assertEqual(payload["pending_pods"][0]["pod_name"], "agent-pending-cpu")

    def test_mcp_tools_call_diagnose_capacity(self) -> None:
        """Verify executing diagnose_capacity via MCP tools/call."""
        req = {
            "jsonrpc": "2.0",
            "id": 6,
            "method": "tools/call",
            "params": {
                "name": "diagnose_capacity",
                "arguments": {"pod_name": "agent-pending-cpu", "namespace": SAMPLE_NAMESPACE},
            },
        }
        res = self.server.handle_request(req)
        self.assertIsNotNone(res)
        payload = json.loads(res["result"]["content"][0]["text"])
        self.assertEqual(payload["classification"], "insufficient_cpu")
        self.assertEqual(payload["reason"], "InsufficientCPU")

    def test_mcp_tools_call_request_scale_up(self) -> None:
        """Verify executing request_scale_up via MCP tools/call."""
        req = {
            "jsonrpc": "2.0",
            "id": 7,
            "method": "tools/call",
            "params": {
                "name": "request_scale_up",
                "arguments": {"node_pool": "default", "target_nodes": 1},
            },
        }
        res = self.server.handle_request(req)
        self.assertIsNotNone(res)
        payload = json.loads(res["result"]["content"][0]["text"])
        self.assertEqual(payload["status"], "ACCEPTED")
        self.assertTrue(payload["allowed"])
        self.assertEqual(payload["nodes_requested"], 1)

    def test_mcp_unknown_method_error(self) -> None:
        """Verify unknown method returns METHOD_NOT_FOUND error."""
        req = {"jsonrpc": "2.0", "id": 8, "method": "non_existent_method"}
        res = self.server.handle_request(req)
        self.assertIsNotNone(res)
        self.assertEqual(res["error"]["code"], METHOD_NOT_FOUND)

    def test_mcp_unknown_tool_error(self) -> None:
        """Verify calling unregistered tool returns INVALID_PARAMS error."""
        req = {
            "jsonrpc": "2.0",
            "id": 9,
            "method": "tools/call",
            "params": {"name": "unregistered_tool"},
        }
        res = self.server.handle_request(req)
        self.assertIsNotNone(res)
        self.assertEqual(res["error"]["code"], INVALID_PARAMS)

    def test_mcp_invalid_request(self) -> None:
        """Verify invalid payload returns INVALID_REQUEST error."""
        res = self.server.handle_request("not-a-dict")  # type: ignore
        self.assertIsNotNone(res)
        self.assertEqual(res["error"]["code"], INVALID_REQUEST)


if __name__ == "__main__":
    unittest.main()
