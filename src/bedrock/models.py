"""Data models and enums for Phase 4 Bedrock reasoning."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ActionType(str, Enum):
    """Allowlisted recovery action types."""
    NO_ACTION = "NO_ACTION"
    REQUEST_SCALE_UP = "REQUEST_SCALE_UP"


@dataclass
class RecoveryContext:
    """
    Structured, normalized facts passed from Sentinel to the AI reasoner.
    
    Contains only typed metrics, allowlisted fields, and sanitized strings.
    """
    agent_id: str
    pod_name: str
    namespace: str = "default"
    resource_requests: Dict[str, Any] = field(default_factory=dict)
    deterministic_diagnosis: Dict[str, Any] = field(default_factory=dict)
    cluster_capacity: Dict[str, Any] = field(default_factory=dict)
    available_node_pools: List[Dict[str, Any]] = field(default_factory=list)
    policy_constraints: Dict[str, Any] = field(default_factory=dict)
    events_summary: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "pod_name": self.pod_name,
            "namespace": self.namespace,
            "resource_requests": self.resource_requests,
            "deterministic_diagnosis": self.deterministic_diagnosis,
            "cluster_capacity": self.cluster_capacity,
            "available_node_pools": self.available_node_pools,
            "policy_constraints": self.policy_constraints,
            "events_summary": self.events_summary,
        }


@dataclass
class RecoveryProposal:
    """
    Structured recovery action proposal produced by AI reasoning or deterministic fallback.
    
    Note: Bedrock only proposes. The proposal must be validated and authorized
    by the RecoveryPolicyEngine before any execution occurs.
    """
    diagnosis: str
    action: ActionType
    parameters: Dict[str, Any]
    confidence: float
    explanation: str
    reasoning_source: str  # "bedrock" | "deterministic_fallback"
    bedrock_status: str = "AVAILABLE"  # "AVAILABLE" | "UNAVAILABLE" | "TIMEOUT" | "ERROR"
    bedrock_error: Optional[str] = None
    latency_ms: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "diagnosis": self.diagnosis,
            "action": self.action.value if isinstance(self.action, ActionType) else str(self.action),
            "parameters": self.parameters,
            "confidence": self.confidence,
            "explanation": self.explanation,
            "reasoning_source": self.reasoning_source,
            "bedrock_status": self.bedrock_status,
            "bedrock_error": self.bedrock_error,
            "latency_ms": self.latency_ms,
        }

