# Nasiko Sentinel - Target & Component Architecture

## Architectural Overview

Nasiko Sentinel acts as an intelligent, automated reliability layer between user agent requests, Kubernetes infrastructure, and AI reasoning models.

```
USER
  ↓
DRONAHQ AGENT (Phase 5 - UI / Application Layer)
  ↓
AWS BEDROCK (Phase 4 - AI Diagnosis & Reasoning Engine)
  ↓
MCP SERVER (Active Foundation & Observation Gateway)
  ↓
CONTROLLED AUTOSCALER (Phase 3 - Capacity Provisioning & Retry)
  ↓
NASIKO + KUBERNETES (Phase 2 - Workload Execution & Observation)
  ↓
NEW CAPACITY → AGENT RUNNING
```

---

## Authoritative Scheduling Principle
> [!IMPORTANT]
> **Authoritative Scheduling Rule:**
> Do not use aggregate cluster capacity as proof that a pod is schedulable. The Kubernetes `default-scheduler` evidence (`FailedScheduling` events, `PodScheduled=False`, and scheduler messages) remains authoritative. Node-level capacity analysis serves as supporting evidence.

---

## Component Responsibilities

### 1. DronaHQ (Planned - Phase 5)
- **Role:** User-facing application and orchestration interface.
- **Responsibilities:**
  - Submit agent deployment requests.
  - Display real-time status of agent creation and recovery actions.
  - Present human-readable diagnostic explanations provided by Bedrock.

### 2. AWS Bedrock (Planned - Phase 4)
- **Role:** Cognitive diagnosis and multi-step recovery decision engine.
- **Responsibilities:**
  - Ingest structured diagnostic output from `diagnose_capacity`.
  - Reason over capacity trends, quota limits, and node pool selections.
  - Select recovery plans and invoke MCP tools deterministically.

### 3. Controlled Autoscaler & Recovery Engine (Planned - Phase 3)
- **Role:** Safe infrastructure mutation and retry orchestration.
- **Responsibilities:**
  - `request_scale_up`: Provision additional compute instances safely under strict policy bounds.
  - `wait_for_capacity`: Async polling loop verifying new nodes reach `Ready` state.
  - `retry_agent`: Re-trigger agent pod placement.

### 4. MCP Server (Foundation & Observation Active in Phase 1 & 2)
- **Role:** Standardized, secure Model Context Protocol gateway.
- **Responsibilities:**
  - Expose safe, structured tools over JSON-RPC 2.0.
  - Execute read/diagnosis operations (`get_agent_status`, `get_pending_pods`, `get_pod_events`, `get_node_capacity`, `diagnose_capacity`).
  - Distinguish Sentinel service health from external dependency reachability in `get_health`.

### 5. Kubernetes & Nasiko (Observation Implemented in Phase 2)
- **Role:** Target workload execution platform.
- **Responsibilities:**
  - Host Nasiko agent pods (`Deployment/<agent_uuid>`).
  - Emit scheduling error events (`FailedScheduling`, `Insufficient cpu`, etc.) when capacity is exhausted.
  - Note: Live Kubernetes integration is implemented but has not yet been validated against a running Kubernetes cluster.

---

## Status Matrix: Implemented vs. Planned

| Component / Layer | Status | Current Scope |
| :--- | :--- | :--- |
| **Project Structure & Git** | **CURRENTLY IMPLEMENTED (Phase 1)** | Clean layout, `.gitignore`, `.env.example`, `pyproject.toml` |
| **Config & Environment** | **CURRENTLY IMPLEMENTED (Phase 1)** | `Settings` loader, type validation, safe defaults |
| **Structured Logging** | **CURRENTLY IMPLEMENTED (Phase 1)** | Redacting logger, JSON / console formatting |
| **Error Handling** | **CURRENTLY IMPLEMENTED (Phase 1)** | Hierarchical exceptions (`ConfigError`, `InfrastructureError`, etc.) |
| **MCP Server Core** | **CURRENTLY IMPLEMENTED (Phase 1)** | JSON-RPC 2.0 dispatch, capability negotiation, tool registry |
| **Service Health Check** | **CURRENTLY IMPLEMENTED (Phase 1 & 2)** | `get_health` distinguishing service health from dependency reachability |
| **Nasiko / K8s Observation**| **CURRENTLY IMPLEMENTED (Phase 2)** | `get_agent_status`, `get_pending_pods`, `get_pod_events`, `get_node_capacity` |
| **Deterministic Diagnosis** | **CURRENTLY IMPLEMENTED (Phase 2)** | `diagnose_capacity` (CPU, Memory, Pod limits, Quotas, Taints, Node pools) |
| **Controlled Autoscaling** | *PLANNED (Phase 3)* | `request_scale_up`, `wait_for_capacity`, `retry_agent`, safeguards |
| **AWS Bedrock Integration** | *PLANNED (Phase 4)* | LLM reasoning, prompt engineering, multi-step explanation |
| **DronaHQ UI & App Layer** | *PLANNED (Phase 5)* | Frontend dashboard and orchestration flow |
| **End-to-End Recovery** | *PLANNED (Phase 6)* | Full loop automated recovery verification |
