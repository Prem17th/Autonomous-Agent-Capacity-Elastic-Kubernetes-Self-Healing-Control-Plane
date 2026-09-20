"""Tool implementation: get_pending_pods."""

from typing import Any, Dict

from src.kubernetes.adapter import KubernetesAdapter
from src.logger.logger import get_logger

logger = get_logger("tools.pending_pods")

TOOL_NAME = "get_pending_pods"
TOOL_DESCRIPTION = "List Kubernetes pods stuck in Pending or Unschedulable state with normalized resource requests."
INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "namespace": {
            "type": "string",
            "description": "Optional Kubernetes namespace to filter pods (defaults to all or configured namespace).",
        },
    },
}

PENDING_PODS_NAME = TOOL_NAME
PENDING_PODS_DESC = TOOL_DESCRIPTION
PENDING_PODS_SCHEMA = INPUT_SCHEMA


def handle_get_pending_pods(adapter: KubernetesAdapter, args: Dict[str, Any]) -> Dict[str, Any]:
    """Execute get_pending_pods tool."""
    namespace = args.get("namespace") if isinstance(args, dict) else None
    pending = adapter.get_pending_pods(namespace=namespace)

    return {
        "count": len(pending),
        "namespace": namespace or "all",
        "pending_pods": [p.to_dict() for p in pending],
    }
