"""Mock Kubernetes object fixtures for testing."""

from typing import Any, Dict, List

# Standard Agent UUID
SAMPLE_AGENT_ID = "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d"
SAMPLE_NAMESPACE = "aegis-agents"

# 1. Agent Deployment Fixture (Running)
DEPLOYMENT_RUNNING: Dict[str, Any] = {
    "apiVersion": "apps/v1",
    "kind": "Deployment",
    "metadata": {
        "name": SAMPLE_AGENT_ID,
        "namespace": SAMPLE_NAMESPACE,
        "creationTimestamp": "2026-09-20T10:00:00Z",
        "labels": {
            "app.kubernetes.io/name": "sales-agent",
        },
    },
    "spec": {
        "replicas": 1,
    },
    "status": {
        "replicas": 1,
        "readyReplicas": 1,
        "updatedReplicas": 1,
        "availableReplicas": 1,
    },
}

# 2. Agent Deployment Fixture (Pending / Scale to 1 with 0 ready)
DEPLOYMENT_PENDING: Dict[str, Any] = {
    "apiVersion": "apps/v1",
    "kind": "Deployment",
    "metadata": {
        "name": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
        "namespace": SAMPLE_NAMESPACE,
        "creationTimestamp": "2026-09-20T10:05:00Z",
    },
    "spec": {
        "replicas": 1,
    },
    "status": {
        "replicas": 1,
        "readyReplicas": 0,
        "updatedReplicas": 1,
        "availableReplicas": 0,
    },
}

# 3. Pod Fixtures
POD_RUNNING: Dict[str, Any] = {
    "apiVersion": "v1",
    "kind": "Pod",
    "metadata": {
        "name": f"{SAMPLE_AGENT_ID}-7f989c9999-abcde",
        "namespace": SAMPLE_NAMESPACE,
        "creationTimestamp": "2026-09-20T10:00:05Z",
        "ownerReferences": [
            {"kind": "ReplicaSet", "name": f"{SAMPLE_AGENT_ID}-7f989c9999"}
        ],
    },
    "spec": {
        "nodeName": "node-worker-1",
        "containers": [
            {
                "name": "agent",
                "resources": {
                    "requests": {"cpu": "500m", "memory": "512Mi"},
                },
            }
        ],
    },
    "status": {
        "phase": "Running",
        "conditions": [
            {"type": "PodScheduled", "status": "True"},
            {"type": "Ready", "status": "True"},
        ],
    },
}

POD_PENDING_CPU: Dict[str, Any] = {
    "apiVersion": "v1",
    "kind": "Pod",
    "metadata": {
        "name": "agent-pending-cpu",
        "namespace": SAMPLE_NAMESPACE,
        "creationTimestamp": "2026-09-20T10:05:05Z",
        "ownerReferences": [
            {"kind": "ReplicaSet", "name": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11-54c74d89bc"}
        ],
    },
    "spec": {
        "containers": [
            {
                "name": "agent",
                "resources": {
                    "requests": {"cpu": "2000m", "memory": "1Gi"},
                },
            }
        ],
    },
    "status": {
        "phase": "Pending",
        "conditions": [
            {
                "type": "PodScheduled",
                "status": "False",
                "reason": "Unschedulable",
                "message": "0/2 nodes available: 2 Insufficient cpu.",
            }
        ],
    },
}

POD_PENDING_MEM: Dict[str, Any] = {
    "apiVersion": "v1",
    "kind": "Pod",
    "metadata": {
        "name": "agent-pending-mem",
        "namespace": SAMPLE_NAMESPACE,
        "creationTimestamp": "2026-09-20T10:06:00Z",
    },
    "spec": {
        "containers": [
            {
                "name": "agent",
                "resources": {
                    "requests": {"cpu": "500m", "memory": "16Gi"},
                },
            }
        ],
    },
    "status": {
        "phase": "Pending",
        "conditions": [
            {
                "type": "PodScheduled",
                "status": "False",
                "reason": "Unschedulable",
                "message": "0/2 nodes available: 2 Insufficient memory.",
            }
        ],
    },
}

POD_PENDING_TOO_MANY_PODS: Dict[str, Any] = {
    "apiVersion": "v1",
    "kind": "Pod",
    "metadata": {
        "name": "agent-pending-pods-limit",
        "namespace": SAMPLE_NAMESPACE,
        "creationTimestamp": "2026-09-20T10:07:00Z",
    },
    "spec": {
        "containers": [{"name": "agent", "resources": {"requests": {"cpu": "100m"}}}],
    },
    "status": {
        "phase": "Pending",
        "conditions": [
            {
                "type": "PodScheduled",
                "status": "False",
                "reason": "Unschedulable",
                "message": "0/2 nodes available: 2 Too many pods.",
            }
        ],
    },
}

POD_PENDING_QUOTA: Dict[str, Any] = {
    "apiVersion": "v1",
    "kind": "Pod",
    "metadata": {
        "name": "agent-pending-quota",
        "namespace": SAMPLE_NAMESPACE,
        "creationTimestamp": "2026-09-20T10:08:00Z",
    },
    "spec": {
        "containers": [{"name": "agent", "resources": {"requests": {"cpu": "500m"}}}],
    },
    "status": {
        "phase": "Pending",
        "conditions": [
            {
                "type": "PodScheduled",
                "status": "False",
                "reason": "Unschedulable",
                "message": "failed quota: compute-resources: exceeded quota: requests.cpu",
            }
        ],
    },
}

POD_PENDING_TAINT: Dict[str, Any] = {
    "apiVersion": "v1",
    "kind": "Pod",
    "metadata": {
        "name": "agent-pending-taint",
        "namespace": SAMPLE_NAMESPACE,
        "creationTimestamp": "2026-09-20T10:09:00Z",
    },
    "spec": {
        "containers": [{"name": "agent", "resources": {"requests": {"cpu": "500m"}}}],
    },
    "status": {
        "phase": "Pending",
        "conditions": [
            {
                "type": "PodScheduled",
                "status": "False",
                "reason": "Unschedulable",
                "message": "0/2 nodes available: 2 node(s) had untolerated taint {dedicated: gpu}.",
            }
        ],
    },
}

POD_PENDING_NODE_POOL: Dict[str, Any] = {
    "apiVersion": "v1",
    "kind": "Pod",
    "metadata": {
        "name": "agent-pending-nodepool",
        "namespace": SAMPLE_NAMESPACE,
        "creationTimestamp": "2026-09-20T10:10:00Z",
    },
    "spec": {
        "containers": [{"name": "agent", "resources": {"requests": {"cpu": "500m"}}}],
    },
    "status": {
        "phase": "Pending",
        "conditions": [
            {
                "type": "PodScheduled",
                "status": "False",
                "reason": "Unschedulable",
                "message": "0/2 nodes available: 2 node(s) didn't match Pod's node selector {karpenter.sh/nodepool: compute-optimized}.",
            }
        ],
    },
}

POD_PENDING_UNKNOWN: Dict[str, Any] = {
    "apiVersion": "v1",
    "kind": "Pod",
    "metadata": {
        "name": "agent-pending-unknown",
        "namespace": SAMPLE_NAMESPACE,
        "creationTimestamp": "2026-09-20T10:11:00Z",
    },
    "spec": {
        "containers": [{"name": "agent", "resources": {"requests": {"cpu": "100m", "memory": "100Mi"}}}],
    },
    "status": {
        "phase": "Pending",
        "conditions": [
            {
                "type": "PodScheduled",
                "status": "False",
                "reason": "Unschedulable",
                "message": "custom scheduling filter rejected pod placement",
            }
        ],
    },
}

# 4. Events Fixtures
EVENTS_LIST: List[Dict[str, Any]] = [
    {
        "metadata": {"name": "evt-1", "namespace": SAMPLE_NAMESPACE, "creationTimestamp": "2026-09-20T10:05:06Z"},
        "involvedObject": {"kind": "Pod", "name": "agent-pending-cpu", "namespace": SAMPLE_NAMESPACE},
        "reason": "FailedScheduling",
        "message": "0/2 nodes available: 2 Insufficient cpu. preemption: 0/2 nodes are available",
        "source": {"component": "default-scheduler"},
        "count": 5,
        "lastTimestamp": "2026-09-20T10:05:30Z",
    },
    {
        "metadata": {"name": "evt-2", "namespace": SAMPLE_NAMESPACE, "creationTimestamp": "2026-09-20T10:06:01Z"},
        "involvedObject": {"kind": "Pod", "name": "agent-pending-mem", "namespace": SAMPLE_NAMESPACE},
        "reason": "FailedScheduling",
        "message": "0/2 nodes available: 2 Insufficient memory.",
        "source": {"component": "default-scheduler"},
        "count": 3,
        "lastTimestamp": "2026-09-20T10:06:15Z",
    },
]

# 5. Nodes Fixtures
NODES_LIST: List[Dict[str, Any]] = [
    {
        "metadata": {
            "name": "node-worker-1",
            "labels": {
                "node.kubernetes.io/instance-type": "m5.large",
                "topology.kubernetes.io/zone": "us-west-2a",
                "karpenter.sh/nodepool": "default",
            },
        },
        "spec": {
            "taints": [],
        },
        "status": {
            "conditions": [{"type": "Ready", "status": "True"}],
            "allocatable": {"cpu": "1930m", "memory": "7800Mi", "pods": "110"},
            "capacity": {"cpu": "2000m", "memory": "8192Mi", "pods": "110"},
        },
    },
    {
        "metadata": {
            "name": "node-worker-2",
            "labels": {
                "node.kubernetes.io/instance-type": "m5.large",
                "topology.kubernetes.io/zone": "us-west-2b",
                "karpenter.sh/nodepool": "default",
            },
        },
        "spec": {
            "taints": [],
        },
        "status": {
            "conditions": [{"type": "Ready", "status": "True"}],
            "allocatable": {"cpu": "1930m", "memory": "7800Mi", "pods": "110"},
            "capacity": {"cpu": "2000m", "memory": "8192Mi", "pods": "110"},
        },
    },
]

