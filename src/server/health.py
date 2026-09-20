"""Health check and status reporting for Nasiko Sentinel."""

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from src.config.settings import Settings


def get_health_status(
    settings: Settings,
    k8s_connected: Optional[bool] = None,
    autoscaler_type: str = "simulated",
    reasoner_name: str = "mock_bedrock",
) -> Dict[str, Any]:
    """
    Generate health and readiness status.
    
    Clearly separates Sentinel service health from external dependency reachability.
    """
    if k8s_connected is True:
        k8s_dep_status = "connected"
        k8s_dep_detail = "Live Kubernetes API server is reachable."
    elif k8s_connected is False:
        k8s_dep_status = "unreachable"
        k8s_dep_detail = (
            "Live Kubernetes integration is implemented but has not yet been validated "
            "against a running Kubernetes cluster (offline/simulation mode active)."
        )
    else:
        k8s_dep_status = "unconfigured"
        k8s_dep_detail = "Cluster connection not evaluated."

    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "phase": 4,
        "components": {
            "config": "ready",
            "mcp_server_foundation": "ready",
            "deterministic_diagnosis": "ready",
            "controlled_autoscaling": "ready",
            "bedrock_reasoning": "ready",
        },
        "dependencies": {
            "kubernetes": {
                "status": k8s_dep_status,
                "detail": k8s_dep_detail,
            },
            "autoscaler": {
                "provider": autoscaler_type,
                "status": "ready",
                "detail": (
                    "Autoscaler provider abstraction initialized with simulated provider. "
                    "Production Karpenter/Cluster Autoscaler integration pending confirmation of demo cluster environment."
                ),
            },
            "bedrock": {
                "provider": reasoner_name,
                "model_id": settings.bedrock_model_id or "unconfigured",
                "mock_mode": settings.bedrock_mock_mode,
                "status": "ready",
                "detail": (
                    "Bedrock reasoning provider initialized with explicit deterministic fallback. "
                    "Live AWS Bedrock client available behind provider abstraction."
                ),
            },
        },
        "roadmap": {
            "phase_1": "foundation (completed)",
            "phase_2": "nasiko_kubernetes_observation (completed)",
            "phase_3": "controlled_autoscaling (completed)",
            "phase_4": "bedrock_reasoning (completed)",
            "phase_5": "dronahq_integration (planned)",
            "phase_6": "end_to_end_recovery (planned)",
        },
    }
