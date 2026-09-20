"""Tool implementation: get_node_capacity."""

from typing import Any, Dict

from src.kubernetes.adapter import KubernetesAdapter
from src.logger.logger import get_logger

logger = get_logger("tools.node_capacity")

TOOL_NAME = "get_node_capacity"
TOOL_DESCRIPTION = "Get cluster-wide and per-node allocatable capacity, current pod requests, and available compute headroom."
INPUT_SCHEMA = {
    "type": "object",
    "properties": {},
}

NODE_CAPACITY_NAME = TOOL_NAME
NODE_CAPACITY_DESC = TOOL_DESCRIPTION
NODE_CAPACITY_SCHEMA = INPUT_SCHEMA


def handle_get_node_capacity(adapter: KubernetesAdapter, args: Dict[str, Any]) -> Dict[str, Any]:
    """Execute get_node_capacity tool."""
    cap_summary = adapter.get_node_capacity()
    return cap_summary.to_dict()
