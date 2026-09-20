"""Tool implementation: get_pod_events."""

from typing import Any, Dict

from src.errors.exceptions import ValidationError
from src.kubernetes.adapter import KubernetesAdapter
from src.logger.logger import get_logger

logger = get_logger("tools.pod_events")

TOOL_NAME = "get_pod_events"
TOOL_DESCRIPTION = "Retrieve Kubernetes scheduling and lifecycle events for a specific pod."
INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "pod_name": {
            "type": "string",
            "description": "Name of the Kubernetes pod to inspect.",
        },
        "namespace": {
            "type": "string",
            "description": "Optional Kubernetes namespace (defaults to 'default').",
        },
    },
    "required": ["pod_name"],
}

POD_EVENTS_NAME = TOOL_NAME
POD_EVENTS_DESC = TOOL_DESCRIPTION
POD_EVENTS_SCHEMA = INPUT_SCHEMA


def handle_get_pod_events(adapter: KubernetesAdapter, args: Dict[str, Any]) -> Dict[str, Any]:
    """Execute get_pod_events tool."""
    pod_name = args.get("pod_name")
    if not pod_name or not isinstance(pod_name, str):
        raise ValidationError("Missing or invalid 'pod_name' parameter", details={"pod_name": pod_name})

    namespace = args.get("namespace")
    events = adapter.get_pod_events(pod_name=pod_name.strip(), namespace=namespace)

    failed_scheduling_events = [e for e in events if e.reason == "FailedScheduling"]

    return {
        "pod_name": pod_name,
        "namespace": namespace or "default",
        "total_events": len(events),
        "failed_scheduling_count": len(failed_scheduling_events),
        "events": [e.to_dict() for e in events],
    }
