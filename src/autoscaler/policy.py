"""Safety and Policy Engine for Sentinel Autoscaling Operations."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import time
from typing import Any, Dict, List, Optional, Set, Tuple

from src.autoscaler.models import ScaleOperation, ScaleRequest
from src.errors.exceptions import PolicyError, ValidationError
from src.logger.logger import get_logger

logger = get_logger("policy")

DEFAULT_ALLOWED_NODE_POOLS: Set[str] = {"default", "general-compute", "memory-optimized"}
DEFAULT_MAX_NODES_PER_REQUEST: int = 2
DEFAULT_MAX_CLUSTER_NODES: int = 10
DEFAULT_COOLDOWN_SECONDS: int = 120
DEFAULT_MAX_OPERATIONS_PER_WINDOW: int = 3
DEFAULT_OPERATION_WINDOW_SECONDS: int = 900  # 15 minutes
DEFAULT_TIMEOUT_SECONDS: int = 180
MAXIMUM_TIMEOUT_SECONDS: int = 300


@dataclass
class PolicyValidationResult:
    """Outcome of safety policy evaluation."""
    allowed: bool
    reason: str
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "allowed": self.allowed,
            "reason": self.reason,
            "details": self.details,
        }


class RecoveryPolicyEngine:
    """
    Enforces safety policies, concurrency limits, cooldowns, and rate limits
    on capacity scaling operations to protect the cluster from flapping or runaway costs.
    """

    def __init__(
        self,
        max_nodes_per_request: int = DEFAULT_MAX_NODES_PER_REQUEST,
        max_cluster_nodes: int = DEFAULT_MAX_CLUSTER_NODES,
        cooldown_seconds: int = DEFAULT_COOLDOWN_SECONDS,
        max_operations_per_window: int = DEFAULT_MAX_OPERATIONS_PER_WINDOW,
        operation_window_seconds: int = DEFAULT_OPERATION_WINDOW_SECONDS,
        allowed_node_pools: Optional[Set[str]] = None,
        default_timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
        maximum_timeout_seconds: int = MAXIMUM_TIMEOUT_SECONDS,
    ) -> None:
        self.max_nodes_per_request = max_nodes_per_request
        self.max_cluster_nodes = max_cluster_nodes
        self.cooldown_seconds = cooldown_seconds
        self.max_operations_per_window = max_operations_per_window
        self.operation_window_seconds = operation_window_seconds
        self.allowed_node_pools = allowed_node_pools or set(DEFAULT_ALLOWED_NODE_POOLS)
        self.default_timeout_seconds = default_timeout_seconds
        self.maximum_timeout_seconds = maximum_timeout_seconds

        # Operation history tracking for rate limits and cooldown
        self._history: List[Tuple[float, ScaleOperation]] = []

    def validate_scale_request(
        self,
        request: ScaleRequest,
        current_cluster_nodes: int,
    ) -> PolicyValidationResult:
        """
        Evaluate all safety policies for a given scale request.
        
        Checks:
        1. Node pool whitelist.
        2. Node count per single request <= max_nodes_per_request.
        3. Projected cluster size <= max_cluster_nodes.
        4. Cooldown debounce since last scale action on the same node pool.
        5. Rate limit (max operations in rolling window).
        """
        now = time.time()

        # 1. Allowed Node Pool Check
        if request.node_pool not in self.allowed_node_pools:
            msg = f"Node pool '{request.node_pool}' is not permitted. Allowed pools: {sorted(self.allowed_node_pools)}"
            logger.warning(f"Policy rejection: {msg}")
            return PolicyValidationResult(
                allowed=False,
                reason="DISALLOWED_NODE_POOL",
                details={"node_pool": request.node_pool, "allowed_pools": sorted(self.allowed_node_pools)},
            )

        # 2. Max Nodes Per Single Request
        if request.nodes_requested <= 0:
            msg = f"nodes_requested must be positive, got {request.nodes_requested}"
            return PolicyValidationResult(
                allowed=False,
                reason="INVALID_NODE_COUNT",
                details={"nodes_requested": request.nodes_requested},
            )

        if request.nodes_requested > self.max_nodes_per_request:
            msg = (
                f"Requested {request.nodes_requested} nodes exceeds single-request limit of "
                f"{self.max_nodes_per_request}"
            )
            logger.warning(f"Policy rejection: {msg}")
            return PolicyValidationResult(
                allowed=False,
                reason="MAX_NODES_PER_REQUEST_EXCEEDED",
                details={
                    "nodes_requested": request.nodes_requested,
                    "max_nodes_per_request": self.max_nodes_per_request,
                },
            )

        # 3. Max Total Cluster Nodes Limit
        projected_total = current_cluster_nodes + request.nodes_requested
        if projected_total > self.max_cluster_nodes:
            msg = (
                f"Scaling by +{request.nodes_requested} would bring cluster to {projected_total} nodes, "
                f"exceeding max ceiling of {self.max_cluster_nodes}"
            )
            logger.warning(f"Policy rejection: {msg}")
            return PolicyValidationResult(
                allowed=False,
                reason="MAX_CLUSTER_NODES_EXCEEDED",
                details={
                    "current_cluster_nodes": current_cluster_nodes,
                    "nodes_requested": request.nodes_requested,
                    "projected_total": projected_total,
                    "max_cluster_nodes": self.max_cluster_nodes,
                },
            )

        # 4. Cooldown Debounce Check (Skip if dry_run)
        if not request.dry_run:
            in_cooldown, remaining = self.is_in_cooldown(request.node_pool, now=now)
            if in_cooldown:
                msg = (
                    f"Node pool '{request.node_pool}' is in cooldown debounce window. "
                    f"Remaining cooldown: {remaining:.1f}s"
                )
                logger.warning(f"Policy rejection: {msg}")
                return PolicyValidationResult(
                    allowed=False,
                    reason="COOLDOWN_ACTIVE",
                    details={
                        "node_pool": request.node_pool,
                        "cooldown_seconds": self.cooldown_seconds,
                        "remaining_seconds": round(remaining, 1),
                    },
                )

            # 5. Rate Limit Check (Rolling window)
            recent_ops = self._get_recent_operations(now=now)
            if len(recent_ops) >= self.max_operations_per_window:
                msg = (
                    f"Scale rate limit exceeded ({len(recent_ops)} operations in {self.operation_window_seconds}s window, "
                    f"max allowed: {self.max_operations_per_window})"
                )
                logger.warning(f"Policy rejection: {msg}")
                return PolicyValidationResult(
                    allowed=False,
                    reason="RATE_LIMIT_EXCEEDED",
                    details={
                        "recent_operations_count": len(recent_ops),
                        "max_operations_per_window": self.max_operations_per_window,
                        "window_seconds": self.operation_window_seconds,
                    },
                )

        logger.info(
            f"Policy validation passed for request {request.request_id} (pool: {request.node_pool}, nodes: +{request.nodes_requested})"
        )
        return PolicyValidationResult(
            allowed=True,
            reason="POLICY_PASSED",
            details={
                "nodes_requested": request.nodes_requested,
                "node_pool": request.node_pool,
                "projected_total_nodes": projected_total,
                "dry_run": request.dry_run,
            },
        )

    def is_in_cooldown(self, node_pool: str, now: Optional[float] = None) -> Tuple[bool, float]:
        """Check if a node pool is currently within its cooldown debounce window."""
        if now is None:
            now = time.time()

        for ts, op in reversed(self._history):
            if op.node_pool == node_pool:
                elapsed = now - ts
                if elapsed < self.cooldown_seconds:
                    return True, self.cooldown_seconds - elapsed
                break
        return False, 0.0

    def record_operation(self, operation: ScaleOperation, timestamp: Optional[float] = None) -> None:
        """Record an approved and executed operation in the policy history."""
        ts = timestamp if timestamp is not None else time.time()
        self._history.append((ts, operation))
        self._prune_history(now=ts)

    def _get_recent_operations(self, now: Optional[float] = None) -> List[ScaleOperation]:
        """Get operations within the sliding rate-limit window."""
        if now is None:
            now = time.time()
        cutoff = now - self.operation_window_seconds
        return [op for ts, op in self._history if ts >= cutoff]

    def _prune_history(self, now: Optional[float] = None) -> None:
        """Remove historical operations older than the rate limit window."""
        if now is None:
            now = time.time()
        cutoff = now - max(self.operation_window_seconds, self.cooldown_seconds * 2)
        self._history = [(ts, op) for ts, op in self._history if ts >= cutoff]

    def reset_history(self) -> None:
        """Clear all operation history (primarily for test isolation)."""
        self._history.clear()

