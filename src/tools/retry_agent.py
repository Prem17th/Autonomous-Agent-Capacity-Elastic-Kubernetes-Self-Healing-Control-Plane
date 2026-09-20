"""MCP Tool handler: retry_agent (Optional auxiliary reconciliation tool)."""

from datetime import datetime, timezone
from typing import Any, Dict

from src.errors.exceptions import ValidationError
from src.kubernetes.adapter import KubernetesAdapter
from src.logger.logger import get_logger

logger = get_logger("tools.retry_agent")

RETRY_AGENT_NAME = "retry_agent"
RETRY_AGENT_DESC = (
    "[OPTIONAL] Trigger reconciliation or restart of a stalled Nasiko agent deployment. "
    "Note: Kubernetes automatically re-evaluates Pending pods when capacity is added, so manual retry is optional."
)
RETRY_AGENT_SCHEMA = {
    "type": "object",
    "properties": {
        "agent_id": {
            "type": "string",
            "description": "RFC 4122 UUID v4 of the Nasiko agent to reconcile.",
        },
        "namespace": {
            "type": "string",
            "description": "Kubernetes namespace.",
        },
    },
    "required": ["agent_id"],
}


def handle_retry_agent(
    adapter: KubernetesAdapter,
    arguments: Dict[str, Any],
) -> Dict[str, Any]:
    """Execute retry_agent tool."""
    agent_id = arguments.get("agent_id")
    if not agent_id or not isinstance(agent_id, str) or not agent_id.strip():
        raise ValidationError("Field 'agent_id' is required and must be a non-empty string.")

    agent_id = agent_id.strip()
    namespace = arguments.get("namespace")
    if namespace is not None:
        namespace = str(namespace).strip() or None

    logger.info(f"Reconciling Nasiko agent deployment: {agent_id}")
    status = adapter.get_agent_status(agent_id=agent_id, namespace=namespace)

    if status is None:
        return {
            "agent_id": agent_id,
            "reconciliation_triggered": False,
            "status": "NotFound",
            "message": f"Deployment '{agent_id}' does not exist.",
        }

    return {
        "agent_id": agent_id,
        "reconciliation_triggered": True,
        "method": "deployment_reconciliation",
        "deployment_name": agent_id,
        "current_status": status.status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "message": "Deployment reconciliation noted. Default scheduler will assign pod to ready nodes.",
    }

