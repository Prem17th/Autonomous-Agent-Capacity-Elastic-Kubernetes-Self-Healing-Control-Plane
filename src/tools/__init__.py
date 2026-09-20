"""MCP Tools registry for Aegis Sentinel."""

from src.tools.agent_status import (
    AGENT_STATUS_DESC,
    AGENT_STATUS_NAME,
    AGENT_STATUS_SCHEMA,
    handle_get_agent_status,
)
from src.tools.autoscaler_status import (
    AUTOSCALER_STATUS_DESC,
    AUTOSCALER_STATUS_NAME,
    AUTOSCALER_STATUS_SCHEMA,
    NODE_POOL_STATUS_DESC,
    NODE_POOL_STATUS_NAME,
    NODE_POOL_STATUS_SCHEMA,
    handle_get_autoscaler_status,
    handle_get_node_pool_status,
)
from src.tools.diagnosis import (
    DIAGNOSIS_DESC,
    DIAGNOSIS_NAME,
    DIAGNOSIS_SCHEMA,
    handle_diagnose_capacity,
)
from src.tools.node_capacity import (
    NODE_CAPACITY_DESC,
    NODE_CAPACITY_NAME,
    NODE_CAPACITY_SCHEMA,
    handle_get_node_capacity,
)
from src.tools.pending_pods import (
    PENDING_PODS_DESC,
    PENDING_PODS_NAME,
    PENDING_PODS_SCHEMA,
    handle_get_pending_pods,
)
from src.tools.pod_events import (
    POD_EVENTS_DESC,
    POD_EVENTS_NAME,
    POD_EVENTS_SCHEMA,
    handle_get_pod_events,
)
from src.tools.reason_recovery import (
    REASON_RECOVERY_DESC,
    REASON_RECOVERY_NAME,
    REASON_RECOVERY_SCHEMA,
    handle_reason_recovery,
)
from src.tools.recovery_status import (
    RECOVERY_STATUS_DESC,
    RECOVERY_STATUS_NAME,
    RECOVERY_STATUS_SCHEMA,
    handle_get_recovery_status,
)
from src.tools.request_scale_up import (
    REQUEST_SCALE_UP_DESC,
    REQUEST_SCALE_UP_NAME,
    REQUEST_SCALE_UP_SCHEMA,
    handle_request_scale_up,
)
from src.tools.retry_agent import (
    RETRY_AGENT_DESC,
    RETRY_AGENT_NAME,
    RETRY_AGENT_SCHEMA,
    handle_retry_agent,
)
from src.tools.verify_recovery import (
    VERIFY_RECOVERY_DESC,
    VERIFY_RECOVERY_NAME,
    VERIFY_RECOVERY_SCHEMA,
    handle_verify_agent_recovery,
)
from src.tools.wait_for_capacity import (
    WAIT_FOR_CAPACITY_DESC,
    WAIT_FOR_CAPACITY_NAME,
    WAIT_FOR_CAPACITY_SCHEMA,
    handle_wait_for_capacity,
)

__all__ = [
    # Phase 2 Observation & Diagnosis Tools
    "AGENT_STATUS_NAME",
    "AGENT_STATUS_DESC",
    "AGENT_STATUS_SCHEMA",
    "handle_get_agent_status",
    "PENDING_PODS_NAME",
    "PENDING_PODS_DESC",
    "PENDING_PODS_SCHEMA",
    "handle_get_pending_pods",
    "POD_EVENTS_NAME",
    "POD_EVENTS_DESC",
    "POD_EVENTS_SCHEMA",
    "handle_get_pod_events",
    "NODE_CAPACITY_NAME",
    "NODE_CAPACITY_DESC",
    "NODE_CAPACITY_SCHEMA",
    "handle_get_node_capacity",
    "DIAGNOSIS_NAME",
    "DIAGNOSIS_DESC",
    "DIAGNOSIS_SCHEMA",
    "handle_diagnose_capacity",
    # Phase 3 Autoscaling & Recovery Tools
    "REQUEST_SCALE_UP_NAME",
    "REQUEST_SCALE_UP_DESC",
    "REQUEST_SCALE_UP_SCHEMA",
    "handle_request_scale_up",
    "WAIT_FOR_CAPACITY_NAME",
    "WAIT_FOR_CAPACITY_DESC",
    "WAIT_FOR_CAPACITY_SCHEMA",
    "handle_wait_for_capacity",
    "AUTOSCALER_STATUS_NAME",
    "AUTOSCALER_STATUS_DESC",
    "AUTOSCALER_STATUS_SCHEMA",
    "handle_get_autoscaler_status",
    "NODE_POOL_STATUS_NAME",
    "NODE_POOL_STATUS_DESC",
    "NODE_POOL_STATUS_SCHEMA",
    "handle_get_node_pool_status",
    "RECOVERY_STATUS_NAME",
    "RECOVERY_STATUS_DESC",
    "RECOVERY_STATUS_SCHEMA",
    "handle_get_recovery_status",
    "VERIFY_RECOVERY_NAME",
    "VERIFY_RECOVERY_DESC",
    "VERIFY_RECOVERY_SCHEMA",
    "handle_verify_agent_recovery",
    "RETRY_AGENT_NAME",
    "RETRY_AGENT_DESC",
    "RETRY_AGENT_SCHEMA",
    "handle_retry_agent",
    # Phase 4 Bedrock AI Reasoning Tool
    "REASON_RECOVERY_NAME",
    "REASON_RECOVERY_DESC",
    "REASON_RECOVERY_SCHEMA",
    "handle_reason_recovery",
]
