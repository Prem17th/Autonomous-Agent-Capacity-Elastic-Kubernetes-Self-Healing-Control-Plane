"""Unit tests for KubernetesAdapter and Models."""

import unittest

from src.errors.exceptions import InfrastructureError, ValidationError
from src.kubernetes.adapter import KubernetesAdapter
from src.kubernetes.client import MockKubernetesClient
from src.kubernetes.models import parse_cpu_milli, parse_memory_bytes
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


class TestKubernetesAdapter(unittest.TestCase):
    """Test suite for Kubernetes adapter and normalization logic."""

    def setUp(self) -> None:
        self.client = MockKubernetesClient(
            deployments=[DEPLOYMENT_RUNNING, DEPLOYMENT_PENDING],
            pods=[POD_RUNNING, POD_PENDING_CPU],
            events=EVENTS_LIST,
            nodes=NODES_LIST,
            connected=True,
        )
        self.adapter = KubernetesAdapter(self.client)

    def test_parse_cpu_milli(self) -> None:
        """Verify CPU parsing from various string formats."""
        self.assertEqual(parse_cpu_milli("500m"), 500)
        self.assertEqual(parse_cpu_milli("2"), 2000)
        self.assertEqual(parse_cpu_milli("0.5"), 500)
        self.assertEqual(parse_cpu_milli(""), 0)
        self.assertEqual(parse_cpu_milli(None), 0)

    def test_parse_memory_bytes(self) -> None:
        """Verify memory parsing with Ki, Mi, Gi suffixes and bare integers."""
        self.assertEqual(parse_memory_bytes("512Mi"), 512 * 1024 * 1024)
        self.assertEqual(parse_memory_bytes("1Gi"), 1024 * 1024 * 1024)
        self.assertEqual(parse_memory_bytes("1024Ki"), 1024 * 1024)
        self.assertEqual(parse_memory_bytes("1048576"), 1048576)
        self.assertEqual(parse_memory_bytes(None), 0)

    def test_get_agent_status_exists(self) -> None:
        """Verify querying existing agent deployment."""
        status = self.adapter.get_agent_status(agent_id=SAMPLE_AGENT_ID, namespace=SAMPLE_NAMESPACE)
        self.assertIsNotNone(status)
        self.assertEqual(status.deployment_name, SAMPLE_AGENT_ID)
        self.assertEqual(status.replicas, 1)
        self.assertEqual(status.ready_replicas, 1)
        self.assertEqual(status.status, "Running")

    def test_get_agent_status_pending(self) -> None:
        """Verify querying pending agent deployment."""
        pending_id = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"
        status = self.adapter.get_agent_status(agent_id=pending_id, namespace=SAMPLE_NAMESPACE)
        self.assertIsNotNone(status)
        self.assertEqual(status.ready_replicas, 0)
        self.assertEqual(status.status, "Pending")

    def test_get_agent_status_not_found(self) -> None:
        """Verify querying non-existent agent returns None."""
        status = self.adapter.get_agent_status(agent_id="non-existent-uuid", namespace=SAMPLE_NAMESPACE)
        self.assertIsNone(status)

    def test_get_agent_status_invalid_param(self) -> None:
        """Verify empty agent_id raises ValidationError."""
        with self.assertRaises(ValidationError):
            self.adapter.get_agent_status(agent_id="", namespace=SAMPLE_NAMESPACE)

    def test_get_pending_pods(self) -> None:
        """Verify get_pending_pods filters only unscheduled/pending pods."""
        pending = self.adapter.get_pending_pods(namespace=SAMPLE_NAMESPACE)
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0].pod_name, "agent-pending-cpu")
        self.assertEqual(pending[0].phase, "Pending")
        self.assertFalse(pending[0].scheduled)
        self.assertEqual(pending[0].resource_requests.cpu_milli, 2000)

    def test_get_pod_events(self) -> None:
        """Verify retrieving events for a specific pod."""
        events = self.adapter.get_pod_events(pod_name="agent-pending-cpu", namespace=SAMPLE_NAMESPACE)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].reason, "FailedScheduling")
        self.assertIn("Insufficient cpu", events[0].message)

    def test_get_node_capacity(self) -> None:
        """Verify node capacity calculations and available headroom."""
        summary = self.adapter.get_node_capacity()
        self.assertEqual(summary.total_nodes, 2)
        self.assertEqual(summary.ready_nodes, 2)
        # 1930m * 2 = 3860m allocatable
        self.assertEqual(summary.total_allocatable_cpu_milli, 3860)
        # POD_RUNNING requested 500m on node-worker-1
        self.assertEqual(summary.total_requested_cpu_milli, 500)
        # Headroom = 3860 - 500 = 3360m
        self.assertEqual(summary.to_dict()["available_cpu_milli"], 3360)

    def test_disconnected_client_raises_infrastructure_error(self) -> None:
        """Verify operations on disconnected client raise InfrastructureError."""
        disconnected_client = MockKubernetesClient(connected=False)
        adapter = KubernetesAdapter(disconnected_client)
        self.assertFalse(adapter.check_connection())
        with self.assertRaises(InfrastructureError):
            adapter.get_agent_status(agent_id=SAMPLE_AGENT_ID, namespace=SAMPLE_NAMESPACE)


if __name__ == "__main__":
    unittest.main()

