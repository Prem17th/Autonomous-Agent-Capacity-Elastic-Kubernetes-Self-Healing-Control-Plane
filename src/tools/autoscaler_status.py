"""MCP Tool handlers: get_autoscaler_status & get_node_pool_status."""

from typing import Any, Dict

from src.autoscaler.provider import AutoscalerProvider
from src.errors.exceptions import ValidationError
from src.logger.logger import get_logger

logger = get_logger("tools.autoscaler_status")

AUTOSCALER_STATUS_NAME = "get_autoscaler_status"
AUTOSCALER_STATUS_DESC = (
    "Retrieve health, provider mode, operation counts, and registered node pools of the autoscaling subsystem."
)
AUTOSCALER_STATUS_SCHEMA = {
    "type": "object",
    "properties": {},
}

NODE_POOL_STATUS_NAME = "get_node_pool_status"
NODE_POOL_STATUS_DESC = (
    "Check instance counts, ready/pending state, and min/max limits for a specific Kubernetes node pool."
)
NODE_POOL_STATUS_SCHEMA = {
    "type": "object",
    "properties": {
        "node_pool": {
            "type": "string",
            "description": "Node pool identifier (default: 'default').",
            "default": "default",
        },
    },
}


def handle_get_autoscaler_status(
    provider: AutoscalerProvider,
    arguments: Dict[str, Any],
) -> Dict[str, Any]:
    """Execute get_autoscaler_status tool."""
    return provider.get_autoscaler_status()


def handle_get_node_pool_status(
    provider: AutoscalerProvider,
    arguments: Dict[str, Any],
) -> Dict[str, Any]:
    """Execute get_node_pool_status tool."""
    node_pool = str(arguments.get("node_pool") or "default").strip()
    status = provider.get_node_pool_status(node_pool)
    return status.to_dict()

