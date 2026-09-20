"""Normalized Kubernetes data models for Nasiko Sentinel."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def parse_cpu_milli(cpu_str: Optional[str]) -> int:
    """Parse Kubernetes CPU quantity (e.g. '500m', '2', '0.5') to millicores."""
    if not cpu_str:
        return 0
    cpu_str = str(cpu_str).strip()
    if cpu_str.endswith("m"):
        try:
            return int(cpu_str[:-1])
        except ValueError:
            return 0
    try:
        return int(float(cpu_str) * 1000)
    except ValueError:
        return 0


def parse_memory_bytes(mem_str: Optional[str]) -> int:
    """Parse Kubernetes Memory quantity (e.g. '512Mi', '1Gi', '2048M', bare bytes) to integer bytes."""
    if not mem_str:
        return 0
    mem_str = str(mem_str).strip()

    multipliers = {
        "Ki": 1024,
        "Mi": 1024**2,
        "Gi": 1024**3,
        "Ti": 1024**4,
        "Pi": 1024**5,
        "Ei": 1024**6,
        "k": 1000,
        "M": 1000**2,
        "G": 1000**3,
        "T": 1000**4,
        "P": 1000**5,
        "E": 1000**6,
    }

    for suffix, mult in multipliers.items():
        if mem_str.endswith(suffix):
            num_part = mem_str[: -len(suffix)].strip()
            try:
                return int(float(num_part) * mult)
            except ValueError:
                return 0

    try:
        return int(mem_str)
    except ValueError:
        return 0


@dataclass
class ResourceRequests:
    """Normalized CPU and Memory resource requests."""

    cpu_milli: int = 0
    memory_bytes: int = 0
    raw_cpu: str = "0m"
    raw_memory: str = "0Mi"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cpu_milli": self.cpu_milli,
            "memory_bytes": self.memory_bytes,
            "raw_cpu": self.raw_cpu,
            "raw_memory": self.raw_memory,
        }


@dataclass
class NormalizedPod:
    """Normalized representation of a Kubernetes Pod."""

    pod_name: str
    namespace: str
    phase: str  # Pending, Running, Succeeded, Failed, Unknown
    scheduled: bool
    ready: bool
    resource_requests: ResourceRequests
    creation_timestamp: str
    node_name: Optional[str] = None
    labels: Dict[str, str] = field(default_factory=dict)
    owner_kind: Optional[str] = None
    owner_name: Optional[str] = None
    unschedulable_reason: Optional[str] = None
    unschedulable_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pod_name": self.pod_name,
            "namespace": self.namespace,
            "phase": self.phase,
            "scheduled": self.scheduled,
            "ready": self.ready,
            "resource_requests": self.resource_requests.to_dict(),
            "creation_timestamp": self.creation_timestamp,
            "node_name": self.node_name,
            "labels": self.labels,
            "owner_kind": self.owner_kind,
            "owner_name": self.owner_name,
            "unschedulable_reason": self.unschedulable_reason,
            "unschedulable_message": self.unschedulable_message,
        }


@dataclass
class NormalizedEvent:
    """Normalized representation of a Kubernetes Event."""

    event_name: str
    namespace: str
    reason: str
    message: str
    event_timestamp: str
    involved_kind: str
    involved_name: str
    component: str
    count: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_name": self.event_name,
            "namespace": self.namespace,
            "reason": self.reason,
            "message": self.message,
            "event_timestamp": self.event_timestamp,
            "involved_kind": self.involved_kind,
            "involved_name": self.involved_name,
            "component": self.component,
            "count": self.count,
        }


@dataclass
class NormalizedNode:
    """Normalized representation of a Kubernetes Node."""

    node_name: str
    ready: bool
    allocatable_cpu_milli: int
    allocatable_memory_bytes: int
    capacity_cpu_milli: int
    capacity_memory_bytes: int
    requested_cpu_milli: int = 0
    requested_memory_bytes: int = 0
    allocatable_pods: int = 110
    requested_pods: int = 0
    taints: List[Dict[str, Any]] = field(default_factory=list)
    node_pool_labels: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        available_cpu = max(0, self.allocatable_cpu_milli - self.requested_cpu_milli)
        available_mem = max(0, self.allocatable_memory_bytes - self.requested_memory_bytes)
        return {
            "node_name": self.node_name,
            "ready": self.ready,
            "allocatable_cpu_milli": self.allocatable_cpu_milli,
            "allocatable_memory_bytes": self.allocatable_memory_bytes,
            "requested_cpu_milli": self.requested_cpu_milli,
            "requested_memory_bytes": self.requested_memory_bytes,
            "available_cpu_milli": available_cpu,
            "available_memory_bytes": available_mem,
            "allocatable_pods": self.allocatable_pods,
            "requested_pods": self.requested_pods,
            "available_pods": max(0, self.allocatable_pods - self.requested_pods),
            "taints": self.taints,
            "node_pool_labels": self.node_pool_labels,
        }


@dataclass
class NormalizedDeployment:
    """Normalized representation of a Kubernetes Deployment (representing a Nasiko agent)."""

    deployment_name: str
    namespace: str
    replicas: int
    ready_replicas: int
    updated_replicas: int
    available_replicas: int
    status: str  # Pending, Running, Degraded, Stopped
    agent_id: Optional[str]
    creation_timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "deployment_name": self.deployment_name,
            "namespace": self.namespace,
            "replicas": self.replicas,
            "ready_replicas": self.ready_replicas,
            "updated_replicas": self.updated_replicas,
            "available_replicas": self.available_replicas,
            "status": self.status,
            "agent_id": self.agent_id,
            "creation_timestamp": self.creation_timestamp,
        }


@dataclass
class CapacitySummary:
    """Cluster-wide capacity and resource allocation summary."""

    total_nodes: int
    ready_nodes: int
    total_allocatable_cpu_milli: int
    total_requested_cpu_milli: int
    total_allocatable_memory_bytes: int
    total_requested_memory_bytes: int
    total_allocatable_pods: int
    total_requested_pods: int
    nodes: List[NormalizedNode]

    def to_dict(self) -> Dict[str, Any]:
        available_cpu = max(0, self.total_allocatable_cpu_milli - self.total_requested_cpu_milli)
        available_mem = max(0, self.total_allocatable_memory_bytes - self.total_requested_memory_bytes)
        return {
            "total_nodes": self.total_nodes,
            "ready_nodes": self.ready_nodes,
            "total_allocatable_cpu_milli": self.total_allocatable_cpu_milli,
            "total_requested_cpu_milli": self.total_requested_cpu_milli,
            "available_cpu_milli": available_cpu,
            "total_allocatable_memory_bytes": self.total_allocatable_memory_bytes,
            "total_requested_memory_bytes": self.total_requested_memory_bytes,
            "available_memory_bytes": available_mem,
            "total_allocatable_pods": self.total_allocatable_pods,
            "total_requested_pods": self.total_requested_pods,
            "available_pods": max(0, self.total_allocatable_pods - self.total_requested_pods),
            "nodes": [n.to_dict() for n in self.nodes],
        }


@dataclass
class DiagnosisResult:
    """Deterministic capacity and scheduling diagnosis result."""

    classification: str  # insufficient_cpu, insufficient_memory, too_many_pods, resource_quota, taint_or_constraint, node_pool_constraint, unknown
    reason: str
    message: str
    target_pod: Optional[str]
    namespace: str
    details: Dict[str, Any]
    suggested_action: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "classification": self.classification,
            "reason": self.reason,
            "message": self.message,
            "target_pod": self.target_pod,
            "namespace": self.namespace,
            "details": self.details,
            "suggested_action": self.suggested_action,
        }

