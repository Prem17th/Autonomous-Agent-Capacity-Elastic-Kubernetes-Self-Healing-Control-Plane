"""Tool implementation: diagnose_capacity."""

from typing import Any, Dict

from src.errors.exceptions import ValidationError
from src.kubernetes.adapter import KubernetesAdapter
from src.logger.logger import get_logger

logger = get_logger("tools.diagnosis")

TOOL_NAME = "diagnose_capacity"
TOOL_DESCRIPTION = "Deterministically analyze unschedulable/pending pods to classify capacity bottlenecks (insufficient_cpu, insufficient_memory, too_many_pods, resource_quota, taint_or_constraint, node_pool_constraint, or unknown)."
INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "pod_name": {
            "type": "string",
            "description": "Name of the pending/unschedulable pod to diagnose.",
        },
        "namespace": {
            "type": "string",
            "description": "Optional Kubernetes namespace (defaults to 'default').",
        },
    },
    "required": ["pod_name"],
}

DIAGNOSIS_NAME = TOOL_NAME
DIAGNOSIS_DESC = TOOL_DESCRIPTION
DIAGNOSIS_SCHEMA = INPUT_SCHEMA


def handle_diagnose_capacity(adapter: KubernetesAdapter, args: Dict[str, Any]) -> Dict[str, Any]:
    """Execute diagnose_capacity tool."""
    pod_name = args.get("pod_name")
    if not pod_name or not isinstance(pod_name, str):
        raise ValidationError("Missing or invalid 'pod_name' parameter", details={"pod_name": pod_name})

    namespace = args.get("namespace")
    diagnosis = adapter.diagnose_capacity(pod_name=pod_name.strip(), namespace=namespace)
    return diagnosis.to_dict()
