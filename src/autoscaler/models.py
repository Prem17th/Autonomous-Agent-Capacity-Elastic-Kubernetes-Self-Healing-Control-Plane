"""Data models and enums for Sentinel Autoscaling & Recovery."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class OperationState(str, Enum):
    """Lifecycle state of a scaling operation."""
    REQUESTED = "REQUESTED"
    PROVISIONING = "PROVISIONING"
    READY = "READY"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"
    CANCELLED = "CANCELLED"


class RecoveryState(str, Enum):
    """Lifecycle state of an end-to-end agent recovery workflow."""
    DETECTED = "DETECTED"
    DIAGNOSED = "DIAGNOSED"
    POLICY_VALIDATED = "POLICY_VALIDATED"
    SCALE_REQUESTED = "SCALE_REQUESTED"
    PROVISIONING = "PROVISIONING"
    CAPACITY_READY = "CAPACITY_READY"
    AGENT_RECOVERY_CHECK = "AGENT_RECOVERY_CHECK"
    RUNNING = "RUNNING"
    # Failure terminal states
    POLICY_DENIED = "POLICY_DENIED"
    SCALE_FAILED = "SCALE_FAILED"
    TIMEOUT = "TIMEOUT"
    CAPACITY_NOT_SUFFICIENT = "CAPACITY_NOT_SUFFICIENT"
    AGENT_RECOVERY_FAILED = "AGENT_RECOVERY_FAILED"
    TERMINAL_FAILURE = "TERMINAL_FAILURE"


@dataclass
class ScaleRequest:
    """Specification of a capacity scale-up request."""
    request_id: str
    node_pool: str = "default"
    nodes_requested: int = 1
    requested_cpu_milli: int = 0
    requested_memory_bytes: int = 0
    reason: str = "capacity_exhaustion"
    agent_id: Optional[str] = None
    dry_run: bool = False
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "node_pool": self.node_pool,
            "nodes_requested": self.nodes_requested,
            "requested_cpu_milli": self.requested_cpu_milli,
            "requested_memory_bytes": self.requested_memory_bytes,
            "reason": self.reason,
            "agent_id": self.agent_id,
            "dry_run": self.dry_run,
            "created_at": self.created_at,
        }


@dataclass
class ScaleOperation:
    """Representation of an active or historical scaling operation."""
    operation_id: str
    node_pool: str
    nodes_requested: int
    state: OperationState
    current_ready_nodes: int
    target_ready_nodes: int
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    estimated_latency_seconds: int = 60
    provisioned_nodes: List[Dict[str, Any]] = field(default_factory=list)
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "operation_id": self.operation_id,
            "node_pool": self.node_pool,
            "nodes_requested": self.nodes_requested,
            "state": self.state.value if isinstance(self.state, OperationState) else str(self.state),
            "current_ready_nodes": self.current_ready_nodes,
            "target_ready_nodes": self.target_ready_nodes,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "estimated_latency_seconds": self.estimated_latency_seconds,
            "provisioned_nodes": self.provisioned_nodes,
            "error_message": self.error_message,
        }


@dataclass
class NodePoolStatus:
    """Capacity and status of a node pool."""
    node_pool: str
    current_nodes: int
    ready_nodes: int
    pending_nodes: int
    min_nodes: int
    max_nodes: int
    instance_types: List[str]
    status: str
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_pool": self.node_pool,
            "current_nodes": self.current_nodes,
            "ready_nodes": self.ready_nodes,
            "pending_nodes": self.pending_nodes,
            "min_nodes": self.min_nodes,
            "max_nodes": self.max_nodes,
            "instance_types": self.instance_types,
            "status": self.status,
            "updated_at": self.updated_at,
        }


@dataclass
class RecoveryRecord:
    """Audit record of an agent recovery lifecycle."""
    recovery_id: str
    agent_id: str
    pod_name: Optional[str] = None
    initial_state: str = "DETECTED"
    current_state: RecoveryState = RecoveryState.DETECTED
    scale_request_id: Optional[str] = None
    diagnosis_reason: Optional[str] = None
    history: List[Dict[str, Any]] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    resolved_at: Optional[str] = None
    error_message: Optional[str] = None

    def transition_to(self, new_state: RecoveryState, detail: Optional[str] = None) -> None:
        """Record state transition in audit trail."""
        now = datetime.now(timezone.utc).isoformat()
        self.current_state = new_state
        self.updated_at = now
        entry: Dict[str, Any] = {
            "state": new_state.value if isinstance(new_state, RecoveryState) else str(new_state),
            "timestamp": now,
        }
        if detail:
            entry["detail"] = detail
        self.history.append(entry)
        if new_state in {RecoveryState.RUNNING, RecoveryState.POLICY_DENIED, RecoveryState.SCALE_FAILED, RecoveryState.TIMEOUT, RecoveryState.TERMINAL_FAILURE}:
            self.resolved_at = now

    def to_dict(self) -> Dict[str, Any]:
        return {
            "recovery_id": self.recovery_id,
            "agent_id": self.agent_id,
            "pod_name": self.pod_name,
            "initial_state": self.initial_state,
            "current_state": self.current_state.value if isinstance(self.current_state, RecoveryState) else str(self.current_state),
            "scale_request_id": self.scale_request_id,
            "diagnosis_reason": self.diagnosis_reason,
            "history": self.history,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "resolved_at": self.resolved_at,
            "error_message": self.error_message,
        }

