# Aegis Sentinel

**AI-powered elastic Kubernetes capacity and recovery system for Aegis agent creation.**

---

## 1. What is Aegis Sentinel?

Aegis Sentinel is an automated reliability and capacity recovery system designed for agentic workloads deployed on Kubernetes. When a high-density cluster runs out of allocatable CPU, memory, or pod limits, newly requested Aegis agents can become stuck in `Pending` (unschedulable) states. 

Aegis Sentinel serves as a controlled bridge between AI reasoning engines (AWS Bedrock / DronaHQ) and Kubernetes infrastructure, orchestrating bottleneck detection, intelligent recovery planning, safe capacity provisioning, and verified agent re-scheduling.

---

## 2. The Problem It Solves

Aegis deploys dynamic AI agents as containerized workloads on Kubernetes (`Deployment/<agent_uuid>`, `ClusterIP Service 80 -> 8000`). When available cluster capacity is exhausted:
- New agent deployments stall indefinitely in `Pending` status.
- Kubernetes scheduling events produce errors like `FailedScheduling` (`Insufficient cpu` / `Insufficient memory` / `Too many pods`).
- Manual operator intervention is slow, reactive, and brittle.

Aegis Sentinel solves this by:
1. Detecting unschedulable agent pods in real time via direct Kubernetes API observation.
2. Diagnosing whether bottlenecks stem from CPU, memory, quotas, or node pools deterministically.
3. Formulating safe scaling plans using AI reasoning and policy limits.
4. Safely provisioning capacity via controlled Model Context Protocol (MCP) tools (`request_scale_up`, `wait_for_capacity`).
5. Waiting for capacity readiness and verifying automatic agent recovery into `Running` status (`verify_agent_recovery`).

> [!IMPORTANT]
> **Authoritative Scheduling Rule:**
> Do not use aggregate cluster capacity as proof that a pod is schedulable. Kubernetes `default-scheduler` evidence (`FailedScheduling` events, `PodScheduled=False`, and scheduler messages) remains authoritative. Node-level capacity analysis serves as supporting evidence.

---

## 3. Current Phase 5 Scope & Status

In **Phase 5 (DronaHQ Streamable HTTP Transport Implementation)**, the Streamable HTTP transport adapter, API Key authentication, CLI transport selection, and DronaHQ setup specifications are fully implemented and verified.

### Implemented in Phase 5:
- **Streamable HTTP Transport Adapter (`HttpMCPServer`):** Exposes `POST /mcp` and `GET /health` endpoints wrapping the existing in-memory `MCPServer.handle_request()` JSON-RPC dispatcher.
- **Authentication & Security:** Constant-time `SENTINEL_API_KEY` verification supporting `Authorization: Bearer <key>`, `X-Sentinel-API-Key`, and `X-API-Key` headers.
- **Fail-Safe Startup:** Requires `SENTINEL_API_KEY` in production/development before starting the HTTP network endpoint.
- **Dual Transport CLI:** Supports both `--stdio` (default) and `--http` runtime modes (`MCP_TRANSPORT=http`).
- **Complete Test Suite Passing:** **109/109 unit and integration tests passing** (94 original + 15 Phase 5 tests).

> [!NOTE]
> **Transport Capabilities:**
> - **Supported:** Streamable HTTP (`POST /mcp`) and stdio.
> - **Not Implemented:** SSE (Server-Sent Events), pending specific downstream client requirement.

> [!IMPORTANT]
> **What is NOT Implemented Yet (Planned for Future Phases):**
> - End-to-end live cluster demo & saturation testing (Phase 6).

---

## 4. Architecture & Roadmap

```
USER
  ↓
DRONAHQ AI AGENT (Phase 5 - Streamable HTTP Connector)
  ↓
SENTINEL HTTP GATEWAY (POST /mcp - API Key Authenticated)
  ↓
MCP SERVER (Active Gateway - JSON-RPC 2.0 Protocol)
  ↓
AWS BEDROCK (Phase 4 - AI Reasoning & Proposal Formulation)
  ↓
RECOVERY POLICY ENGINE (Authoritative Safety Bounds)
  ↓
CONTROLLED AUTOSCALER (Phase 3 - Capacity Provisioning)
  ↓
AEGIS + KUBERNETES (Phase 2 - Observation & Diagnosis Layer)
  ↓
AGENT RUNNING
```

### Multi-Phase Roadmap:
- **Phase 1 (Completed):** Project Foundation, Configuration, Structured Logging, Error Hierarchy, MCP Server Skeleton.
- **Phase 2 (Completed):** Aegis / Kubernetes Observation Layer & Deterministic Capacity Diagnosis.
- **Phase 3 (Completed):** Controlled Autoscaling Provider, Safety Policy Engine, Recovery State Tracking, Verification Tools.
- **Phase 4 (Completed):** AWS Bedrock AI Reasoning, Proposal Schema Validation, Explicit Deterministic Fallback, `reason_recovery` Tool.
- **Phase 5 (Completed):** DronaHQ Streamable HTTP Transport Adapter, API Key Auth, Compatibility Testing.
- **Phase 6 (Planned Next):** End-to-End Autonomous Recovery Verification & Demo.

---

## 5. Prerequisites

- **Python:** Python 3.10 or higher (Tested with Python 3.14.7)
- **Operating System:** Windows, Linux, or macOS
- **Kubernetes (Optional for Local Dev):** In-cluster ServiceAccount or `~/.kube/config` (offline mock/simulated fallback active)

---

## 6. Installation & Setup

1. **Clone or navigate to the repository:**
   ```bash
   cd c:/Users/PREM TH/OneDrive/Desktop/Project-2
   ```

2. **Configure Environment:**
   Copy the example environment configuration:
   ```bash
   # On Windows PowerShell
   Copy-Item .env.example .env

   # On Linux / macOS
   cp .env.example .env
   ```

3. **Install Dependencies (Optional):**
   ```bash
   python -m pip install -r requirements.txt
   ```

---

## 7. How to Run Locally

### Health Check
Verify service status, active phase, and dependency reachability:
```bash
python src/main.py --health
```
*Sample Output:*
```json
{
  "status": "ok",
  "service": "aegis-sentinel",
  "version": "0.1.0",
  "environment": "development",
  "phase": 4,
  "components": {
    "config": "ready",
    "mcp_server_foundation": "ready",
    "deterministic_diagnosis": "ready",
    "controlled_autoscaling": "ready",
    "ai_reasoning": "ready"
  },
  "dependencies": {
    "kubernetes": {
      "status": "unreachable",
      "detail": "Live Kubernetes integration is implemented but has not yet been validated against a running Kubernetes cluster (offline/simulation mode active)."
    },
    "autoscaler": {
      "provider": "simulated",
      "status": "ready",
      "detail": "Autoscaler provider abstraction initialized with simulated provider."
    },
    "bedrock": {
      "model_id": "anthropic.claude-3-5-haiku-20241022-v1:0",
      "status": "mock",
      "mock_mode": true
    }
  },
  "roadmap": {
    "phase_1": "foundation (completed)",
    "phase_2": "aegis_kubernetes_observation (completed)",
    "phase_3": "controlled_autoscaling (completed)",
    "phase_4": "bedrock_reasoning (completed)",
    "phase_5": "dronahq_integration (planned)",
    "phase_6": "end_to_end_recovery (planned)"
  }
}
```

### Run MCP Server (stdio transport - default)
Launch the Model Context Protocol server over standard I/O:
```bash
python src/main.py
# Or explicitly:
python src/main.py --stdio
```

Interact with the server via JSON-RPC 2.0 messages over standard input:
```json
{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "client", "version": "1.0"}}}
{"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
{"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "diagnose_capacity", "arguments": {"pod_name": "agent-pending-cpu"}}}
{"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "reason_recovery", "arguments": {"pod_name": "agent-pending-cpu", "agent_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d"}}}
{"jsonrpc": "2.0", "id": 5, "method": "tools/call", "params": {"name": "request_scale_up", "arguments": {"node_pool": "default", "target_nodes": 1, "agent_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d"}}}
{"jsonrpc": "2.0", "id": 6, "method": "tools/call", "params": {"name": "wait_for_capacity", "arguments": {"scale_request_id": "scale-op-a1b2c3d4", "timeout_seconds": 60}}}
{"jsonrpc": "2.0", "id": 7, "method": "tools/call", "params": {"name": "verify_agent_recovery", "arguments": {"agent_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d"}}}
```

### Run MCP Server (Streamable HTTP transport - DronaHQ / Remote)
Launch the Model Context Protocol server over Streamable HTTP:
```bash
# In PowerShell:
$env:SENTINEL_API_KEY="my-secret-key-12345"
python src/main.py --http

# Or in Linux / macOS:
SENTINEL_API_KEY="my-secret-key-12345" python src/main.py --http
```

Execute tool calls against `http://127.0.0.1:8000/mcp`:
```bash
curl -X POST http://127.0.0.1:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer my-secret-key-12345" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}'
```

---

## 8. How to Run Automated Tests

Run the full automated test suite using Python's built-in `unittest` runner:

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

All 109 test cases pass with zero cloud dependencies:
- `test_config.py`: Default configuration, environment overrides, validation errors.
- `test_logging.py`: Structured output, formatting, sensitive token redaction.
- `test_errors.py`: Exception inheritance, error codes, serialization for all error types including `PolicyError`.
- `test_kubernetes_adapter.py`: Quantity parsing (`500m`, `512Mi`), Agent deployment lookup, pod normalization, node capacity aggregation, connection error handling.
- `test_tools.py`: Observation tools and 8 deterministic diagnosis classification test cases.
- `test_autoscaler_policy.py`: Policy rules (max nodes per request, max cluster nodes, cooldown debounce, rate limit, pool whitelist, dry-run).
- `test_simulated_autoscaler.py`: Provider mechanics, state transitions (`PROVISIONING` → `READY`), mock capacity injection, timeouts, failure simulation.
- `test_phase3_tools.py`: Tool handlers, MCP server execution, and complete end-to-end simulated recovery sequence.
- `test_bedrock_reasoner.py`: Bedrock mock reasoning, proposal schema validation, deterministic fallback, policy interception, and `reason_recovery` MCP tool handling.
- `test_http_server.py`: Phase 5 Streamable HTTP transport adapter, API Key authentication, request limits, JSON-RPC errors, and policy validation.
- `test_server.py`: MCP protocol negotiation, active tool dispatching, and error handling.

---

## 9. Technical Specifications

- [docs/PHASE5_DRONAHQ_IMPLEMENTATION.md](docs/PHASE5_DRONAHQ_IMPLEMENTATION.md): Phase 5 DronaHQ Streamable HTTP Transport Implementation.
- [docs/DRONAHQ_SETUP.md](docs/DRONAHQ_SETUP.md): DronaHQ AI Agent MCP Setup Guide.
- [docs/PHASE4_BEDROCK_DESIGN.md](docs/PHASE4_BEDROCK_DESIGN.md): Phase 4 AWS Bedrock Reasoning Design Specification.
- [docs/PHASE3_AUTOSCALING_DESIGN.md](docs/PHASE3_AUTOSCALING_DESIGN.md): Phase 3 Autoscaling & Recovery Design Specification.
- [docs/MCP_TOOL_CONTRACTS.md](docs/MCP_TOOL_CONTRACTS.md): Full MCP tool schema definitions and input/output examples.
- [docs/AEGIS_INTEGRATION_REPORT.md](docs/AEGIS_INTEGRATION_REPORT.md): Source-verified technical report of `Aegis-Labs/aegis`.
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md): System architecture and component boundaries.
- [docs/DECISIONS.md](docs/DECISIONS.md): Architectural Decision Records (ADRs).
- [docs/TODO.md](docs/TODO.md): Prioritized multi-phase backlog.
- [docs/CHANGELOG.md](docs/CHANGELOG.md): Project changelog and release history.
