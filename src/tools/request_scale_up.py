"""MCP Tool handler: request_scale_up."""

from typing import Any, Dict, Optional
import uuid

from src.autoscaler.models import RecoveryState, ScaleRequest
from src.autoscaler.policy import RecoveryPolicyEngine
from src.autoscaler.provider import AutoscalerProvider
from src.autoscaler.recovery_tracker import recovery_tracker
from src.errors.exceptions import ValidationError
from src.kubernetes.adapter import KubernetesAdapter
from src.logger.logger import get_logger

logger = get_logger("tools.request_scale_up")

REQUEST_SCALE_UP_NAME = "request_scale_up"
REQUEST_SCALE_UP_DESC = (
    "Safely request additional Kubernetes compute capacity / worker nodes for a target node pool. "
    "Validates safety policies (max nodes, rate limits, cooldown debounce) before triggering provisioning."
)
REQUEST_SCALE_UP_SCHEMA = {
    "type": "object",
    "properties": {
        "node_pool": {
            "type": "string",
            "description": "Target node pool identifier (e.g. 'default', 'general-compute', 'memory-optimized').",
            "default": "default",
        },
        "target_nodes": {
            "type": "integer",
            "description": "Number of new nodes to provision (default 1, max 2).",
            "default": 1,
        },
        "requested_cpu": {
            "type": "string",
            "description": "Required CPU amount (e.g. '2000m' or '2').",
        },
        "requested_memory": {
            "type": "string",
            "description": "Required Memory amount (e.g. '4Gi' or '4096Mi').",
        },
        "reason": {
            "type": "string",
            "description": "Operational justification for scaling (e.g. 'insufficient_cpu').",
            "default": "capacity_exhaustion",
        },
        "agent_id": {
            "type": "string",
            "description": "Optional Aegis agent UUID that triggered this capacity request.",
        },
        "dry_run": {
            "type": "boolean",
            "description": "If true, validates policies and calculates capacity impact without mutating infrastructure.",
            "default": False,
        },
    },
}


def handle_request_scale_up(
    adapter: KubernetesAdapter,
    provider: AutoscalerProvider,
    policy_engine: RecoveryPolicyEngine,
    arguments: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Handle request_scale_up tool execution.
    
    1. Validates input parameters.
    2. Queries current cluster node count.
    3. Evaluates safety policies via RecoveryPolicyEngine.
    4. If approved, requests capacity via AutoscalerProvider.
    5. Links operation to agent recovery tracking if agent_id is provided.
    """
    node_pool = str(arguments.get("node_pool") or "default").strip()
    raw_nodes = arguments.get("target_nodes", 1)
    try:
        nodes_requested = int(raw_nodes)
    except (ValueError, TypeError) as e:
        raise ValidationError(f"target_nodes must be an integer, got: {raw_nodes}") from e

    dry_run = bool(arguments.get("dry_run", False))
    reason = str(arguments.get("reason") or "capacity_exhaustion").strip()
    agent_id = arguments.get("agent_id")
    if agent_id is not None:
        agent_id = str(agent_id).strip() or None

    req_id = f"scale-req-{uuid.uuid4().hex[:8]}"

    scale_req = ScaleRequest(
        request_id=req_id,
        node_pool=node_pool,
        nodes_requested=nodes_requested,
        reason=reason,
        agent_id=agent_id,
        dry_run=dry_run,
    )

    # 1. Obtain current cluster node count for policy check
    try:
        cap = adapter.get_node_capacity()
        current_cluster_nodes = cap.total_nodes
    except Exception as e:
        logger.warning(f"Could not query live node capacity for policy check ({e}), defaulting to 2 nodes")
        current_cluster_nodes = 2

    # 2. Evaluate Policy
    validation = policy_engine.validate_scale_request(scale_req, current_cluster_nodes)

    # Track recovery state if agent_id is provided
    rec = None
    if agent_id:
        rec = recovery_tracker.get_recovery_by_agent(agent_id)
        if not rec:
            rec = recovery_tracker.start_recovery(agent_id=agent_id, diagnosis_reason=reason)

    if not validation.allowed:
        if rec:
            rec.transition_to(RecoveryState.POLICY_DENIED, detail=validation.reason)
        return {
            "scale_request_id": req_id,
            "status": "POLICY_DENIED",
            "allowed": False,
            "reason": validation.reason,
            "details": validation.details,
            "node_pool": node_pool,
            "nodes_requested": nodes_requested,
            "dry_run": dry_run,
        }

    if dry_run:
        return {
            "scale_request_id": req_id,
            "status": "DRY_RUN_PASSED",
            "allowed": True,
            "node_pool": node_pool,
            "nodes_requested": nodes_requested,
            "current_ready_nodes": current_cluster_nodes,
            "target_ready_nodes": current_cluster_nodes + nodes_requested,
            "dry_run": True,
            "message": "Policy validation succeeded. No infrastructure mutations were performed in dry-run mode.",
        }

    # 3. Execute scale operation via provider
    operation = provider.request_scale_up(scale_req)
    policy_engine.record_operation(operation)

    if rec:
        rec.scale_request_id = operation.operation_id
        rec.transition_to(
            RecoveryState.SCALE_REQUESTED,
            detail=f"Requested +{nodes_requested} nodes in pool '{node_pool}' (Op ID: {operation.operation_id})",
        )

    return {
        "scale_request_id": operation.operation_id,
        "status": "ACCEPTED",
        "allowed": True,
        "node_pool": operation.node_pool,
        "nodes_requested": operation.nodes_requested,
        "current_ready_nodes": operation.current_ready_nodes,
        "target_ready_nodes": operation.target_ready_nodes,
        "created_at": operation.created_at,
        "estimated_latency_seconds": operation.estimated_latency_seconds,
        "provider": provider.provider_type,
        "agent_id": agent_id,
    }

