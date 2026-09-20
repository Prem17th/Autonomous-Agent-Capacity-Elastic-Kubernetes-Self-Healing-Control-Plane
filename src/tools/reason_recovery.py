"""MCP Tool handler: reason_recovery (AI-assisted bottleneck analysis & proposal)."""

from typing import Any, Dict, Optional

from src.autoscaler.provider import AutoscalerProvider
from src.bedrock.models import RecoveryContext, RecoveryProposal
from src.bedrock.orchestrator import SentinelRecoveryReasoner
from src.errors.exceptions import ValidationError
from src.kubernetes.adapter import KubernetesAdapter
from src.logger.logger import get_logger

logger = get_logger("tools.reason_recovery")

REASON_RECOVERY_NAME = "reason_recovery"
REASON_RECOVERY_DESC = (
    "Analyze an unschedulable Nasiko agent pod using AI reasoning (or deterministic fallback) "
    "to formulate a structured RecoveryProposal before submitting to the RecoveryPolicyEngine."
)
REASON_RECOVERY_SCHEMA = {
    "type": "object",
    "properties": {
        "pod_name": {
            "type": "string",
            "description": "Name of the unschedulable pod to analyze.",
        },
        "agent_id": {
            "type": "string",
            "description": "Optional Nasiko agent UUID.",
        },
        "namespace": {
            "type": "string",
            "description": "Optional Kubernetes namespace.",
        },
    },
    "required": ["pod_name"],
}


def handle_reason_recovery(
    adapter: KubernetesAdapter,
    autoscaler_provider: AutoscalerProvider,
    reasoner: SentinelRecoveryReasoner,
    arguments: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Execute reason_recovery tool.
    
    1. Collects structured facts (pod resources, diagnosis, node capacity, pools).
    2. Constructs RecoveryContext.
    3. Invokes SentinelRecoveryReasoner to produce a validated RecoveryProposal.
    """
    pod_name = arguments.get("pod_name")
    if not pod_name or not isinstance(pod_name, str) or not pod_name.strip():
        raise ValidationError("Field 'pod_name' is required and must be a non-empty string.")

    pod_name = pod_name.strip()
    namespace = str(arguments.get("namespace") or "default").strip()
    agent_id = arguments.get("agent_id")
    if agent_id:
        agent_id = str(agent_id).strip()
    else:
        agent_id = "unknown-agent"

    logger.info(f"Gathering structured facts for reason_recovery on pod '{pod_name}'")

    # 1. Deterministic Diagnosis
    diagnosis = adapter.diagnose_capacity(pod_name=pod_name, namespace=namespace)

    # 2. Cluster Capacity Summary
    cap_summary = adapter.get_node_capacity()

    # 3. Available Node Pools
    node_pools_list = [p.to_dict() for p in autoscaler_provider.list_node_pools()]

    # 4. Resource Requests
    all_pending = adapter.get_pending_pods(namespace=namespace)
    matched_pod = next((p for p in all_pending if p.pod_name == pod_name), None)
    
    if matched_pod:
        res_requests = matched_pod.resource_requests.to_dict()
        if not agent_id or agent_id == "unknown-agent":
            agent_id = matched_pod.owner_name or "unknown-agent"
    else:
        res_requests = {"cpu_milli": 500, "memory_bytes": 536870912, "raw_cpu": "500m", "raw_memory": "512Mi"}

    # 5. Events summary
    events = adapter.get_pod_events(pod_name=pod_name, namespace=namespace)
    events_summary = [f"[{e.reason}] {e.message}" for e in events]

    # Construct Context
    context = RecoveryContext(
        agent_id=agent_id,
        pod_name=pod_name,
        namespace=namespace,
        resource_requests=res_requests,
        deterministic_diagnosis=diagnosis.to_dict(),
        cluster_capacity=cap_summary.to_dict(),
        available_node_pools=node_pools_list,
        policy_constraints={
            "max_nodes_per_request": 2,
            "max_cluster_nodes": 10,
        },
        events_summary=events_summary,
    )

    # Evaluate Reasoner
    proposal = reasoner.evaluate(context)
    return proposal.to_dict()

