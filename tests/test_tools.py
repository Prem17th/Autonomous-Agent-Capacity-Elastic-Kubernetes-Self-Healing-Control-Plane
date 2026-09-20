"""Unit tests for Phase 2 MCP observation and diagnosis tools."""

import unittest

from src.errors.exceptions import ValidationError
from src.kubernetes.adapter import KubernetesAdapter
from src.kubernetes.client import MockKubernetesClient
from src.tools.agent_status import handle_get_agent_status
from src.tools.diagnosis import handle_diagnose_capacity
from src.tools.node_capacity import handle_get_node_capacity
from src.tools.pending_pods import handle_get_pending_pods
from src.tools.pod_events import handle_get_pod_events
from tests.fixtures.k8s_fixtures import (
    DEPLOYMENT_PENDING,
    DEPLOYMENT_RUNNING,
    EVENTS_LIST,
    NODES_LIST,
    POD_PENDING_CPU,
    POD_PENDING_MEM,
    POD_PENDING_NODE_POOL,
    POD_PENDING_QUOTA,
    POD_PENDING_TAINT,
    POD_PENDING_TOO_MANY_PODS,
    POD_PENDING_UNKNOWN,
    POD_RUNNING,
    SAMPLE_AGENT_ID,
    SAMPLE_NAMESPACE,
)


class TestTools(unittest.TestCase):
    """Test suite for Phase 2 tool handlers and diagnosis classification."""

    def setUp(self) -> None:
        self.all_pods = [
            POD_RUNNING,
            POD_PENDING_CPU,
            POD_PENDING_MEM,
            POD_PENDING_TOO_MANY_PODS,
            POD_PENDING_QUOTA,
            POD_PENDING_TAINT,
            POD_PENDING_NODE_POOL,
            POD_PENDING_UNKNOWN,
        ]
        self.client = MockKubernetesClient(
            deployments=[DEPLOYMENT_RUNNING, DEPLOYMENT_PENDING],
            pods=self.all_pods,
            events=EVENTS_LIST,
            nodes=NODES_LIST,
            connected=True,
        )
        self.adapter = KubernetesAdapter(self.client)

    # ─── 1. get_agent_status Tool ────────────────────────────────────────────

    def test_handle_get_agent_status_found(self) -> None:
        """Verify get_agent_status returns normalized deployment when found."""
        result = handle_get_agent_status(
            self.adapter,
            {"agent_id": SAMPLE_AGENT_ID, "namespace": SAMPLE_NAMESPACE},
        )
        self.assertTrue(result["found"])
        self.assertEqual(result["agent_id"], SAMPLE_AGENT_ID)
        self.assertEqual(result["deployment"]["status"], "Running")

    def test_handle_get_agent_status_not_found(self) -> None:
        """Verify get_agent_status returns found=False when deployment missing."""
        result = handle_get_agent_status(
            self.adapter,
            {"agent_id": "non-existent-uuid", "namespace": SAMPLE_NAMESPACE},
        )
        self.assertFalse(result["found"])
        self.assertIn("No active deployment found", result["message"])

    def test_handle_get_agent_status_validation_error(self) -> None:
        """Verify missing agent_id raises ValidationError."""
        with self.assertRaises(ValidationError):
            handle_get_agent_status(self.adapter, {})

    # ─── 2. get_pending_pods Tool ───────────────────────────────────────────

    def test_handle_get_pending_pods(self) -> None:
        """Verify get_pending_pods returns all unscheduled/pending pods."""
        result = handle_get_pending_pods(self.adapter, {"namespace": SAMPLE_NAMESPACE})
        self.assertEqual(result["count"], 7)
        pod_names = [p["pod_name"] for p in result["pending_pods"]]
        self.assertIn("agent-pending-cpu", pod_names)
        self.assertIn("agent-pending-mem", pod_names)
        self.assertNotIn(POD_RUNNING["metadata"]["name"], pod_names)

    # ─── 3. get_pod_events Tool ─────────────────────────────────────────────

    def test_handle_get_pod_events(self) -> None:
        """Verify get_pod_events returns normalized events."""
        result = handle_get_pod_events(
            self.adapter,
            {"pod_name": "agent-pending-cpu", "namespace": SAMPLE_NAMESPACE},
        )
        self.assertEqual(result["pod_name"], "agent-pending-cpu")
        self.assertEqual(result["failed_scheduling_count"], 1)
        self.assertIn("Insufficient cpu", result["events"][0]["message"])

    def test_handle_get_pod_events_validation_error(self) -> None:
        """Verify missing pod_name raises ValidationError."""
        with self.assertRaises(ValidationError):
            handle_get_pod_events(self.adapter, {})

    # ─── 4. get_node_capacity Tool ──────────────────────────────────────────

    def test_handle_get_node_capacity(self) -> None:
        """Verify get_node_capacity returns cluster capacity summary."""
        result = handle_get_node_capacity(self.adapter, {})
        self.assertEqual(result["total_nodes"], 2)
        self.assertEqual(result["ready_nodes"], 2)
        self.assertEqual(result["total_allocatable_cpu_milli"], 3860)
        self.assertIn("nodes", result)
        self.assertEqual(len(result["nodes"]), 2)

    # ─── 5. diagnose_capacity Tool & Classifications ────────────────────────

    def test_diagnose_insufficient_cpu(self) -> None:
        """Verify deterministic classification of insufficient_cpu."""
        diag = handle_diagnose_capacity(
            self.adapter,
            {"pod_name": "agent-pending-cpu", "namespace": SAMPLE_NAMESPACE},
        )
        self.assertEqual(diag["classification"], "insufficient_cpu")
        self.assertEqual(diag["reason"], "InsufficientCPU")
        self.assertIn("insufficient CPU capacity", diag["message"])

    def test_diagnose_insufficient_memory(self) -> None:
        """Verify deterministic classification of insufficient_memory."""
        diag = handle_diagnose_capacity(
            self.adapter,
            {"pod_name": "agent-pending-mem", "namespace": SAMPLE_NAMESPACE},
        )
        self.assertEqual(diag["classification"], "insufficient_memory")
        self.assertEqual(diag["reason"], "InsufficientMemory")
        self.assertIn("insufficient memory capacity", diag["message"])

    def test_diagnose_too_many_pods(self) -> None:
        """Verify deterministic classification of too_many_pods."""
        diag = handle_diagnose_capacity(
            self.adapter,
            {"pod_name": "agent-pending-pods-limit", "namespace": SAMPLE_NAMESPACE},
        )
        self.assertEqual(diag["classification"], "too_many_pods")
        self.assertEqual(diag["reason"], "TooManyPods")

    def test_diagnose_resource_quota(self) -> None:
        """Verify deterministic classification of resource_quota."""
        diag = handle_diagnose_capacity(
            self.adapter,
            {"pod_name": "agent-pending-quota", "namespace": SAMPLE_NAMESPACE},
        )
        self.assertEqual(diag["classification"], "resource_quota")
        self.assertEqual(diag["reason"], "ResourceQuotaExceeded")

    def test_diagnose_taint_or_constraint(self) -> None:
        """Verify deterministic classification of taint_or_constraint."""
        diag = handle_diagnose_capacity(
            self.adapter,
            {"pod_name": "agent-pending-taint", "namespace": SAMPLE_NAMESPACE},
        )
        self.assertEqual(diag["classification"], "taint_or_constraint")
        self.assertEqual(diag["reason"], "UntoleratedTaint")

    def test_diagnose_node_pool_constraint(self) -> None:
        """Verify deterministic classification of node_pool_constraint."""
        diag = handle_diagnose_capacity(
            self.adapter,
            {"pod_name": "agent-pending-nodepool", "namespace": SAMPLE_NAMESPACE},
        )
        self.assertEqual(diag["classification"], "node_pool_constraint")
        self.assertEqual(diag["reason"], "NodeSelectorMismatch")

    def test_diagnose_unknown(self) -> None:
        """Verify fallback classification to unknown when no recognized pattern matches."""
        diag = handle_diagnose_capacity(
            self.adapter,
            {"pod_name": "agent-pending-unknown", "namespace": SAMPLE_NAMESPACE},
        )
        self.assertEqual(diag["classification"], "unknown")
        self.assertEqual(diag["reason"], "UnclassifiedSchedulingDelay")

    def test_diagnose_already_running_pod(self) -> None:
        """Verify diagnosing a running pod returns non-failure note."""
        running_pod_name = POD_RUNNING["metadata"]["name"]
        diag = handle_diagnose_capacity(
            self.adapter,
            {"pod_name": running_pod_name, "namespace": SAMPLE_NAMESPACE},
        )
        self.assertEqual(diag["classification"], "unknown")
        self.assertEqual(diag["reason"], "PodAlreadyScheduled")
        self.assertIn("already scheduled and running", diag["message"])

    def test_diagnose_pod_not_found(self) -> None:
        """Verify non-existent pod raises ValidationError."""
        with self.assertRaises(ValidationError):
            handle_diagnose_capacity(
                self.adapter,
                {"pod_name": "ghost-pod", "namespace": SAMPLE_NAMESPACE},
            )


if __name__ == "__main__":
    unittest.main()

