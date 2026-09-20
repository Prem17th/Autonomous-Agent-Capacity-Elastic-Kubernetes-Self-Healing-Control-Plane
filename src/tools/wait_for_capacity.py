"""MCP Tool handler: wait_for_capacity."""

from typing import Any, Dict, Optional

from src.autoscaler.models import RecoveryState
from src.autoscaler.provider import AutoscalerProvider
from src.autoscaler.recovery_tracker import recovery_tracker
from src.errors.exceptions import ValidationError
from src.logger.logger import get_logger

logger = get_logger("tools.wait_for_capacity")

WAIT_FOR_CAPACITY_NAME = "wait_for_capacity"
WAIT_FOR_CAPACITY_DESC = (
    "Wait/poll until requested capacity is provisioned, joined the cluster, and in 'Ready' state with allocatable resources."
)
WAIT_FOR_CAPACITY_SCHEMA = {
    "type": "object",
    "properties": {
        "scale_request_id": {
            "type": "string",
            "description": "Correlation ID from request_scale_up.",
        },
        "target_ready_nodes": {
            "type": "integer",
            "description": "Expected minimum total ready nodes count.",
        },
        "timeout_seconds": {
            "type": "integer",
            "description": "Maximum seconds to wait before timing out (default 180, max 300).",
            "default": 180,
        },
        "poll_interval_seconds": {
            "type": "number",
            "description": "Interval between polling checks in seconds (default 2.0).",
            "default": 2.0,
        },
        "agent_id": {
            "type": "string",
            "description": "Optional Nasiko agent UUID for recovery tracking.",
        },
    },
}


def handle_wait_for_capacity(
    provider: AutoscalerProvider,
    arguments: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Handle wait_for_capacity tool execution.
    
    Polls the AutoscalerProvider until capacity is ready, failed, or timed out.
    """
    scale_request_id = arguments.get("scale_request_id")
    if scale_request_id is not None:
        scale_request_id = str(scale_request_id).strip() or None

    target_ready_nodes = arguments.get("target_ready_nodes")
    if target_ready_nodes is not None:
        try:
            target_ready_nodes = int(target_ready_nodes)
        except (ValueError, TypeError) as e:
            raise ValidationError(f"target_ready_nodes must be an integer, got: {target_ready_nodes}") from e

    raw_timeout = arguments.get("timeout_seconds", 180)
    try:
        timeout_seconds = int(raw_timeout)
    except (ValueError, TypeError) as e:
        raise ValidationError(f"timeout_seconds must be an integer, got: {raw_timeout}") from e

    if timeout_seconds <= 0 or timeout_seconds > 300:
        raise ValidationError(f"timeout_seconds must be between 1 and 300, got: {timeout_seconds}")

    raw_interval = arguments.get("poll_interval_seconds", 2.0)
    try:
        poll_interval = float(raw_interval)
    except (ValueError, TypeError) as e:
        raise ValidationError(f"poll_interval_seconds must be a number, got: {raw_interval}") from e

    agent_id = arguments.get("agent_id")
    if agent_id is not None:
        agent_id = str(agent_id).strip() or None

    rec = None
    if agent_id:
        rec = recovery_tracker.get_recovery_by_agent(agent_id)
        if rec:
            rec.transition_to(RecoveryState.PROVISIONING, detail="Waiting for autoscaler capacity to become ready")

    logger.info(
        f"Waiting for capacity (operation: {scale_request_id}, timeout: {timeout_seconds}s, interval: {poll_interval}s)"
    )

    result = provider.wait_for_capacity(
        operation_id=scale_request_id,
        target_ready_nodes=target_ready_nodes,
        timeout_seconds=timeout_seconds,
        poll_interval_seconds=poll_interval,
    )

    status = result.get("status")
    if rec:
        if status == "READY":
            rec.transition_to(
                RecoveryState.CAPACITY_READY,
                detail=f"Capacity ready with {result.get('ready_nodes_count')} ready nodes",
            )
        elif status == "TIMEOUT":
            rec.transition_to(RecoveryState.TIMEOUT, detail="Timed out waiting for capacity")
        elif status == "FAILED":
            rec.transition_to(RecoveryState.SCALE_FAILED, detail=result.get("error", "Scaling failed"))

    return result

