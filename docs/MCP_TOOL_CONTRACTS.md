# Nasiko Sentinel - MCP Tool Contracts & Specification

This document details the exact JSON-RPC 2.0 tool interface contracts exposed by the Nasiko Sentinel MCP Server in Phase 5 across both `stdio` and `Streamable HTTP` transports.

---

## Transport Specification (Phase 5)

- **Stdio Transport:** Communicates via standard I/O streams (`sys.stdin` / `sys.stdout`) with newline-delimited JSON-RPC 2.0 frames.
- **Streamable HTTP Transport:** Communicates via authenticated HTTP `POST http://<host>:<port>/mcp` using header-based authentication (`Authorization: Bearer <SENTINEL_API_KEY>` or `X-Sentinel-API-Key: <SENTINEL_API_KEY>`).

---

## Tool Index

| Tool Name | Phase | Category | Purpose |
| :--- | :--- | :--- | :--- |
| `get_health` | Phase 1 | Foundation | Check service health, dependency state, and roadmap status. |
| `get_agent_status` | Phase 2 | Observation | Query agent deployment (`Deployment/<agent_uuid>`) and pods. |
| `get_pending_pods` | Phase 2 | Observation | List unscheduled pods and normalized resource requests. |
| `get_pod_events` | Phase 2 | Observation | Retrieve scheduler events for a pod. |
| `get_node_capacity` | Phase 2 | Observation | Query cluster and node-level compute allocatables and headroom. |
| `diagnose_capacity` | Phase 2 | Diagnosis | Deterministically classify scheduling bottleneck root causes. |
| `request_scale_up` | Phase 3 | Autoscaling | Request additional capacity with safety policy validation. |
| `wait_for_capacity` | Phase 3 | Autoscaling | Poll until newly provisioned capacity reaches Ready state. |
| `get_autoscaler_status` | Phase 3 | Autoscaling | Retrieve autoscaler health, provider mode, and operation metrics. |
| `get_node_pool_status` | Phase 3 | Autoscaling | Query instance counts and limits for a node pool. |
| `get_recovery_status` | Phase 3 | Recovery | Retrieve audit trail and state machine status for agent recoveries. |
| `verify_agent_recovery`| Phase 3 | Verification | Confirm agent deployment and pod reached Running state. |
| `retry_agent` | Phase 3 | Auxiliary | Optional trigger for manual deployment reconciliation. |
| `reason_recovery` | Phase 4 | AI Reasoning | Formulate structured recovery proposals using Bedrock / deterministic fallback. |

---

## Tool 1: `get_health`
- **Description:** Returns service status, runtime environment, Phase 3 readiness, and Kubernetes/autoscaler dependency readiness.
- **Requires Kubernetes:** No (degrades gracefully).
- **Input Schema:**
  ```json
  {
    "type": "object",
    "properties": {}
  }
  ```
- **Success Output Schema:**
  ```json
  {
    "status": "ok",
    "service": "nasiko-sentinel",
    "version": "0.1.0",
    "environment": "development",
    "phase": 3,
    "components": {
      "config": "ready",
      "mcp_server_foundation": "ready",
      "deterministic_diagnosis": "ready",
      "controlled_autoscaling": "ready"
    },
    "dependencies": {
      "kubernetes": {
        "status": "connected | unreachable",
        "detail": "Live Kubernetes integration is implemented but has not yet been validated against a running Kubernetes cluster."
      },
      "autoscaler": {
        "provider": "simulated",
        "status": "ready",
        "detail": "Autoscaler provider abstraction initialized with simulated provider."
      }
    },
    "roadmap": {
      "phase_1": "foundation (completed)",
      "phase_2": "nasiko_kubernetes_observation (completed)",
      "phase_3": "controlled_autoscaling (completed)",
      "phase_4": "bedrock_reasoning (planned)",
      "phase_5": "dronahq_integration (planned)",
      "phase_6": "end_to_end_recovery (planned)"
    }
  }
  ```

---

## Tool 2: `get_agent_status`
- **Description:** Query status of a specific Nasiko agent workload and backing Kubernetes resources using verified Nasiko deployment mapping (`Deployment/<agent_uuid>`).
- **Input Schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "agent_id": { "type": "string", "description": "The RFC 4122 UUID v4 of the Nasiko agent." },
      "namespace": { "type": "string", "description": "Optional Kubernetes namespace." }
    },
    "required": ["agent_id"]
  }
  ```

---

## Tool 3: `get_pending_pods`
- **Description:** Lists pods in `Pending` state or with `PodScheduled=False` along with normalized resource requests.
- **Input Schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "namespace": { "type": "string", "description": "Optional Kubernetes namespace." }
    }
  }
  ```

---

## Tool 4: `get_pod_events`
- **Description:** Retrieves Kubernetes scheduling and lifecycle events for a specific pod.
- **Input Schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "pod_name": { "type": "string", "description": "Name of the Kubernetes pod." },
      "namespace": { "type": "string", "description": "Optional Kubernetes namespace." }
    },
    "required": ["pod_name"]
  }
  ```

---

## Tool 5: `get_node_capacity`
- **Description:** Returns cluster-wide and per-node allocatable capacity, current pod requests, and remaining headroom.
- **Input Schema:**
  ```json
  {
    "type": "object",
    "properties": {}
  }
  ```

---

## Tool 6: `diagnose_capacity`
- **Description:** Deterministically analyzes an unschedulable pod and classifies root-cause capacity exhaustion into deterministic categories for upstream reasoning.
- **Classifications:** `insufficient_cpu`, `insufficient_memory`, `too_many_pods`, `resource_quota`, `taint_or_constraint`, `node_pool_constraint`, `unknown`.
- **Input Schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "pod_name": { "type": "string", "description": "Name of the pending pod." },
      "namespace": { "type": "string", "description": "Optional Kubernetes namespace." }
    },
    "required": ["pod_name"]
  }
  ```

---

## Tool 7: `request_scale_up`
- **Description:** Safely requests additional Kubernetes compute nodes for a target node pool. Enforces safety policies (max 2 nodes per request, max 10 total cluster nodes, 120s cooldown debounce, rate limit 3 ops/15min).
- **Input Schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "node_pool": { "type": "string", "description": "Target node pool (default: 'default').", "default": "default" },
      "target_nodes": { "type": "integer", "description": "Number of new nodes (default 1, max 2).", "default": 1 },
      "requested_cpu": { "type": "string", "description": "Required CPU (e.g. '2000m')." },
      "requested_memory": { "type": "string", "description": "Required Memory (e.g. '4Gi')." },
      "reason": { "type": "string", "description": "Operational justification.", "default": "capacity_exhaustion" },
      "agent_id": { "type": "string", "description": "Optional agent UUID triggering this scale action." },
      "dry_run": { "type": "boolean", "description": "If true, validates policy without mutating infrastructure.", "default": false }
    }
  }
  ```
- **Success Output Example:**
  ```json
  {
    "scale_request_id": "scale-op-a1b2c3d4",
    "status": "ACCEPTED",
    "allowed": true,
    "node_pool": "default",
    "nodes_requested": 1,
    "current_ready_nodes": 2,
    "target_ready_nodes": 3,
    "created_at": "2026-09-20T10:15:00Z",
    "estimated_latency_seconds": 60,
    "provider": "simulated",
    "agent_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d"
  }
  ```
- **Policy Denied Output Example:**
  ```json
  {
    "scale_request_id": "scale-req-8f12a9b3",
    "status": "POLICY_DENIED",
    "allowed": false,
    "reason": "COOLDOWN_ACTIVE",
    "details": {
      "node_pool": "default",
      "cooldown_seconds": 120,
      "remaining_seconds": 45.2
    },
    "node_pool": "default",
    "nodes_requested": 1,
    "dry_run": false
  }
  ```

---

## Tool 8: `wait_for_capacity`
- **Description:** Non-blocking async/polling check that verifies newly requested capacity is Ready, allocatable, and without untolerated taints.
- **Input Schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "scale_request_id": { "type": "string", "description": "Correlation ID from request_scale_up." },
      "target_ready_nodes": { "type": "integer", "description": "Expected minimum total ready nodes count." },
      "timeout_seconds": { "type": "integer", "description": "Timeout in seconds (default 180, max 300).", "default": 180 },
      "poll_interval_seconds": { "type": "number", "description": "Interval between polling checks (default 2.0).", "default": 2.0 },
      "agent_id": { "type": "string", "description": "Optional agent UUID for recovery tracking." }
    }
  }
  ```
- **Success Output Example:**
  ```json
  {
    "status": "READY",
    "operation_id": "scale-op-a1b2c3d4",
    "ready_nodes_count": 3,
    "provisioned_nodes": [
      {
        "node_name": "sentinel-sim-default-f92e10",
        "node_pool": "default",
        "instance_type": "t3.xlarge",
        "allocatable_cpu_milli": 4000,
        "allocatable_memory_bytes": 17179869184,
        "ready": true,
        "taints": [],
        "joined_at": "2026-09-20T10:15:45Z"
      }
    ],
    "elapsed_seconds": 45.2
  }
  ```

---

## Tool 9: `get_autoscaler_status`
- **Description:** Retrieve health, provider mode, operation counts, and registered node pools of the autoscaling subsystem.
- **Input Schema:**
  ```json
  {
    "type": "object",
    "properties": {}
  }
  ```
- **Success Output Example:**
  ```json
  {
    "status": "HEALTHY",
    "provider": "simulated",
    "mode": "simulation",
    "active_operations_count": 0,
    "completed_operations_count": 5,
    "failed_operations_count": 0,
    "total_operations_count": 5,
    "configured_node_pools": ["default", "general-compute", "memory-optimized"],
    "timestamp": "2026-09-20T10:20:00Z"
  }
  ```

---

## Tool 10: `get_node_pool_status`
- **Description:** Check instance counts, ready/pending state, and min/max limits for a specific Kubernetes node pool.
- **Input Schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "node_pool": { "type": "string", "description": "Node pool identifier.", "default": "default" }
    }
  }
  ```
- **Success Output Example:**
  ```json
  {
    "node_pool": "default",
    "current_nodes": 3,
    "ready_nodes": 3,
    "pending_nodes": 0,
    "min_nodes": 1,
    "max_nodes": 10,
    "instance_types": ["t3.xlarge", "m5.xlarge"],
    "status": "Ready",
    "updated_at": "2026-09-20T10:20:00Z"
  }
  ```

---

## Tool 11: `get_recovery_status`
- **Description:** Retrieve audit history, state machine status, and resolution timestamps for Nasiko agent recoveries.
- **Input Schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "recovery_id": { "type": "string", "description": "Optional specific recovery operation identifier." },
      "agent_id": { "type": "string", "description": "Optional Nasiko agent UUID." }
    }
  }
  ```
- **Success Output Example:**
  ```json
  {
    "found": true,
    "recovery": {
      "recovery_id": "rec-7c1b82aa",
      "agent_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
      "pod_name": "agent-pending-cpu",
      "initial_state": "DETECTED",
      "current_state": "RUNNING",
      "scale_request_id": "scale-op-a1b2c3d4",
      "diagnosis_reason": "insufficient_cpu",
      "history": [
        { "state": "DETECTED", "timestamp": "2026-09-20T10:14:00Z" },
        { "state": "SCALE_REQUESTED", "timestamp": "2026-09-20T10:15:00Z" },
        { "state": "PROVISIONING", "timestamp": "2026-09-20T10:15:05Z" },
        { "state": "CAPACITY_READY", "timestamp": "2026-09-20T10:15:45Z" },
        { "state": "RUNNING", "timestamp": "2026-09-20T10:16:10Z" }
      ],
      "created_at": "2026-09-20T10:14:00Z",
      "updated_at": "2026-09-20T10:16:10Z",
      "resolved_at": "2026-09-20T10:16:10Z"
    }
  }
  ```

---

## Tool 12: `verify_agent_recovery`
- **Description:** Verify whether a previously stalled Nasiko agent has successfully scheduled, reached `Running` status, and has ready replicas serving traffic.
- **Input Schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "agent_id": { "type": "string", "description": "RFC 4122 UUID v4 of the Nasiko agent." },
      "namespace": { "type": "string", "description": "Optional Kubernetes namespace." }
    },
    "required": ["agent_id"]
  }
  ```
- **Success Output Example:**
  ```json
  {
    "agent_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
    "recovered": true,
    "status": "Running",
    "ready_replicas": 1,
    "replicas": 1,
    "port": 8000,
    "created_at": "2026-09-20T10:00:00Z",
    "message": "Nasiko agent workload is healthy, fully scheduled, and actively running."
  }
  ```

---

## Tool 13: `retry_agent` (Auxiliary / Secondary Tool)
- **Description:** Optional auxiliary tool to trigger reconciliation or restart of a stalled Nasiko agent deployment.
- **Input Schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "agent_id": { "type": "string", "description": "RFC 4122 UUID v4 of the Nasiko agent." },
      "namespace": { "type": "string", "description": "Optional Kubernetes namespace." }
    },
    "required": ["agent_id"]
  }
  ```
- **Success Output Example:**
  ```json
  {
    "agent_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
    "reconciliation_triggered": true,
    "method": "deployment_reconciliation",
    "deployment_name": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
    "current_status": "Pending",
    "timestamp": "2026-09-20T10:16:00Z",
    "message": "Deployment reconciliation noted. Default scheduler will assign pod to ready nodes."
  }
  ```

---

## Tool 14: `reason_recovery`
- **Description:** Synthesizes deterministic Kubernetes capacity diagnostics and cluster headroom into a structured action proposal (`RecoveryProposal`) using AWS Bedrock Claude models (or explicit deterministic fallback). All proposals are subjected to P0 schema validation and remain strictly subject to the authoritative Recovery Policy Engine before execution.
- **Allowed Actions (P0):** `NO_ACTION`, `REQUEST_SCALE_UP`.
- **Input Schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "agent_id": { "type": "string", "description": "Optional Nasiko agent UUID." },
      "pod_name": { "type": "string", "description": "Name of the unschedulable pod." },
      "namespace": { "type": "string", "description": "Kubernetes namespace (default: default).", "default": "default" },
      "deterministic_diagnosis": {
        "type": "object",
        "description": "Output object from diagnose_capacity.",
        "properties": {
          "classification": { "type": "string" },
          "primary_reason": { "type": "string" },
          "message": { "type": "string" }
        }
      },
      "force_fallback": { "type": "boolean", "description": "Force deterministic fallback reasoning for testing/reliability.", "default": false }
    },
    "required": ["pod_name"]
  }
  ```
- **Success Output Example (Bedrock Reasoning):**
  ```json
  {
    "action": "REQUEST_SCALE_UP",
    "node_pool": "default",
    "target_nodes": 1,
    "requested_cpu": "2000m",
    "requested_memory": "1073741824",
    "reason": "Agent requires 2000m CPU. Existing nodes lack contiguous capacity. Recommend scaling default pool by +1 node.",
    "confidence": 0.95,
    "reasoning_source": "bedrock",
    "model_id": "anthropic.claude-3-5-haiku-20241022-v1:0",
    "agent_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
    "pod_name": "agent-pending-cpu",
    "timestamp": "2026-09-20T10:15:00Z"
  }
  ```
- **Deterministic Fallback Output Example (AWS Unavailable / Timeout / Malformed):**
  ```json
  {
    "action": "REQUEST_SCALE_UP",
    "node_pool": "default",
    "target_nodes": 1,
    "requested_cpu": "500m",
    "requested_memory": "536870912",
    "reason": "Deterministic fallback: classification insufficient_cpu mapped to default scale up of 1 node.",
    "confidence": 1.0,
    "reasoning_source": "deterministic_fallback",
    "model_id": "deterministic-rules-v1",
    "agent_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
    "pod_name": "agent-pending-cpu",
    "timestamp": "2026-09-20T10:15:00Z"
  }
  ```

