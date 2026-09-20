# Nasiko Sentinel - Target Demo Flow (Planned)

> [!NOTE]
> This document describes the planned end-to-end hackathon demonstration flow.
> In Phase 1, only the MCP server foundation and health mechanisms are active. Real Kubernetes mutations and Bedrock reasoning loops will be connected in future phases.

---

## Planned Scenario: Autonomous Capacity Scaling for Unschedulable Agents

```
Step 1: User Request       → User requests Nasiko agent creation via DronaHQ interface.
Step 2: Capacity Exhaustion→ Cluster lacks CPU/memory to schedule agent pod; pod transitions to Pending.
Step 3: Detection          → Sentinel detects pod stuck in Unschedulable state via `get_pending_pods`.
Step 4: AI Diagnosis       → AWS Bedrock analyzes scheduling events via `diagnose_capacity`.
Step 5: Controlled Recovery→ Bedrock calls `request_scale_up` via MCP gateway to expand node pool.
Step 6: Capacity Polling   → Sentinel polls cluster via `wait_for_capacity` until new node is Ready.
Step 7: Retry Agent        → Sentinel triggers `retry_agent` reconciliation.
Step 8: Verified Running   → Agent pod is scheduled and enters `Running` status.
Step 9: Explanation Display→ DronaHQ presents recovery timeline and diagnostic explanation to user.
```

---

## Detailed Step Walkthrough

### 1. Initial State: Saturated Cluster
- A Kubernetes cluster has running workloads utilizing 95%+ of allocatable CPU/memory.
- A user requests a high-resource Nasiko agent through the DronaHQ portal.

### 2. Failure Occurrence: Pod Unschedulable
- Nasiko provisions an agent Pod manifest in Kubernetes.
- Default Kubernetes scheduler rejects the pod due to `0/N nodes available: Insufficient cpu`.
- The pod remains in `Pending` state with event `FailedScheduling`.

### 3. Sentinel Detection & Triage
- Sentinel's MCP tool `get_pending_pods` surfaces the stuck agent workload.
- Sentinel gathers event history via `get_pod_events` and cluster node metrics via `get_node_capacity`.

### 4. AI Reasoning (AWS Bedrock)
- Bedrock ingests the diagnostic context:
  - Pod resource requests (e.g., 2000m CPU, 4Gi Memory).
  - Cluster node capacity table (all nodes at capacity).
  - Autoscaler limits and node pool configurations.
- Bedrock identifies the exact bottleneck: "Agent pod requires 2 CPU cores, but largest available node capacity is 400m CPU."
- Bedrock generates an actionable recovery plan: "Scale node pool `general-compute` by +1 instance."

### 5. Safe Tool Invocation via MCP
- Bedrock invokes `request_scale_up(node_pool="general-compute", target_nodes=3)` via the MCP server gateway.
- MCP validates safety constraints (checks max node limit, rate limits, and authorized credentials).

### 6. Node Provisioning & Readiness Verification
- Cloud provider / autoscaler spins up the new VM node.
- Sentinel executes `wait_for_capacity(timeout_seconds=180)` polling until the node joins the cluster and reports `Ready`.

### 7. Agent Reconciliation & Success
- Sentinel executes `retry_agent(agent_id=...)`.
- Kubernetes scheduler places the agent pod on the newly provisioned node.
- Pod reaches `Running` state and health probes pass.

### 8. User Feedback in DronaHQ
- DronaHQ UI updates in real-time:
  - Shows diagnostic reasoning ("Capacity shortage detected").
  - Displays recovery action ("Provisioned 1 new node in pool `general-compute`").
  - Confirms agent is ready for user interaction.

