"""Kubernetes adapter providing high-level normalized queries and diagnosis."""

import re
from typing import Any, Dict, List, Optional

from src.errors.exceptions import InfrastructureError, ValidationError
from src.kubernetes.client import BaseKubeClient
from src.kubernetes.models import (
    CapacitySummary,
    DiagnosisResult,
    NormalizedDeployment,
    NormalizedEvent,
    NormalizedNode,
    NormalizedPod,
    ResourceRequests,
    parse_cpu_milli,
    parse_memory_bytes,
)
from src.logger.logger import get_logger

logger = get_logger("kubernetes.adapter")


class KubernetesAdapter:
    """High-level adapter for inspecting Kubernetes workloads, capacity, and scheduling."""

    def __init__(self, client: BaseKubeClient) -> None:
        self.client = client

    def check_connection(self) -> bool:
        """Verify cluster connectivity."""
        return self.client.is_connected()

    # ─── 1. Agent & Deployment Normalization ─────────────────────────────────

    def get_agent_status(self, agent_id: str, namespace: Optional[str] = None) -> Optional[NormalizedDeployment]:
        """
        Query deployment status for a Nasiko agent.
        Per verified Nasiko contract, deployment is named with the agent UUID.
        """
        if not agent_id or not isinstance(agent_id, str):
            raise ValidationError("agent_id must be a non-empty string", details={"agent_id": agent_id})

        raw_dep = self.client.get_deployment(name=agent_id.strip(), namespace=namespace or "default")
        if not raw_dep:
            return None

        spec = raw_dep.get("spec", {})
        status = raw_dep.get("status", {})
        meta = raw_dep.get("metadata", {})

        replicas = spec.get("replicas", 1)
        ready_replicas = status.get("readyReplicas", 0)
        updated_replicas = status.get("updatedReplicas", 0)
        available_replicas = status.get("availableReplicas", 0)

        if replicas == 0:
            lifecycle_status = "Stopped"
        elif ready_replicas >= replicas:
            lifecycle_status = "Running"
        elif ready_replicas == 0 and available_replicas == 0:
            lifecycle_status = "Pending"
        else:
            lifecycle_status = "Degraded"

        return NormalizedDeployment(
            deployment_name=meta.get("name", agent_id),
            namespace=meta.get("namespace", "default"),
            replicas=replicas,
            ready_replicas=ready_replicas,
            updated_replicas=updated_replicas,
            available_replicas=available_replicas,
            status=lifecycle_status,
            agent_id=agent_id,
            creation_timestamp=meta.get("creationTimestamp", ""),
        )

    # ─── 2. Pod Normalization ───────────────────────────────────────────────

    def normalize_pod(self, raw_pod: Dict[str, Any]) -> NormalizedPod:
        """Convert a raw Kubernetes Pod dictionary to NormalizedPod."""
        meta = raw_pod.get("metadata", {})
        spec = raw_pod.get("spec", {})
        status = raw_pod.get("status", {})

        phase = status.get("phase", "Unknown")
        conditions = status.get("conditions", [])

        scheduled = True
        ready = False
        unschedulable_reason = None
        unschedulable_message = None

        for cond in conditions:
            c_type = cond.get("type")
            c_status = cond.get("status")
            if c_type == "PodScheduled":
                scheduled = (c_status == "True")
                if not scheduled:
                    unschedulable_reason = cond.get("reason")
                    unschedulable_message = cond.get("message")
            elif c_type == "Ready":
                ready = (c_status == "True")

        # Sum resource requests across all containers
        total_cpu = 0
        total_mem = 0
        containers = spec.get("containers", [])
        for c in containers:
            reqs = c.get("resources", {}).get("requests", {})
            total_cpu += parse_cpu_milli(reqs.get("cpu"))
            total_mem += parse_memory_bytes(reqs.get("memory"))

        owner_references = meta.get("ownerReferences", [])
        owner_kind = owner_references[0].get("kind") if owner_references else None
        owner_name = owner_references[0].get("name") if owner_references else None

        return NormalizedPod(
            pod_name=meta.get("name", ""),
            namespace=meta.get("namespace", "default"),
            phase=phase,
            scheduled=scheduled,
            ready=ready,
            resource_requests=ResourceRequests(
                cpu_milli=total_cpu,
                memory_bytes=total_mem,
                raw_cpu=f"{total_cpu}m",
                raw_memory=f"{total_mem // (1024**2)}Mi",
            ),
            creation_timestamp=meta.get("creationTimestamp", ""),
            node_name=spec.get("nodeName"),
            labels=meta.get("labels", {}),
            owner_kind=owner_kind,
            owner_name=owner_name,
            unschedulable_reason=unschedulable_reason,
            unschedulable_message=unschedulable_message,
        )

    def get_pending_pods(self, namespace: Optional[str] = None) -> List[NormalizedPod]:
        """List pods in Pending state or with PodScheduled=False."""
        raw_pods = self.client.list_pods(namespace=namespace)
        pending = []
        for raw in raw_pods:
            norm = self.normalize_pod(raw)
            if norm.phase == "Pending" or not norm.scheduled:
                pending.append(norm)
        return pending

    def get_pod(self, name: str, namespace: Optional[str] = None) -> Optional[NormalizedPod]:
        """Get a single normalized pod."""
        raw = self.client.get_pod(name=name, namespace=namespace or "default")
        return self.normalize_pod(raw) if raw else None

    # ─── 3. Event Normalization ─────────────────────────────────────────────

    def get_pod_events(self, pod_name: str, namespace: Optional[str] = None) -> List[NormalizedEvent]:
        """Get scheduling and lifecycle events for a specific pod."""
        if not pod_name or not isinstance(pod_name, str):
            raise ValidationError("pod_name must be a non-empty string", details={"pod_name": pod_name})

        raw_events = self.client.list_events(namespace=namespace)
        events = []
        for raw in raw_events:
            inv = raw.get("involvedObject", {})
            if inv.get("kind") == "Pod" and inv.get("name") == pod_name:
                meta = raw.get("metadata", {})
                source = raw.get("source", {})
                events.append(
                    NormalizedEvent(
                        event_name=meta.get("name", ""),
                        namespace=meta.get("namespace", "default"),
                        reason=raw.get("reason", "Unknown"),
                        message=raw.get("message", ""),
                        event_timestamp=raw.get("lastTimestamp") or meta.get("creationTimestamp", ""),
                        involved_kind="Pod",
                        involved_name=pod_name,
                        component=source.get("component", "unknown"),
                        count=raw.get("count", 1),
                    )
                )
        # Sort newest first
        events.sort(key=lambda x: x.event_timestamp, reverse=True)
        return events

    # ─── 4. Node Capacity Calculation ───────────────────────────────────────

    def get_node_capacity(self) -> CapacitySummary:
        """Compute cluster allocatable capacity, current pod allocations, and available headroom."""
        raw_nodes = self.client.list_nodes()
        all_raw_pods = self.client.list_pods(namespace=None)

        # Map active pod requests to nodes
        node_requested_cpu: Dict[str, int] = {}
        node_requested_mem: Dict[str, int] = {}
        node_requested_pods: Dict[str, int] = {}

        for p in all_raw_pods:
            spec = p.get("spec", {})
            status = p.get("status", {})
            node_name = spec.get("nodeName")
            phase = status.get("phase")

            if node_name and phase not in ("Succeeded", "Failed"):
                node_requested_pods[node_name] = node_requested_pods.get(node_name, 0) + 1
                for c in spec.get("containers", []):
                    reqs = c.get("resources", {}).get("requests", {})
                    node_requested_cpu[node_name] = (
                        node_requested_cpu.get(node_name, 0) + parse_cpu_milli(reqs.get("cpu"))
                    )
                    node_requested_mem[node_name] = (
                        node_requested_mem.get(node_name, 0) + parse_memory_bytes(reqs.get("memory"))
                    )

        nodes: List[NormalizedNode] = []
        total_allocatable_cpu = 0
        total_requested_cpu = 0
        total_allocatable_mem = 0
        total_requested_mem = 0
        total_allocatable_pods = 0
        total_requested_pods = 0
        ready_node_count = 0

        for raw_n in raw_nodes:
            meta = raw_n.get("metadata", {})
            status = raw_n.get("status", {})
            spec = raw_n.get("spec", {})
            node_name = meta.get("name", "")

            # Check Ready condition
            ready = False
            for cond in status.get("conditions", []):
                if cond.get("type") == "Ready" and cond.get("status") == "True":
                    ready = True
                    break

            if ready:
                ready_node_count += 1

            alloc = status.get("allocatable", {})
            cap = status.get("capacity", {})

            alloc_cpu = parse_cpu_milli(alloc.get("cpu"))
            alloc_mem = parse_memory_bytes(alloc.get("memory"))
            alloc_pods = int(alloc.get("pods", 110))

            cap_cpu = parse_cpu_milli(cap.get("cpu"))
            cap_mem = parse_memory_bytes(cap.get("memory"))

            req_cpu = node_requested_cpu.get(node_name, 0)
            req_mem = node_requested_mem.get(node_name, 0)
            req_pods = node_requested_pods.get(node_name, 0)

            total_allocatable_cpu += alloc_cpu
            total_requested_cpu += req_cpu
            total_allocatable_mem += alloc_mem
            total_requested_mem += req_mem
            total_allocatable_pods += alloc_pods
            total_requested_pods += req_pods

            # Extract relevant node pool labels
            labels = meta.get("labels", {})
            node_pool_labels = {
                k: v for k, v in labels.items()
                if any(k.startswith(p) for p in (
                    "node.kubernetes.io/instance-type",
                    "karpenter.sh/nodepool",
                    "eks.amazonaws.com/nodegroup",
                    "topology.kubernetes.io/zone",
                ))
            }

            nodes.append(
                NormalizedNode(
                    node_name=node_name,
                    ready=ready,
                    allocatable_cpu_milli=alloc_cpu,
                    allocatable_memory_bytes=alloc_mem,
                    capacity_cpu_milli=cap_cpu,
                    capacity_memory_bytes=cap_mem,
                    requested_cpu_milli=req_cpu,
                    requested_memory_bytes=req_mem,
                    allocatable_pods=alloc_pods,
                    requested_pods=req_pods,
                    taints=spec.get("taints", []),
                    node_pool_labels=node_pool_labels,
                )
            )

        return CapacitySummary(
            total_nodes=len(nodes),
            ready_nodes=ready_node_count,
            total_allocatable_cpu_milli=total_allocatable_cpu,
            total_requested_cpu_milli=total_requested_cpu,
            total_allocatable_memory_bytes=total_allocatable_mem,
            total_requested_memory_bytes=total_requested_mem,
            total_allocatable_pods=total_allocatable_pods,
            total_requested_pods=total_requested_pods,
            nodes=nodes,
        )

    # ─── 5. Deterministic Capacity Diagnosis ────────────────────────────────

    def diagnose_capacity(self, pod_name: str, namespace: Optional[str] = None) -> DiagnosisResult:
        """
        Deterministically diagnose why a pod is unschedulable or pending.
        
        Classifies into one of:
        - insufficient_cpu
        - insufficient_memory
        - too_many_pods
        - resource_quota
        - taint_or_constraint
        - node_pool_constraint
        - unknown
        """
        if not pod_name or not isinstance(pod_name, str):
            raise ValidationError("pod_name must be a non-empty string", details={"pod_name": pod_name})

        ns = namespace or "default"
        pod = self.get_pod(name=pod_name, namespace=ns)
        if not pod:
            raise ValidationError(f"Pod '{pod_name}' was not found in namespace '{ns}'", details={"pod_name": pod_name, "namespace": ns})

        if pod.phase == "Running" and pod.scheduled:
            return DiagnosisResult(
                classification="unknown",
                reason="PodAlreadyScheduled",
                message=f"Pod '{pod_name}' is already scheduled and running on node '{pod.node_name}'",
                target_pod=pod_name,
                namespace=ns,
                details={"phase": pod.phase, "node": pod.node_name},
                suggested_action="No recovery action required; pod is healthy.",
            )

        events = self.get_pod_events(pod_name=pod_name, namespace=ns)
        scheduling_events = [e for e in events if e.reason == "FailedScheduling"]

        # Aggregate error messages from scheduler events and pod status conditions
        messages = [e.message for e in scheduling_events]
        if pod.unschedulable_message:
            messages.append(pod.unschedulable_message)
        combined_text = " ".join(messages).lower()

        cap_summary = self.get_node_capacity()

        # 1. Check for Insufficient CPU
        if "insufficient cpu" in combined_text or "0/N nodes available: insufficient cpu" in combined_text:
            return DiagnosisResult(
                classification="insufficient_cpu",
                reason="InsufficientCPU",
                message=f"Agent pod '{pod_name}' cannot be scheduled due to insufficient CPU capacity on all nodes.",
                target_pod=pod_name,
                namespace=ns,
                details={
                    "requested_cpu_milli": pod.resource_requests.cpu_milli,
                    "available_cluster_cpu_milli": max(0, cap_summary.total_allocatable_cpu_milli - cap_summary.total_requested_cpu_milli),
                    "raw_events": [e.message for e in scheduling_events],
                },
                suggested_action="Scale up node pool or provision additional compute capacity with sufficient CPU.",
            )

        # 2. Check for Insufficient Memory
        if "insufficient memory" in combined_text:
            return DiagnosisResult(
                classification="insufficient_memory",
                reason="InsufficientMemory",
                message=f"Agent pod '{pod_name}' cannot be scheduled due to insufficient memory capacity on all nodes.",
                target_pod=pod_name,
                namespace=ns,
                details={
                    "requested_memory_bytes": pod.resource_requests.memory_bytes,
                    "available_cluster_memory_bytes": max(0, cap_summary.total_allocatable_memory_bytes - cap_summary.total_requested_memory_bytes),
                    "raw_events": [e.message for e in scheduling_events],
                },
                suggested_action="Scale up node pool or provision nodes with larger memory allocation.",
            )

        # 3. Check for Too Many Pods
        if "too many pods" in combined_text or "exceeded pod limit" in combined_text:
            return DiagnosisResult(
                classification="too_many_pods",
                reason="TooManyPods",
                message=f"Agent pod '{pod_name}' cannot be scheduled because the maximum pod limit per node is reached.",
                target_pod=pod_name,
                namespace=ns,
                details={
                    "total_nodes": cap_summary.total_nodes,
                    "total_allocatable_pods": cap_summary.total_allocatable_pods,
                    "total_requested_pods": cap_summary.total_requested_pods,
                },
                suggested_action="Add additional worker nodes to increase cluster max-pod ceiling.",
            )

        # 4. Check for Resource Quota
        if "exceeded quota" in combined_text or "forbidden: exceeded quota" in combined_text:
            return DiagnosisResult(
                classification="resource_quota",
                reason="ResourceQuotaExceeded",
                message=f"Agent pod '{pod_name}' cannot be created because namespace '{ns}' resource quota is exceeded.",
                target_pod=pod_name,
                namespace=ns,
                details={"namespace": ns, "raw_events": [e.message for e in scheduling_events]},
                suggested_action="Increase ResourceQuota limits for the namespace or clean up inactive workloads.",
            )

        # 5. Check for Taints or Tolerations
        if "had untolerated taint" in combined_text or "taint" in combined_text:
            return DiagnosisResult(
                classification="taint_or_constraint",
                reason="UntoleratedTaint",
                message=f"Agent pod '{pod_name}' cannot be scheduled due to node taints not tolerated by the pod spec.",
                target_pod=pod_name,
                namespace=ns,
                details={"raw_events": [e.message for e in scheduling_events]},
                suggested_action="Adjust node taints or update agent pod tolerations.",
            )

        # 6. Check for Node Selector / Affinity / Node Pool Constraint
        if "match pod's node selector" in combined_text or "node affinity" in combined_text:
            return DiagnosisResult(
                classification="node_pool_constraint",
                reason="NodeSelectorMismatch",
                message=f"Agent pod '{pod_name}' requires specific node selectors or affinity that no active node matches.",
                target_pod=pod_name,
                namespace=ns,
                details={"raw_events": [e.message for e in scheduling_events]},
                suggested_action="Provision nodes matching required node-pool labels.",
            )

        # 7. Fallback capacity analysis against node summary
        largest_available_cpu = max(
            (max(0, n.allocatable_cpu_milli - n.requested_cpu_milli) for n in cap_summary.nodes if n.ready),
            default=0,
        )
        largest_available_mem = max(
            (max(0, n.allocatable_memory_bytes - n.requested_memory_bytes) for n in cap_summary.nodes if n.ready),
            default=0,
        )

        if pod.resource_requests.cpu_milli > 0 and pod.resource_requests.cpu_milli > largest_available_cpu:
            return DiagnosisResult(
                classification="insufficient_cpu",
                reason="NoSingleNodeHasEnoughCPU",
                message=f"Pod requires {pod.resource_requests.raw_cpu} CPU, but largest available node headroom is {largest_available_cpu}m.",
                target_pod=pod_name,
                namespace=ns,
                details={
                    "requested_cpu_milli": pod.resource_requests.cpu_milli,
                    "largest_available_node_cpu_milli": largest_available_cpu,
                },
                suggested_action="Provision a node with at least the requested CPU size.",
            )

        if pod.resource_requests.memory_bytes > 0 and pod.resource_requests.memory_bytes > largest_available_mem:
            return DiagnosisResult(
                classification="insufficient_memory",
                reason="NoSingleNodeHasEnoughMemory",
                message=f"Pod requires {pod.resource_requests.raw_memory} Memory, but largest available node headroom is {largest_available_mem // (1024**2)}Mi.",
                target_pod=pod_name,
                namespace=ns,
                details={
                    "requested_memory_bytes": pod.resource_requests.memory_bytes,
                    "largest_available_node_memory_bytes": largest_available_mem,
                },
                suggested_action="Provision a node with at least the requested memory size.",
            )

        # 8. Unclassified
        return DiagnosisResult(
            classification="unknown",
            reason="UnclassifiedSchedulingDelay",
            message=f"Pod '{pod_name}' is unscheduled without a recognized bottleneck keyword.",
            target_pod=pod_name,
            namespace=ns,
            details={
                "events_count": len(events),
                "messages": messages,
                "ready_nodes": cap_summary.ready_nodes,
            },
            suggested_action="Inspect pod description and cluster logs for non-standard scheduling constraints.",
        )

