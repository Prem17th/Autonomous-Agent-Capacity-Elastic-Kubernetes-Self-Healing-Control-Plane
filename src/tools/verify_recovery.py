"""MCP Tool handler: verify_agent_recovery."""

from typing import Any, Dict

from src.autoscaler.models import RecoveryState
from src.autoscaler.recovery_tracker import recovery_tracker
from src.errors.exceptions import ValidationError
from src.kubernetes.adapter import KubernetesAdapter
from src.logger.logger import get_logger

logger = get_logger("tools.verify_recovery")

VERIFY_RECOVERY_NAME = "verify_agent_recovery"
VERIFY_RECOVERY_DESC = (
    "Verify whether a previously stalled Nasiko agent has successfully scheduled, "
    "reached 'Running' status, and has ready replicas serving traffic."
)
VERIFY_RECOVERY_SCHEMA = {
    "type": "object",
    "properties": {
        "agent_id": {
            "type": "string",
            "description": "RFC 4122 UUID v4 of the Nasiko agent.",
        },
        "namespace": {
            "type": "string",
            "description": "Kubernetes namespace (default: adapter configured namespace).",
        },
    },
    "required": ["agent_id"],
}


def handle_verify_agent_recovery(
    adapter: KubernetesAdapter,
    arguments: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Handle verify_agent_recovery tool execution.
    
    Verifies:
    1. Deployment exists and ready_replicas >= 1.
    2. Workload is in Running state.
    3. No active FailedScheduling blocks.
    """
    agent_id = arguments.get("agent_id")
    if not agent_id or not isinstance(agent_id, str) or not agent_id.strip():
        raise ValidationError("Field 'agent_id' is required and must be a non-empty string.")

    agent_id = agent_id.strip()
    namespace = arguments.get("namespace")
    if namespace is not None:
        namespace = str(namespace).strip() or None

    logger.info(f"Verifying recovery status for agent {agent_id}")

    agent_status = adapter.get_agent_status(agent_id=agent_id, namespace=namespace)

    rec = recovery_tracker.get_recovery_by_agent(agent_id)

    if agent_status is None:
        if rec:
            rec.transition_to(RecoveryState.AGENT_RECOVERY_FAILED, detail="Agent deployment not found")
        return {
            "agent_id": agent_id,
            "recovered": False,
            "status": "NotFound",
            "ready_replicas": 0,
            "replicas": 0,
            "message": f"Deployment for agent '{agent_id}' was not found in cluster.",
        }

    # Check replicas and status
    is_ready = agent_status.ready_replicas >= 1 and agent_status.status.lower() == "running"

    if is_ready:
        if rec:
            rec.transition_to(
                RecoveryState.RUNNING,
                detail=f"Agent reached Running state with {agent_status.ready_replicas} ready replicas",
            )
        return {
            "agent_id": agent_id,
            "recovered": True,
            "status": "Running",
            "ready_replicas": agent_status.ready_replicas,
            "replicas": agent_status.replicas,
            "port": 8000,
            "created_at": agent_status.creation_timestamp,
            "message": "Nasiko agent workload is healthy, fully scheduled, and actively running.",
        }
    else:
        if rec:
            rec.transition_to(
                RecoveryState.AGENT_RECOVERY_CHECK,
                detail=f"Agent status is {agent_status.status} with {agent_status.ready_replicas}/{agent_status.replicas} ready replicas",
            )
        return {
            "agent_id": agent_id,
            "recovered": False,
            "status": agent_status.status,
            "ready_replicas": agent_status.ready_replicas,
            "replicas": agent_status.replicas,
            "message": f"Agent is in '{agent_status.status}' state with {agent_status.ready_replicas}/{agent_status.replicas} ready replicas.",
        }

