"""Tool implementation: get_agent_status."""

from typing import Any, Dict

from src.errors.exceptions import InfrastructureError, ValidationError
from src.kubernetes.adapter import KubernetesAdapter
from src.logger.logger import get_logger

logger = get_logger("tools.agent_status")

TOOL_NAME = "get_agent_status"
TOOL_DESCRIPTION = "Query status of a specific Nasiko agent workload and its backing Kubernetes resources."
INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "agent_id": {
            "type": "string",
            "description": "The RFC 4122 UUID v4 of the Nasiko agent.",
        },
        "namespace": {
            "type": "string",
            "description": "Optional Kubernetes namespace (defaults to configured namespace or 'default').",
        },
    },
    "required": ["agent_id"],
}

AGENT_STATUS_NAME = TOOL_NAME
AGENT_STATUS_DESC = TOOL_DESCRIPTION
AGENT_STATUS_SCHEMA = INPUT_SCHEMA


def handle_get_agent_status(adapter: KubernetesAdapter, args: Dict[str, Any]) -> Dict[str, Any]:
    """Execute get_agent_status tool."""
    agent_id = args.get("agent_id")
    if not agent_id or not isinstance(agent_id, str):
        raise ValidationError("Missing or invalid 'agent_id' parameter", details={"agent_id": agent_id})

    namespace = args.get("namespace")

    dep = adapter.get_agent_status(agent_id=agent_id.strip(), namespace=namespace)
    if not dep:
        return {
            "found": False,
            "agent_id": agent_id,
            "message": f"No active deployment found for agent '{agent_id}'",
        }

    # Also lookup any pods belonging to this deployment
    all_pending = adapter.get_pending_pods(namespace=dep.namespace)
    agent_pending_pods = [
        p.to_dict() for p in all_pending
        if p.owner_name == agent_id or agent_id in p.pod_name
    ]

    return {
        "found": True,
        "agent_id": agent_id,
        "deployment": dep.to_dict(),
        "pending_pods_count": len(agent_pending_pods),
        "pending_pods": agent_pending_pods,
    }
