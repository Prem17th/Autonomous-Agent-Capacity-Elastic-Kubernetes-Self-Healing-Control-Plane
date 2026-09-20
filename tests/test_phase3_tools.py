"""Unit and integration tests for Phase 3 MCP tools and recovery workflows."""

import copy
import json
import unittest

from src.autoscaler.policy import RecoveryPolicyEngine
from src.autoscaler.recovery_tracker import recovery_tracker
from src.autoscaler.simulated_provider import SimulatedAutoscalerProvider
from src.config.settings import Settings
from src.errors.exceptions import ValidationError
from src.kubernetes.adapter import KubernetesAdapter
from src.kubernetes.client import MockKubernetesClient
from src.server.mcp_server import MCPServer
from src.tools import (
    handle_diagnose_capacity,
    handle_get_autoscaler_status,
    handle_get_node_pool_status,
    handle_get_recovery_status,
    handle_request_scale_up,
    handle_retry_agent,
    handle_verify_agent_recovery,
    handle_wait_for_capacity,
)
from tests.fixtures.k8s_fixtures import (
    DEPLOYMENT_PENDING,
    DEPLOYMENT_RUNNING,
    EVENTS_LIST,
    NODES_LIST,
    POD_PENDING_CPU,
    POD_RUNNING,
    SAMPLE_AGENT_ID,
    SAMPLE_NAMESPACE,
)


class TestPhase3Tools(unittest.TestCase):
    """Test suite for Phase 3 tools and end-to-end recovery flow."""

    def setUp(self) -> None:
        recovery_tracker.clear()
        self.settings = Settings(environment="test")
        self.client = MockKubernetesClient(
            deployments=copy.deepcopy([DEPLOYMENT_RUNNING, DEPLOYMENT_PENDING]),
            pods=copy.deepcopy([POD_RUNNING, POD_PENDING_CPU]),
            events=copy.deepcopy(EVENTS_LIST),
            nodes=copy.deepcopy(NODES_LIST),
            connected=True,
        )
        self.adapter = KubernetesAdapter(self.client)
        self.provider = SimulatedAutoscalerProvider(
            adapter=self.adapter,
            provision_delay_seconds=0.02,
        )
        self.policy_engine = RecoveryPolicyEngine()
        self.server = MCPServer(
            settings=self.settings,
            adapter=self.adapter,
            autoscaler_provider=self.provider,
            policy_engine=self.policy_engine,
        )

    def test_handle_request_scale_up_success(self) -> None:
        """Verify request_scale_up accepts valid request and returns structured response."""
        res = handle_request_scale_up(
            self.adapter,
            self.provider,
            self.policy_engine,
            {"node_pool": "default", "target_nodes": 1, "agent_id": "test-agent-123"},
        )
        self.assertEqual(res["status"], "ACCEPTED")
        self.assertTrue(res["allowed"])
        self.assertEqual(res["nodes_requested"], 1)
        self.assertEqual(res["node_pool"], "default")

        # Verify recovery record was initiated
        rec = recovery_tracker.get_recovery_by_agent("test-agent-123")
        self.assertIsNotNone(rec)
        self.assertEqual(rec.current_state.value, "SCALE_REQUESTED")

    def test_handle_request_scale_up_dry_run(self) -> None:
        """Verify request_scale_up in dry_run mode performs validation without scaling."""
        res = handle_request_scale_up(
            self.adapter,
            self.provider,
            self.policy_engine,
            {"node_pool": "default", "target_nodes": 1, "dry_run": True},
        )
        self.assertEqual(res["status"], "DRY_RUN_PASSED")
        self.assertTrue(res["dry_run"])

    def test_handle_request_scale_up_policy_denied(self) -> None:
        """Verify request_scale_up returns POLICY_DENIED when limits exceeded."""
        res = handle_request_scale_up(
            self.adapter,
            self.provider,
            self.policy_engine,
            {"node_pool": "default", "target_nodes": 5},  # > max 2
        )
        self.assertEqual(res["status"], "POLICY_DENIED")
        self.assertFalse(res["allowed"])
        self.assertEqual(res["reason"], "MAX_NODES_PER_REQUEST_EXCEEDED")

    def test_handle_wait_for_capacity_success(self) -> None:
        """Verify wait_for_capacity waits and returns ready nodes."""
        scale_res = handle_request_scale_up(
            self.adapter,
            self.provider,
            self.policy_engine,
            {"node_pool": "default", "target_nodes": 1, "agent_id": "test-agent-wait"},
        )
        op_id = scale_res["scale_request_id"]

        wait_res = handle_wait_for_capacity(
            self.provider,
            {"scale_request_id": op_id, "timeout_seconds": 5, "poll_interval_seconds": 0.01, "agent_id": "test-agent-wait"},
        )
        self.assertEqual(wait_res["status"], "READY")
        self.assertGreaterEqual(len(wait_res["provisioned_nodes"]), 1)

        rec = recovery_tracker.get_recovery_by_agent("test-agent-wait")
        self.assertEqual(rec.current_state.value, "CAPACITY_READY")

    def test_handle_get_autoscaler_status(self) -> None:
        """Verify get_autoscaler_status returns provider health."""
        status = handle_get_autoscaler_status(self.provider, {})
        self.assertEqual(status["status"], "HEALTHY")
        self.assertEqual(status["provider"], "simulated")

    def test_handle_get_node_pool_status(self) -> None:
        """Verify get_node_pool_status returns pool metrics."""
        pool_status = handle_get_node_pool_status(self.provider, {"node_pool": "default"})
        self.assertEqual(pool_status["node_pool"], "default")
        self.assertIn("ready_nodes", pool_status)

    def test_handle_get_recovery_status(self) -> None:
        """Verify get_recovery_status returns audit trail."""
        recovery_tracker.start_recovery("agent-rec-test", diagnosis_reason="insufficient_cpu")
        res = handle_get_recovery_status({"agent_id": "agent-rec-test"})
        self.assertTrue(res["found"])
        self.assertEqual(res["recovery"]["agent_id"], "agent-rec-test")
        self.assertEqual(res["recovery"]["diagnosis_reason"], "insufficient_cpu")

    def test_handle_verify_agent_recovery_running(self) -> None:
        """Verify verify_agent_recovery reports recovered=True when deployment has ready replicas."""
        res = handle_verify_agent_recovery(self.adapter, {"agent_id": SAMPLE_AGENT_ID, "namespace": SAMPLE_NAMESPACE})
        self.assertTrue(res["recovered"])
        self.assertEqual(res["status"], "Running")
        self.assertEqual(res["ready_replicas"], 1)

    def test_handle_verify_agent_recovery_pending(self) -> None:
        """Verify verify_agent_recovery reports recovered=False when deployment is pending."""
        res = handle_verify_agent_recovery(self.adapter, {"agent_id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11", "namespace": SAMPLE_NAMESPACE})
        self.assertFalse(res["recovered"])
        self.assertEqual(res["status"], "Pending")
        self.assertEqual(res["ready_replicas"], 0)

    def test_handle_verify_agent_recovery_not_found(self) -> None:
        """Verify verify_agent_recovery reports NotFound when agent deployment missing."""
        res = handle_verify_agent_recovery(self.adapter, {"agent_id": "non-existent-agent-id"})
        self.assertFalse(res["recovered"])
        self.assertEqual(res["status"], "NotFound")

    def test_handle_retry_agent(self) -> None:
        """Verify retry_agent triggers reconciliation response."""
        res = handle_retry_agent(self.adapter, {"agent_id": SAMPLE_AGENT_ID, "namespace": SAMPLE_NAMESPACE})
        self.assertTrue(res["reconciliation_triggered"])
        self.assertEqual(res["method"], "deployment_reconciliation")

    def test_mcp_server_tools_call_phase3(self) -> None:
        """Verify MCP Server executes Phase 3 tools over JSON-RPC."""
        req = {
            "jsonrpc": "2.0",
            "id": 100,
            "method": "tools/call",
            "params": {
                "name": "get_autoscaler_status",
                "arguments": {},
            },
        }
        resp = self.server.handle_request(req)
        self.assertNotIn("error", resp)
        result_text = resp["result"]["content"][0]["text"]
        result_json = json.loads(result_text)
        self.assertEqual(result_json["status"], "HEALTHY")

    def test_full_end_to_end_recovery_flow(self) -> None:
        """
        Verify complete end-to-end recovery sequence:
        1. diagnose_capacity (pending pod -> insufficient_cpu)
        2. request_scale_up (scale-up accepted)
        3. wait_for_capacity (nodes provisioned and ready)
        4. update agent workload state to Running
        5. verify_agent_recovery (confirmed running)
        6. get_recovery_status (confirms audit log state = RUNNING)
        """
        agent_id = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"
        pod_name = "agent-pending-cpu"

        # Step 1: Diagnose Capacity
        diag = handle_diagnose_capacity(self.adapter, {"pod_name": pod_name, "namespace": SAMPLE_NAMESPACE})
        self.assertEqual(diag["classification"], "insufficient_cpu")
        self.assertIn("Scale up", diag["suggested_action"])

        # Track initial recovery
        recovery_tracker.start_recovery(agent_id=agent_id, pod_name=pod_name, diagnosis_reason=diag["classification"])

        # Step 2: Request Scale Up
        scale_res = handle_request_scale_up(
            self.adapter,
            self.provider,
            self.policy_engine,
            {
                "node_pool": "default",
                "target_nodes": 1,
                "reason": diag["classification"],
                "agent_id": agent_id,
            },
        )
        self.assertEqual(scale_res["status"], "ACCEPTED")
        op_id = scale_res["scale_request_id"]

        # Step 3: Wait For Capacity
        wait_res = handle_wait_for_capacity(
            self.provider,
            {
                "scale_request_id": op_id,
                "timeout_seconds": 5,
                "poll_interval_seconds": 0.01,
                "agent_id": agent_id,
            },
        )
        self.assertEqual(wait_res["status"], "READY")

        # Step 4: Simulate Pod & Deployment Scheduled & Running
        dep_dict = self.client.deployments.get(agent_id)
        if dep_dict:
            dep_dict["status"]["readyReplicas"] = 1
            dep_dict["status"]["availableReplicas"] = 1
            dep_dict["status"]["conditions"] = [{"type": "Available", "status": "True"}]

        # Step 5: Verify Agent Recovery
        verify_res = handle_verify_agent_recovery(self.adapter, {"agent_id": agent_id, "namespace": SAMPLE_NAMESPACE})
        self.assertTrue(verify_res["recovered"])
        self.assertEqual(verify_res["status"], "Running")

        # Step 6: Verify Final Recovery State
        rec_status = handle_get_recovery_status({"agent_id": agent_id})
        self.assertTrue(rec_status["found"])
        self.assertEqual(rec_status["recovery"]["current_state"], "RUNNING")
        self.assertIsNotNone(rec_status["recovery"]["resolved_at"])


if __name__ == "__main__":
    unittest.main()

