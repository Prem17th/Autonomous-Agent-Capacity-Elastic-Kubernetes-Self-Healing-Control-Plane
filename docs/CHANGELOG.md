# Changelog

All notable changes to the Nasiko Sentinel project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.0] - 2026-09-20 (Phase 5: DronaHQ Streamable HTTP Transport Implementation)

### Added
- **Streamable HTTP Network Transport (`src/server/http_server.py`):**
  - Implemented `HttpMCPServer` transport adapter wrapping the existing `MCPServer.handle_request()` JSON-RPC dispatcher.
  - Constant-time API Key authentication (`secrets.compare_digest`) supporting `Authorization: Bearer <key>`, `X-Sentinel-API-Key`, and `X-API-Key` headers.
  - Safe request parsing, Content-Length boundaries, and structured JSON-RPC error mapping without tracebacks.
  - `GET /health` endpoint for HTTP liveness and dependency status monitoring.
- **Configuration & CLI Enhancements (`src/config/settings.py`, `src/main.py`):**
  - Added `mcp_http_host`, `mcp_http_port`, and `sentinel_api_key` configuration fields.
  - Added `--http` and `--stdio` CLI switches.
  - Fail-safe check preventing unauthenticated HTTP server startup in production/dev.
- **Automated Test Suite Expansion & Compatibility:**
  - Added 15 new unit and integration tests in `tests/test_http_server.py` covering HTTP lifecycle, initialize, tools/list, tools/call, auth rejections, policy enforcement, and key masking (109 total tests, 100% passing).
  - Created standalone compatibility test script `scripts/test_mcp_http_compatibility.py`.
- **Documentation & Setup Guides:**
  - Created `docs/PHASE5_DRONAHQ_IMPLEMENTATION.md` and `docs/DRONAHQ_SETUP.md`.
  - Added `ADR-013: Streamable HTTP Network Transport for DronaHQ Integration`.

---

## [0.4.0] - 2026-09-20 (Phase 4: AI Reasoning & AWS Bedrock Integration)

### Added
- **AI Reasoning Subsystem (`src/bedrock/`):**
  - Abstract provider interface `BedrockReasoner` with standard `reason(context)` contract (`src/bedrock/provider.py`).
  - Structured data models: `RecoveryContext`, `RecoveryProposal`, and `ActionType` (`NO_ACTION`, `REQUEST_SCALE_UP`) (`src/bedrock/models.py`).
  - `ProposalValidator` enforcing strict action allowlists, valid target nodes, and parameter hygiene (`src/bedrock/validator.py`).
  - Explicit `DeterministicFallbackReasoner` mapping deterministic diagnoses into safe proposal actions when Bedrock is unavailable (`src/bedrock/fallback_reasoner.py`).
  - `MockBedrockReasoner` for offline test suites, failure simulation, and latency emulation (`src/bedrock/mock_reasoner.py`).
  - `BedrockRuntimeReasoner` connecting to AWS Bedrock Converse API via `boto3` behind provider abstractions (`src/bedrock/bedrock_reasoner.py`).
  - Orchestrator `SentinelRecoveryReasoner` combining primary reasoning, schema validation, and transparent fallback (`src/bedrock/orchestrator.py`).
- **Phase 4 Active MCP Tools (`src/tools/`):**
  - `reason_recovery`: Synthesizes deterministic Kubernetes diagnostics into structured remediation proposals using AWS Bedrock or explicit fallback (`src/tools/reason_recovery.py`).
- **Health Check Enhancement (`src/server/health.py`):**
  - Added `dependencies.bedrock` reporting model ID, status (`mock` / `connected` / `unavailable`), and mock mode flag.
- **Automated Test Suite Expansion:**
  - Added 14 unit and integration tests across Mock reasoning, schema validation, fallback activation, policy interception, and MCP server tools (94 total tests, 100% passing).
- **Architectural Decision Records:**
  - Added `ADR-011: AWS Bedrock Reasoner & Proposal Model`.
  - Added `ADR-012: Explicit Deterministic Fallback & Policy Authorization`.

---

## [0.3.0] - 2026-09-20 (Phase 3: Controlled Autoscaling & Recovery Execution)

### Added
- **Autoscaler Subsystem (`src/autoscaler/`):**
  - Abstract provider interface `AutoscalerProvider` for decoupled cloud (Karpenter/CAS) and simulated scaling backends (`src/autoscaler/provider.py`).
  - Realistic `SimulatedAutoscalerProvider` supporting lifecycle transitions (`REQUESTED` → `PROVISIONING` → `READY`/`FAILED`/`TIMEOUT`), simulated latency delays, and mock node injection into `KubernetesAdapter` (`src/autoscaler/simulated_provider.py`).
  - `RecoveryPolicyEngine` enforcing strict cluster safety controls: max 2 nodes per request, max 10 cluster nodes, 120s cooldown debounce per node pool, 3 ops/15min rate limit, node pool whitelisting, and dry-run policy evaluation (`src/autoscaler/policy.py`).
  - `RecoveryTracker` state machine managing lifecycle audit trails (`DETECTED` → `DIAGNOSED` → `POLICY_VALIDATED` → `SCALE_REQUESTED` → `PROVISIONING` → `CAPACITY_READY` → `AGENT_RECOVERY_CHECK` → `RUNNING`) (`src/autoscaler/recovery_tracker.py`).
  - Data models for `ScaleRequest`, `ScaleOperation`, `NodePoolStatus`, and `RecoveryRecord` (`src/autoscaler/models.py`).
- **Phase 3 Active MCP Tools (`src/tools/`):**
  - `request_scale_up`: Evaluates safety policies and dispatches scale requests to the autoscaler provider (`src/tools/request_scale_up.py`).
  - `wait_for_capacity`: Asynchronous/polling mechanism checking when newly requested capacity reaches Ready state with allocatable headroom (`src/tools/wait_for_capacity.py`).
  - `verify_agent_recovery`: Confirms whether Nasiko agent deployment and backing pod reached `Running` status with ready replicas (`src/tools/verify_recovery.py`).
  - `get_autoscaler_status`: Reports autoscaler health, provider mode, and operation metrics (`src/tools/autoscaler_status.py`).
  - `get_node_pool_status`: Inspects instance counts, limits, and status of target node pools (`src/tools/autoscaler_status.py`).
  - `get_recovery_status`: Queries audit history and state transitions for active or completed agent recoveries (`src/tools/recovery_status.py`).
  - `retry_agent`: Auxiliary tool to trigger manual deployment reconciliation outside the canonical auto-scheduling flow (`src/tools/retry_agent.py`).
- **Automated Test Suite Expansion:**
  - Added 27 new unit and integration tests across policy validation, simulated autoscaler mechanics, tool handlers, MCP server JSON-RPC calls, and full end-to-end recovery sequence (80 total unit tests, 100% passing).
- **Architectural Decision Records:**
  - Added `ADR-009: Provider Abstraction & Simulation for Controlled Autoscaling`.
  - Added `ADR-010: Normal Recovery Flow & Independent Auto-Scheduling Verification`.

---

## [0.2.0] - 2026-09-20 (Phase 2: Kubernetes Observation & Diagnosis Layer)

### Added
- **Kubernetes Integration Layer (`src/kubernetes/`):**
  - Data models for normalized Pod, Node, Event, Deployment, and Capacity representations (`src/kubernetes/models.py`).
  - Unit-aware quantity parsers for CPU (`parse_cpu_milli` parsing `500m`, `2`, `0.5`) and Memory (`parse_memory_bytes` parsing `Ki`, `Mi`, `Gi`, bare bytes).
  - Kubernetes API client (`src/kubernetes/client.py`) supporting in-cluster ServiceAccount, kubeconfig parsing, and mock test client (`MockKubernetesClient`).
  - High-level adapter (`src/kubernetes/adapter.py`) providing resource normalization and deterministic diagnosis.
- **Active MCP Observation Tools (`src/tools/`):**
  - `get_agent_status`: Query agent lifecycle and backing Kubernetes Deployment (`Deployment/<agent_uuid>`).
  - `get_pending_pods`: Filter pods in `Pending` state or with `PodScheduled=False` with normalized resource requests.
  - `get_pod_events`: Extract scheduling and lifecycle events (filtering `FailedScheduling` events).
  - `get_node_capacity`: Compute total allocatable vs requested CPU millicores, memory bytes, and max pod limits across nodes.
  - `diagnose_capacity`: Deterministic classification of scheduling bottlenecks (`insufficient_cpu`, `insufficient_memory`, `too_many_pods`, `resource_quota`, `taint_or_constraint`, `node_pool_constraint`, `unknown`).
- **MCP Tool Contracts:** Created comprehensive specification in `docs/MCP_TOOL_CONTRACTS.md`.
- **Automated Test Suite Expansion:** Added 29 new unit tests covering Kubernetes normalization, client connection error handling, tool handlers, and diagnosis classifications (53 total unit tests, 100% passing).

---

## [0.1.0] - 2026-09-20 (Phase 1: Project Foundation)

### Added
- **Project Foundation:** Initialized repository structure with `pyproject.toml`, `requirements.txt`, `.gitignore`, and `.env.example`.
- **Configuration Management:** Implemented `Settings` module supporting environment variables, type validation, safe defaults, and secret masking (`src/config/settings.py`).
- **Structured Logging:** Implemented extensible logger with UTC timestamps, custom event metadata, and sensitive token redaction (`src/logger/logger.py`).
- **Unified Error Handling:** Created hierarchical exception types with `SentinelError`, `ConfigError`, `ValidationError`, `InfrastructureError`, `ExternalServiceError`, `TimeoutError`, and `InternalError` (`src/errors/exceptions.py`).
- **MCP Server Foundation:** Built Model Context Protocol (MCP) server supporting JSON-RPC 2.0 protocol over `stdio` (`src/server/mcp_server.py`).
- **Health Reporting:** Implemented `get_health_status` mechanism and CLI `--health` flag (`src/server/health.py`).
- **Documentation Suite:** Authored `ARCHITECTURE.md`, `DECISIONS.md`, `PROJECT_PLAN.md`, `TODO.md`, `BUGS.md`, and `DEMO_FLOW.md`.
