# Aegis Sentinel - Project Plan & Multi-Phase Roadmap

## Executive Summary
Aegis Sentinel is an AI-powered elastic Kubernetes capacity and recovery system designed to ensure high-reliability agent deployment for Aegis. When available Kubernetes node capacity is exhausted, new agent workloads can become unschedulable (Pending). Aegis Sentinel orchestrates detection, diagnosis via deterministic classification and LLM reasoning, capacity scaling via infrastructure tools, and agent re-scheduling verification.

> [!IMPORTANT]
> **Authoritative Scheduling Principle:**
> Do not use aggregate cluster capacity as proof that a pod is schedulable. Kubernetes `default-scheduler` evidence (`FailedScheduling` events, `PodScheduled=False`, and scheduler messages) remains authoritative. Node-level capacity analysis serves as supporting evidence.

---

## Multi-Phase Roadmap

### Phase 1: Project Foundation
**Status: Complete & Verified**
- [x] Repository setup, Git initialization, and `.gitignore`.
- [x] Language decision (Python 3) and architecture documentation.
- [x] Central configuration management with `.env` support and safe defaults.
- [x] Structured logging framework with secret redaction and JSON support.
- [x] Centralized error classification and exception handling.
- [x] Model Context Protocol (MCP) server foundation (JSON-RPC 2.0 stdio dispatching).
- [x] Service health and readiness reporting (`get_health`).

---

### Phase 2: Aegis / Kubernetes Observation & Diagnosis Layer
**Status: Complete & Verified**
- [x] Source verification of `Aegis-Labs/aegis` repository contracts.
- [x] Implement Kubernetes client and adapter layer (`src/kubernetes/`).
- [x] Implement `get_agent_status`: Inspect Aegis agent lifecycle (`Deployment/<agent_uuid>`).
- [x] Implement `get_pending_pods`: Identify pods stuck in unschedulable/pending states.
- [x] Implement `get_pod_events`: Parse scheduling failure reason codes (`FailedScheduling`).
- [x] Implement `get_node_capacity`: Compute allocatable capacity vs resource requests across nodes.
- [x] Implement `diagnose_capacity`: Deterministically classify capacity bottlenecks (`insufficient_cpu`, `insufficient_memory`, `too_many_pods`, `resource_quota`, `taint_or_constraint`, `node_pool_constraint`, `unknown`).
- [x] Full mock test suite with 53 passing test cases.
- [x] Document MCP tool contracts (`docs/MCP_TOOL_CONTRACTS.md`).

> [!NOTE]
> Live Kubernetes integration is implemented but has not yet been validated against a running Kubernetes cluster.

---

### Phase 3: Controlled Capacity Scaling & Recovery Execution
**Status: Complete & Verified (80/80 Tests Passing)**
**Focus:** Safe infrastructure mutation, capacity polling, and recovery state tracking
- [x] Implement `AutoscalerProvider` interface abstraction.
- [x] Implement `SimulatedAutoscalerProvider` supporting mock capacity injection and realistic provisioning delay.
- [x] Implement `RecoveryPolicyEngine`: max 2 nodes/request, max 10 cluster nodes, 120s cooldown debounce, rate limit (3 ops/15min), allowed node pools, dry-run mode.
- [x] Implement `RecoveryTracker` state machine (`DETECTED` → `DIAGNOSED` → `POLICY_VALIDATED` → `SCALE_REQUESTED` → `PROVISIONING` → `CAPACITY_READY` → `AGENT_RECOVERY_CHECK` → `RUNNING`).
- [x] Implement Phase 3 active tools: `request_scale_up`, `wait_for_capacity`, `get_autoscaler_status`, `get_node_pool_status`, `get_recovery_status`, `verify_agent_recovery`.
- [x] Implement optional auxiliary tool `retry_agent` (outside canonical flow).
- [x] Wire all tools into `MCPServer` and update `get_health` for Phase 3 readiness.
- [x] Comprehensive test suites with 80/80 unit and integration tests passing.

> [!NOTE]
> Production Karpenter/Cluster Autoscaler provider integration is ready to connect pending confirmation of the live AWS/EKS cluster environment.

---

### Phase 4: AI Reasoning & AWS Bedrock Integration
**Status: Planned (Next Phase)**
**Focus:** Intelligent root-cause analysis and recovery decision making
- Integrate AWS Bedrock client (`boto3`) with configurable models (Claude 3.5 Sonnet / Haiku).
- Construct structured prompts consuming deterministic diagnosis outputs from Phase 2.
- Implement reasoning loops that formulate multi-step recovery strategies.
- Format reasoning output for human-readable summaries and DronaHQ UI consumption.

---

### Phase 5: DronaHQ Orchestration & Application Layer
**Status: Planned**
**Focus:** UI integration, workflow triggers, and real-time status reporting
- Connect DronaHQ application layer to MCP server endpoints (via HTTP/SSE transport).
- Provide real-time recovery event telemetry, logs, and diagnostic timelines.
- Present human-readable explanations and interactive operator approval gates.

---

### Phase 6: End-to-End Recovery Verification & Testing
**Status: Planned**
**Focus:** Full autonomous loop validation and demonstration
- Execute end-to-end demo flow against saturated cluster.
- Validate complete autonomous cycle: Exhausted cluster → Pending agent → Detection → Diagnosis → Controlled scale-up → Capacity readiness → Auto-scheduling → Verified running.
