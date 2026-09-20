"""Unit tests for Sentinel Recovery Policy Engine."""

import time
import unittest

from src.autoscaler.models import OperationState, ScaleOperation, ScaleRequest
from src.autoscaler.policy import (
    DEFAULT_COOLDOWN_SECONDS,
    DEFAULT_MAX_CLUSTER_NODES,
    DEFAULT_MAX_NODES_PER_REQUEST,
    RecoveryPolicyEngine,
)


class TestAutoscalerPolicy(unittest.TestCase):
    """Test suite for RecoveryPolicyEngine safety rules and limits."""

    def setUp(self) -> None:
        self.engine = RecoveryPolicyEngine(
            max_nodes_per_request=2,
            max_cluster_nodes=10,
            cooldown_seconds=120,
            max_operations_per_window=3,
            operation_window_seconds=900,
            allowed_node_pools={"default", "general-compute", "memory-optimized"},
        )

    def test_valid_scale_request(self) -> None:
        """Verify normal scale request within limits is approved."""
        req = ScaleRequest(request_id="req-1", node_pool="default", nodes_requested=1)
        result = self.engine.validate_scale_request(req, current_cluster_nodes=2)
        self.assertTrue(result.allowed)
        self.assertEqual(result.reason, "POLICY_PASSED")
        self.assertEqual(result.details["projected_total_nodes"], 3)

    def test_dry_run_request(self) -> None:
        """Verify dry-run scale request is approved and indicated."""
        req = ScaleRequest(request_id="req-dry", node_pool="default", nodes_requested=1, dry_run=True)
        result = self.engine.validate_scale_request(req, current_cluster_nodes=2)
        self.assertTrue(result.allowed)
        self.assertTrue(result.details["dry_run"])

    def test_disallowed_node_pool(self) -> None:
        """Verify request for unauthorized node pool is rejected."""
        req = ScaleRequest(request_id="req-bad-pool", node_pool="unauthorized-pool", nodes_requested=1)
        result = self.engine.validate_scale_request(req, current_cluster_nodes=2)
        self.assertFalse(result.allowed)
        self.assertEqual(result.reason, "DISALLOWED_NODE_POOL")

    def test_zero_or_negative_node_count(self) -> None:
        """Verify requesting zero or negative nodes is rejected."""
        req_zero = ScaleRequest(request_id="req-0", node_pool="default", nodes_requested=0)
        res_zero = self.engine.validate_scale_request(req_zero, current_cluster_nodes=2)
        self.assertFalse(res_zero.allowed)
        self.assertEqual(res_zero.reason, "INVALID_NODE_COUNT")

        req_neg = ScaleRequest(request_id="req-neg", node_pool="default", nodes_requested=-1)
        res_neg = self.engine.validate_scale_request(req_neg, current_cluster_nodes=2)
        self.assertFalse(res_neg.allowed)
        self.assertEqual(res_neg.reason, "INVALID_NODE_COUNT")

    def test_exceeding_max_nodes_per_request(self) -> None:
        """Verify requesting more than max_nodes_per_request is rejected."""
        req = ScaleRequest(request_id="req-too-many", node_pool="default", nodes_requested=3)
        result = self.engine.validate_scale_request(req, current_cluster_nodes=2)
        self.assertFalse(result.allowed)
        self.assertEqual(result.reason, "MAX_NODES_PER_REQUEST_EXCEEDED")

    def test_exceeding_max_cluster_nodes(self) -> None:
        """Verify scale bringing total cluster nodes over max ceiling is rejected."""
        req = ScaleRequest(request_id="req-ceiling", node_pool="default", nodes_requested=2)
        result = self.engine.validate_scale_request(req, current_cluster_nodes=9)  # 9 + 2 = 11 > 10
        self.assertFalse(result.allowed)
        self.assertEqual(result.reason, "MAX_CLUSTER_NODES_EXCEEDED")

    def test_cooldown_debounce_active(self) -> None:
        """Verify rapid repeated scale requests within cooldown window are rejected."""
        # 1. Record an initial operation
        op = ScaleOperation(
            operation_id="op-1",
            node_pool="default",
            nodes_requested=1,
            state=OperationState.READY,
            current_ready_nodes=2,
            target_ready_nodes=3,
        )
        self.engine.record_operation(op, timestamp=time.time())

        # 2. Attempt another scale request on the same pool immediately
        req2 = ScaleRequest(request_id="req-2", node_pool="default", nodes_requested=1)
        result = self.engine.validate_scale_request(req2, current_cluster_nodes=3)
        self.assertFalse(result.allowed)
        self.assertEqual(result.reason, "COOLDOWN_ACTIVE")
        self.assertIn("remaining_seconds", result.details)

        # 3. Dry-run ignores cooldown
        dry_req = ScaleRequest(request_id="req-dry", node_pool="default", nodes_requested=1, dry_run=True)
        dry_result = self.engine.validate_scale_request(dry_req, current_cluster_nodes=3)
        self.assertTrue(dry_result.allowed)

        # 4. Request on a DIFFERENT pool is not affected by default's cooldown
        req_diff = ScaleRequest(request_id="req-diff", node_pool="general-compute", nodes_requested=1)
        res_diff = self.engine.validate_scale_request(req_diff, current_cluster_nodes=3)
        self.assertTrue(res_diff.allowed)

    def test_rate_limit_exceeded(self) -> None:
        """Verify rate limit blocks operations exceeding max_operations_per_window."""
        now = time.time()
        # Record 3 operations in general-compute, memory-optimized, etc.
        for i, pool in enumerate(["general-compute", "memory-optimized", "general-compute"]):
            op = ScaleOperation(
                operation_id=f"op-{i}",
                node_pool=pool,
                nodes_requested=1,
                state=OperationState.READY,
                current_ready_nodes=2,
                target_ready_nodes=3,
            )
            # Stagger timestamps slightly outside cooldown
            self.engine.record_operation(op, timestamp=now - 200 - (i * 10))

        # 4th operation in window should trigger RATE_LIMIT_EXCEEDED
        req = ScaleRequest(request_id="req-4", node_pool="default", nodes_requested=1)
        result = self.engine.validate_scale_request(req, current_cluster_nodes=5)
        self.assertFalse(result.allowed)
        self.assertEqual(result.reason, "RATE_LIMIT_EXCEEDED")


if __name__ == "__main__":
    unittest.main()

