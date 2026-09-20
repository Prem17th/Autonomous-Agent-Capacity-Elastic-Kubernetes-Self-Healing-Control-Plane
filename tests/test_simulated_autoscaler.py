"""Unit tests for SimulatedAutoscalerProvider."""

import copy
import time
import unittest

from src.autoscaler.models import OperationState, ScaleRequest
from src.autoscaler.simulated_provider import SimulatedAutoscalerProvider
from src.errors.exceptions import ValidationError
from src.kubernetes.adapter import KubernetesAdapter
from src.kubernetes.client import MockKubernetesClient
from tests.fixtures.k8s_fixtures import NODES_LIST


class TestSimulatedAutoscaler(unittest.TestCase):
    """Test suite for SimulatedAutoscalerProvider mechanics and lifecycle."""

    def setUp(self) -> None:
        self.client = MockKubernetesClient(
            nodes=copy.deepcopy(NODES_LIST),
            connected=True,
        )
        self.adapter = KubernetesAdapter(self.client)
        self.provider = SimulatedAutoscalerProvider(
            adapter=self.adapter,
            provision_delay_seconds=0.05,
        )

    def test_request_scale_up_lifecycle(self) -> None:
        """Verify scale operation progresses from PROVISIONING to READY."""
        req = ScaleRequest(
            request_id="req-test-1",
            node_pool="default",
            nodes_requested=1,
        )
        op = self.provider.request_scale_up(req)
        self.assertEqual(op.state, OperationState.PROVISIONING)
        self.assertEqual(op.nodes_requested, 1)

        # Wait for simulated provisioning delay
        time.sleep(0.08)
        updated_op = self.provider.get_operation_status(op.operation_id)
        self.assertIsNotNone(updated_op)
        self.assertEqual(updated_op.state, OperationState.READY)
        self.assertEqual(len(updated_op.provisioned_nodes), 1)
        self.assertTrue(updated_op.provisioned_nodes[0]["ready"])
        self.assertEqual(updated_op.provisioned_nodes[0]["allocatable_cpu_milli"], 4000)

    def test_mock_capacity_injection(self) -> None:
        """Verify newly provisioned nodes are reflected in the KubernetesAdapter."""
        initial_cap = self.adapter.get_node_capacity()
        initial_nodes = initial_cap.total_nodes

        req = ScaleRequest(
            request_id="req-inject",
            node_pool="default",
            nodes_requested=2,
        )
        op = self.provider.request_scale_up(req)
        result = self.provider.wait_for_capacity(
            operation_id=op.operation_id,
            timeout_seconds=5,
            poll_interval_seconds=0.02,
        )

        self.assertEqual(result["status"], "READY")
        self.assertEqual(len(result["provisioned_nodes"]), 2)

        # Check that adapter now reports initial + 2 nodes
        new_cap = self.adapter.get_node_capacity()
        self.assertEqual(new_cap.total_nodes, initial_nodes + 2)

    def test_wait_for_capacity_timeout(self) -> None:
        """Verify wait_for_capacity cleanly times out when configured."""
        provider_timeout = SimulatedAutoscalerProvider(
            adapter=self.adapter,
            provision_delay_seconds=5.0,  # 5s delay
            simulate_timeout=True,
        )
        req = ScaleRequest(request_id="req-to", node_pool="default", nodes_requested=1)
        op = provider_timeout.request_scale_up(req)

        result = provider_timeout.wait_for_capacity(
            operation_id=op.operation_id,
            timeout_seconds=1,  # 1s timeout
            poll_interval_seconds=0.05,
        )
        self.assertEqual(result["status"], "TIMEOUT")
        self.assertIn("Timed out waiting", result["error"])

    def test_wait_for_capacity_failure(self) -> None:
        """Verify wait_for_capacity handles provider failure."""
        provider_fail = SimulatedAutoscalerProvider(
            adapter=self.adapter,
            simulate_failure=True,
        )
        req = ScaleRequest(request_id="req-fail", node_pool="default", nodes_requested=1)
        op = provider_fail.request_scale_up(req)

        result = provider_fail.wait_for_capacity(
            operation_id=op.operation_id,
            timeout_seconds=2,
            poll_interval_seconds=0.02,
        )
        self.assertEqual(result["status"], "FAILED")
        self.assertIn("InsufficientInstanceCapacity", result["error"])

    def test_get_autoscaler_status(self) -> None:
        """Verify autoscaler status and metric reporting."""
        status = self.provider.get_autoscaler_status()
        self.assertEqual(status["status"], "HEALTHY")
        self.assertEqual(status["provider"], "simulated")
        self.assertEqual(status["mode"], "simulation")
        self.assertIn("default", status["configured_node_pools"])

    def test_get_node_pool_status(self) -> None:
        """Verify node pool querying and bounds."""
        pool = self.provider.get_node_pool_status("default")
        self.assertEqual(pool.node_pool, "default")
        self.assertEqual(pool.max_nodes, 10)
        self.assertIn("t3.xlarge", pool.instance_types)

        with self.assertRaises(ValidationError):
            self.provider.get_node_pool_status("unknown-pool-xyz")


if __name__ == "__main__":
    unittest.main()

