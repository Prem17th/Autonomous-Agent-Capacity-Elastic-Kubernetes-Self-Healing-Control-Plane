# Aegis Sentinel - Backlog & Task Priority (TODO)

## Phase 1 (Foundation) - Completed
- [x] **[P0]** Establish project directory layout and Git configuration (`.gitignore`).
- [x] **[P0]** Implement central configuration management (`Settings`) with `.env` support.
- [x] **[P0]** Implement structured logging with redaction for sensitive fields.
- [x] **[P0]** Implement unified error hierarchy (`SentinelError` and specialized subclasses).
- [x] **[P0]** Implement MCP Server foundation supporting JSON-RPC 2.0 and capability negotiation.
- [x] **[P0]** Implement `get_health` status tool and health CLI flag (`--health`).

---

## Phase 2 (Aegis/Kubernetes Observation & Diagnosis) - Completed
- [x] **[P0]** Source verification of `Aegis-Labs/aegis` repository contracts.
- [x] **[P0]** Implement Kubernetes models and client abstraction (`src/kubernetes/models.py`, `src/kubernetes/client.py`).
- [x] **[P0]** Implement `get_agent_status` tool mapped to Aegis UUID deployments.
- [x] **[P0]** Implement `get_pending_pods` tool normalizing resource requests.
- [x] **[P0]** Implement `get_pod_events` tool extracting `FailedScheduling` event details.
- [x] **[P0]** Implement `get_node_capacity` tool computing allocatable vs requested CPU, memory, and pod limits.
- [x] **[P0]** Implement deterministic `diagnose_capacity` tool classifying 7 bottleneck categories.
- [x] **[P0]** Add unit test suite with 53 test cases covering mock cluster fixtures.
- [x] **[P0]** Document MCP tool contracts (`docs/MCP_TOOL_CONTRACTS.md`).
- [x] **[P0]** Separate Sentinel service health from external dependency reachability in `get_health`.

---

## Phase 3 (Controlled Autoscaling & Recovery Execution) - Completed
- [x] **[P0]** Implement `AutoscalerProvider` interface abstraction (`src/autoscaler/provider.py`).
- [x] **[P0]** Implement `SimulatedAutoscalerProvider` with realistic lifecycle (`REQUESTED` → `PROVISIONING` → `READY`/`FAILED`/`TIMEOUT`) and mock capacity injection (`src/autoscaler/simulated_provider.py`).
- [x] **[P0]** Implement `RecoveryPolicyEngine` with strict safety limits: max 2 nodes/req, max 10 cluster nodes, 120s cooldown debounce, rate limiting (3 ops/15min), allowed pools whitelist, dry-run mode (`src/autoscaler/policy.py`).
- [x] **[P0]** Implement `request_scale_up` tool validating safety policies and dispatching to provider (`src/tools/request_scale_up.py`).
- [x] **[P0]** Implement `wait_for_capacity` tool polling until capacity is ready and allocatable (`src/tools/wait_for_capacity.py`).
- [x] **[P0]** Implement `verify_agent_recovery` tool confirming deployment and pod reach Running state (`src/tools/verify_recovery.py`).
- [x] **[P0]** Implement `get_autoscaler_status`, `get_node_pool_status`, and `get_recovery_status` (`src/tools/autoscaler_status.py`, `src/tools/recovery_status.py`).
- [x] **[P1]** Implement auxiliary `retry_agent` tool outside the canonical auto-scheduling flow (`src/tools/retry_agent.py`).
- [x] **[P0]** Implement `RecoveryTracker` state machine and audit trail (`src/autoscaler/recovery_tracker.py`).
- [x] **[P0]** Complete comprehensive test suite with 80/80 passing tests (`tests/test_autoscaler_policy.py`, `tests/test_simulated_autoscaler.py`, `tests/test_phase3_tools.py`).

---

## Phase 4 (AI Reasoning & AWS Bedrock Integration) - Completed
- [x] **[P0]** Model configuration management (`BEDROCK_MODEL_ID`, region, timeout, tokens, temperature, mock mode) (`src/config/settings.py`).
- [x] **[P0]** Abstract `BedrockReasoner` interface and data models (`RecoveryContext`, `RecoveryProposal`, `ActionType`) (`src/bedrock/provider.py`, `src/bedrock/models.py`).
- [x] **[P0]** Proposal schema validator enforcing action allowlist and positive integer target nodes (`src/bedrock/validator.py`).
- [x] **[P0]** Explicit `DeterministicFallbackReasoner` mapping deterministic classifications to safe proposals (`src/bedrock/fallback_reasoner.py`).
- [x] **[P0]** High-fidelity `MockBedrockReasoner` for offline testing and deterministic simulation (`src/bedrock/mock_reasoner.py`).
- [x] **[P0]** Production `BedrockRuntimeReasoner` using `boto3` Converse API with fallback hooks (`src/bedrock/bedrock_reasoner.py`).
- [x] **[P0]** Orchestrator `SentinelRecoveryReasoner` managing primary reasoner, schema validation, and fallback (`src/bedrock/orchestrator.py`).
- [x] **[P0]** Implement `reason_recovery` MCP tool and register in JSON-RPC server (`src/tools/reason_recovery.py`, `src/server/mcp_server.py`).
- [x] **[P0]** Update health check with `dependencies.bedrock` status (`src/server/health.py`).
- [x] **[P0]** Automated test suite with 94/94 passing tests (14 Phase 4 tests) (`tests/test_bedrock_reasoner.py`).


---

## Phase 5 (DronaHQ Streamable HTTP Transport Implementation) - Completed
- [x] **[P0]** Implement `HttpMCPServer` Streamable HTTP transport adapter in `src/server/http_server.py`.
- [x] **[P0]** Implement constant-time `SENTINEL_API_KEY` authentication (`secrets.compare_digest`) with Bearer, X-Sentinel-API-Key, and X-API-Key header support.
- [x] **[P0]** Add fail-safe startup validation preventing unauthenticated HTTP endpoints in production/dev (`src/config/settings.py`).
- [x] **[P0]** Add `--http` and `--stdio` transport switches to CLI entrypoint (`src/main.py`).
- [x] **[P0]** Author `docs/PHASE5_DRONAHQ_IMPLEMENTATION.md` and `docs/DRONAHQ_SETUP.md`.
- [x] **[P0]** Create standalone compatibility test script `scripts/test_mcp_http_compatibility.py`.
- [x] **[P0]** Expand test suite to 109/109 passing unit and integration tests (`tests/test_http_server.py`).


---

## Phase 6 (End-to-End Recovery Verification & Demo) - Planned
- [ ] **[P0]** Build end-to-end demo script simulating capacity exhaustion and autonomous recovery.
- [ ] **[P1]** Validate complete autonomous loop against saturated cluster.
- [ ] **[P2]** Produce final walkthrough documentation and demo presentation assets.
