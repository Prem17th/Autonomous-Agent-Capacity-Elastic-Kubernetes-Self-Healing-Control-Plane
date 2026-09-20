# Nasiko Sentinel - Phase 3 Autoscaling & Recovery Design Specification

## Executive Summary
This document defines the architectural and technical design for **Phase 3: Controlled Autoscaling & Recovery Execution** for Nasiko Sentinel. It establishes how Sentinel safely translates deterministic scheduling bottleneck diagnoses into controlled capacity scaling actions, polls for infrastructure readiness, triggers agent reconciliation, and verifies end-to-end recovery without compromising cluster safety or stability.

---

## 1. Classification Index

To ensure technical rigor, all statements and design decisions are strictly classified as:
- **`[VERIFIED]`**: Empirically proven from local inspection, source code, or Kubernetes API specifications.
- **`[INFERENCE]`**: Logical deduction based on verified evidence.
- **`[DESIGN PROPOSAL]`**: Recommended architectural design for Phase 3 implementation.
- **`[UNKNOWN]`**: External dependency or environment detail requiring user/organizer confirmation.

---

## 2. Target Deployment Environment
- **Local Host**: Windows environment with Python 3.14.7, Node v24.21.0, kubectl v1.36.1 `[VERIFIED]`.
- **AWS & Remote Cloud State**: No active AWS credentials or remote EKS kubeconfig are currently configured in the workspace environment `[VERIFIED]`.
- **Demo Platform**: The final demonstration may run on AWS EKS or a local simulated cluster (Kind / Minikube) `[UNKNOWN]`.
- **Dual-Mode Adapter Strategy**: Sentinel will be designed with an environment-agnostic Autoscaler Adapter supporting both cloud EKS (Karpenter / Cluster Autoscaler) and local simulated capacity environments `[DESIGN PROPOSAL]`.

---

## 3. Autoscaler Options & Architecture Decision

### Option A: Karpenter (`karpenter.sh`)
- **Mechanism**: Declarative `NodePool` and `NodeClaim` custom resources. Karpenter provisions right-sized EC2 instances directly in response to pending pods or explicit NodePool capacity adjustments.
- **Latency**: Typically 45–90 seconds on AWS EKS `[INFERENCE]`.
- **Interface**: Kubernetes CRD API (`karpenter.sh/v1beta1` or `karpenter.sh/v1`).

### Option B: Kubernetes Cluster Autoscaler (CAS)
- **Mechanism**: Manages AWS AutoScaling Groups (ASGs) by altering desired capacity or reacting to unschedulable pod events.
- **Latency**: Typically 90–180 seconds on AWS EKS `[INFERENCE]`.
- **Interface**: AWS ASG API / `cluster-autoscaler` deployment annotations.

### Option C: Simulated Elastic Autoscaler (Local / Offline Mode)
- **Mechanism**: Emulated node provisioning adapter for zero-cloud hackathon demonstrations and unit test suites.
- **Latency**: 5–15 seconds `[DESIGN PROPOSAL]`.

### Architectural Decision
**Hybrid Autoscaler Provider Interface (`AutoscalerProvider`)** `[DESIGN PROPOSAL]`:
- Sentinel will define a generic `AutoscalerProvider` interface with concrete implementations:
  1. `KarpenterAutoscalerProvider`: Interacts with Karpenter CRDs on AWS EKS.
  2. `ClusterAutoscalerProvider`: Interacts with ASG / managed node groups.
  3. `SimulatedAutoscalerProvider`: Simulates node creation and readiness for local verification.

---

## 4. Scaling Mechanism & Workflow

```
┌────────────────────────┐
│  diagnose_capacity     │ (Identifies 'insufficient_cpu' / 'insufficient_memory')
└───────────┬────────────┘
            │
            ▼
┌────────────────────────┐
│   request_scale_up     │ (Validates safety limits, invokes AutoscalerProvider)
└───────────┬────────────┘
            │
            ▼
┌────────────────────────┐
│  wait_for_capacity     │ (Polls Kubernetes API until target Node reaches 'Ready')
└───────────┬────────────┘
            │
            ▼
┌────────────────────────┐
│     retry_agent        │ (Triggers Nasiko / K8s Deployment reconciliation)
└───────────┬────────────┘
            │
            ▼
┌────────────────────────┐
│  verify_agent_running  │ (Confirms PodScheduled=True, Ready=True, Endpoint live)
└────────────────────────┘
```

---

## 5. Required Permissions (RBAC & IAM)
*Classification: DESIGN PROPOSAL*

Sentinel requires the following Kubernetes RBAC permissions:
- **Pods & Events**: `get`, `list`, `watch` on `api/v1/pods`, `api/v1/events`.
- **Nodes**: `get`, `list`, `watch` on `api/v1/nodes`.
- **Deployments**: `get`, `list`, `watch`, `patch` on `apps/v1/deployments`.
- **Karpenter (if EKS)**: `get`, `list`, `patch`, `create` on `karpenter.sh/v1beta1/nodepools`, `karpenter.sh/v1beta1/nodeclaims`.
- **AWS IAM (if ASG)**: `autoscaling:DescribeAutoScalingGroups`, `autoscaling:SetDesiredCapacity`.

---

## 6. Sentinel → Autoscaler Interaction Contracts

### Tool 1: `request_scale_up`
- **Input**:
  - `node_pool` (string, default: `"default"`): Target node pool identifier.
  - `target_nodes` (integer, default: `1`): Number of additional nodes to provision (max: `3`).
  - `requested_cpu` (string, optional): Required CPU minimum (e.g. `"2000m"`).
  - `requested_memory` (string, optional): Required Memory minimum (e.g. `"4Gi"`).
  - `dry_run` (boolean, default: `false`): If true, simulates safety checks without mutating infrastructure.
- **Output**:
  ```json
  {
    "scale_request_id": "scale-req-8f12a9b3",
    "status": "ACCEPTED",
    "node_pool": "default",
    "nodes_requested": 1,
    "current_ready_nodes": 2,
    "target_ready_nodes": 3,
    "timestamp": "2026-09-20T10:15:00Z",
    "estimated_latency_seconds": 90
  }
  ```

### Tool 2: `wait_for_capacity`
- **Input**:
  - `scale_request_id` (string, optional): Correlation ID from `request_scale_up`.
  - `target_ready_nodes` (integer, optional): Expected minimum ready node count.
  - `timeout_seconds` (integer, default: `180`, max: `300`): Maximum duration to poll.
  - `poll_interval_seconds` (integer, default: `5`): Polling frequency.
- **Output**:
  ```json
  {
    "status": "READY",
    "ready_nodes_count": 3,
    "new_nodes": [
      {
        "node_name": "ip-10-0-2-45.ec2.internal",
        "allocatable_cpu_milli": 3860,
        "allocatable_memory_bytes": 16357785600,
        "joined_at": "2026-09-20T10:16:15Z"
      }
    ],
    "elapsed_seconds": 75
  }
  ```

### Tool 3: `retry_agent`
- **Input**:
  - `agent_id` (string, required): RFC 4122 UUID v4 of the Nasiko agent.
  - `namespace` (string, optional): Target namespace.
- **Output**:
  ```json
  {
    "agent_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
    "reconciliation_triggered": true,
    "method": "deployment_restart",
    "deployment_name": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
    "timestamp": "2026-09-20T10:16:30Z"
  }
  ```

---

## 7. Safety Controls & Policy Limits
*Classification: DESIGN PROPOSAL*

To prevent cluster instability, runaway costs, or autoscaler flapping:
1. **Max Scale Ceiling**: Maximum `+2` nodes per single scale request; maximum `10` total nodes in the cluster.
2. **Cooldown Period / Debounce**: Minimum `120` seconds mandatory cooldown between consecutive scale operations on the same node pool.
3. **Rate Limiting**: Maximum `3` scale actions per 15-minute window.
4. **Dry-Run Validation**: Mandatory policy check evaluating max limits before executing any mutation.
5. **No Shell / Raw Command Execution**: All operations must execute through typed API handlers with parameterized inputs.

---

## 8. Timeout & Polling Strategy
*Classification: DESIGN PROPOSAL*

1. **Non-Blocking Async Polling**: `wait_for_capacity` polls the Kubernetes API at regular intervals (`5s`) without blocking the MCP server transport thread.
2. **Timeout Bounds**: Default timeout is `180` seconds (3 minutes), capped at `300` seconds (5 minutes).
3. **Exponential Backoff on Transient Errors**: If the Kubernetes API encounters network jitter during polling, retry with backoff (1s, 2s, 4s).
4. **Timeout Return Structure**: If timeout expires, return structured `TIMEOUT_ERROR` with current ready node count and elapsed duration rather than crashing.

---

## 9. Capacity Verification Criteria
*Classification: DESIGN PROPOSAL*

A capacity scale-up is considered **READY** only when all of the following conditions are met:
1. At least one new node object exists with `creationTimestamp >= scale_request_timestamp`.
2. The new node has condition `Ready = True`.
3. The new node has no untolerated scheduling taints.
4. The new node's `status.allocatable` satisfies the requested CPU and Memory headroom.

---

## 10. Agent Recovery Verification Criteria
*Classification: VERIFIED KUBERNETES & NASIKO CONTRACT*

An agent workload is considered **RECOVERED & RUNNING** only when:
1. `Deployment.status.readyReplicas >= 1`.
2. The agent's Pod transitions from `Pending` to `Running`.
3. `pod.status.conditions` contains `PodScheduled = True` and `Ready = True`.
4. `FailedScheduling` events cease to be emitted.
5. (Optional) Agent container responds with HTTP 200 on port `8000`.

---

## 11. Failure Scenarios & Mitigation

| Failure Scenario | Root Cause | Sentinel Mitigation / Recovery |
| :--- | :--- | :--- |
| **Cloud Quota Exceeded** | AWS vCPU limit reached in region | `wait_for_capacity` times out; returns `CLOUD_QUOTA_EXCEEDED` diagnostic for user notification. |
| **Node Join Timeout** | Cloud VM boot failure / networking issue | Timeout fires at 180s; triggers diagnostic report and alerts operator. |
| **Pod CrashLoopBackOff** | Agent application bug post-scheduling | `retry_agent` observes pod scheduled but crashing; returns `APP_CRASH` diagnosis (does NOT scale again). |
| **Flapping / Rapid Retries**| Repeated agent triggers | Enforced 120s cooldown debounce window prevents duplicate scale requests. |
| **Disconnected Cluster** | Network disconnect to API server | Clean `INFRASTRUCTURE_ERROR` returned; Sentinel service remains healthy. |

---

## 12. Local Testing Strategy
*Classification: DESIGN PROPOSAL*

Phase 3 will be verified locally with zero cloud dependencies using:
1. **Mock Autoscaler Provider**: Implements `AutoscalerProvider` interface with controllable time-delayed node additions in unit tests.
2. **Deterministic Time-Stepped Tests**:
   - Test 1: `request_scale_up` accepts valid request and rejects requests exceeding max ceiling (+5 nodes).
   - Test 2: `request_scale_up` enforces 120s cooldown debounce.
   - Test 3: `wait_for_capacity` polls and transitions to `READY` when node joins.
   - Test 4: `wait_for_capacity` cleanly times out after configured deadline.
   - Test 5: `retry_agent` triggers Deployment restart and verifies pod transition to `Running`.
   - Test 6: Dry-run simulation mode.

---

## 13. Hackathon Demo Strategy
*Classification: DESIGN PROPOSAL*

1. **Step 1 (Saturated Cluster)**: Cluster starts with full node utilization (0 available CPU).
2. **Step 2 (Deploy Agent)**: User requests high-compute Nasiko agent (2000m CPU).
3. **Step 3 (Detection)**: Sentinel detects pod in `Pending` state via `get_pending_pods`.
4. **Step 4 (Diagnosis)**: `diagnose_capacity` deterministically classifies `insufficient_cpu`.
5. **Step 5 (Safe Scale)**: `request_scale_up` provisions 1 compute node in pool `default`.
6. **Step 6 (Wait)**: `wait_for_capacity` displays progress spinner until node is `Ready`.
7. **Step 7 (Retry & Verify)**: `retry_agent` reconciles workload; agent pod reaches `Running`.
8. **Step 8 (Summary)**: DronaHQ / Bedrock displays complete recovery timeline.

---

## 14. Unknowns Requiring Confirmation

1. **Live EKS Cluster Credentials**: Will organizers provide an active EKS cluster with Karpenter/ASG, or should the demo support local Kind/Simulated execution?
2. **Cloud Region & Instance Types**: If on AWS, which target instance types (e.g. `m5.large`, `c6i.xlarge`) should the default node pool target?
3. **Target Namespace**: Will agents run in `default`, `nasiko-agents`, or custom namespaces?

---

### NEXT STEP
Standing by for ChatGPT architecture review of this Phase 3 Design Specification.

