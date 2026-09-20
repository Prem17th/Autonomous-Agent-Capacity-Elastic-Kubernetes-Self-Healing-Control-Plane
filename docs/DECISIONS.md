# Architectural Decision Records (ADRs)

## ADR-001: Backend Language Selection
- **Status:** Accepted
- **Context:** Aegis Sentinel requires a robust, maintainable backend for its MCP server that easily integrates with Kubernetes APIs, AWS Bedrock SDK (`boto3`), and standardized Model Context Protocol tools.
- **Decision:** Use Python 3 (standard library + minimal dependencies).
- **Rationale:**
  - Python is natively available in the host environment (Python 3.14.7).
  - Python offers first-class official SDKs for both Kubernetes (`kubernetes`) and AWS Bedrock (`boto3`).
  - Zero-compilation overhead allows rapid iteration, automated unit testing, and cross-platform execution.

---

## ADR-002: Model Context Protocol (MCP) Foundation Approach
- **Status:** Accepted
- **Context:** The server must act as a clean MCP tool provider to AI orchestrators (Bedrock / DronaHQ).
- **Decision:** Implement a lightweight, compliant JSON-RPC 2.0 MCP server over `stdio` transport.
- **Rationale:**
  - Provides full compliance with the Model Context Protocol specification (`initialize`, `ping`, `tools/list`, `tools/call`).
  - Decouples the protocol interface from transport details, enabling easy extension to SSE or HTTP in later phases without redesign.

---

## ADR-003: Subpackage Naming (`src/logger/`)
- **Status:** Accepted
- **Context:** Standard Python includes a top-level built-in library named `logging`. Creating a subpackage named `src/logging` can create shadowing collisions when scripts are executed directly.
- **Decision:** Name the logging module `src/logger/` to maintain absolute import clarity while preserving the proposed architectural grouping.

---

## ADR-004: Exclusion of Database, Redis, and Vector DB in Phase 1 & 2
- **Status:** Accepted
- **Context:** Observation and diagnosis tools query the Kubernetes API and Aegis REST API directly as live sources of truth.
- **Decision:** Do not add databases, key-value stores, or caches in Phase 1 & 2.
- **Rationale:** Direct API queries guarantee zero cache staleness and prevent divergence between cluster state and Sentinel observations.

---

## ADR-005: Deterministic Bottleneck Classification in `diagnose_capacity`
- **Status:** Accepted
- **Context:** Capacity diagnosis requires high accuracy when classifying scheduling failure reasons before handing diagnostic payloads to LLMs.
- **Decision:** Perform root-cause classification deterministically in code (`src/kubernetes/adapter.py`) rather than delegating basic parsing to an LLM.
- **Rationale:**
  - Standard Kubernetes scheduler messages (`Insufficient cpu`, `Insufficient memory`, `Too many pods`, `Untolerated taint`) follow well-defined patterns.
  - Deterministic classification produces reliable, testable outputs with zero token latency and zero hallucination risk.
  - Upstream LLMs (Bedrock Claude 3.5 in Phase 4) will receive this structured classification to reason about complex multi-step remediation strategies.

---

## ADR-006: Kubernetes Adapter Layer & Client Seam
- **Status:** Accepted
- **Context:** MCP tool handlers should not be coupled directly to raw Kubernetes API calls or SDK details.
- **Decision:** Introduce `KubernetesAdapter` backed by `BaseKubeClient` (`KubernetesClient` for live cluster, `MockKubernetesClient` for test suites).
- **Rationale:** Enables 100% test coverage without requiring Docker Desktop, Minikube, or live cloud infrastructure during local unit test runs.

---

## ADR-007: Authoritative Scheduler Evidence Rule
- **Status:** Accepted
- **Context:** When determining whether a pod can be scheduled or why it failed, calculating aggregate cluster allocatable capacity alone is insufficient (e.g. fragmentation, per-node boundaries, taints, affinity).
- **Decision:** Kubernetes `default-scheduler` signals (`FailedScheduling` events, `PodScheduled=False`, and scheduler condition messages) must remain the primary authoritative evidence. Node-level capacity calculation is strictly supporting context.
- **Rationale:** Prevents false-negative scheduling assumptions and mirrors genuine Kubernetes scheduler semantics.

---

## ADR-008: Health Check Service Health vs Dependency Separation
- **Status:** Accepted
- **Context:** If the target Kubernetes cluster is unreachable or offline during local execution, the Sentinel MCP server itself is still operational and capable of serving requests/reporting status.
- **Decision:** `get_health` returns `status: "ok"` for the Sentinel service itself, while reporting Kubernetes connectivity under a separate `dependencies.kubernetes` section.
- **Rationale:** Aligns with standard cloud-native health probe conventions and allows graceful degradation.

---

## ADR-009: Provider Abstraction & Simulation for Controlled Autoscaling
- **Status:** Accepted
- **Context:** In Phase 3, AWS EKS credentials and remote Karpenter/ASG instances may not be provisioned or configured on the local host.
- **Decision:** Implement `AutoscalerProvider` interface with a concrete `SimulatedAutoscalerProvider` that emulates provisioning delays, node readiness, and mock capacity injection into the KubernetesAdapter.
- **Rationale:** Guarantees full offline testability and robust mock validation while maintaining an interface that directly swappable for production `KarpenterProvider` / `ClusterAutoscalerProvider` once live AWS/EKS credentials are provided.

---

## ADR-010: Normal Recovery Flow & Independent Auto-Scheduling Verification
- **Status:** Accepted
- **Context:** Once new worker nodes join a Kubernetes cluster in `Ready` state, the native `default-scheduler` automatically re-evaluates unscheduled `Pending` pods and places them on the newly available nodes.
- **Decision:** The canonical recovery flow is `diagnose_capacity` → policy validation → `request_scale_up` → `wait_for_capacity` → `verify_agent_recovery`. The `retry_agent` tool is maintained as an auxiliary/manual tool and is NOT part of the standard automated recovery flow.
- **Rationale:** Conforms directly to Kubernetes declarative reconciliation principles and prevents unnecessary pod terminations.

---

## ADR-011: AWS Bedrock Reasoner & Proposal Model
- **Status:** Accepted
- **Context:** Phase 4 requires intelligent reasoning over deterministic capacity diagnoses and cluster allocatable headroom to propose recovery actions. However, direct agent execution of AWS CLI or shell commands introduces severe reliability and security risks.
- **Decision:** Bedrock only formulates a structured `RecoveryProposal` (`ActionType.NO_ACTION` or `ActionType.REQUEST_SCALE_UP`). It has no direct tool execution privileges or shell access. Model ID is configurable via `BEDROCK_MODEL_ID` and never hardcoded.
- **Rationale:** Guarantees zero unconstrained mutations, strict schema validation via `ProposalValidator`, and strict policy engine enforcement before any infrastructure is provisioned.

---

## ADR-012: Explicit Deterministic Fallback & Policy Authorization
- **Status:** Accepted
- **Context:** AWS Bedrock may become unreachable, throttled, or unconfigured during local development or network partitions.
- **Decision:** Sentinel provides an automatic, transparent `DeterministicFallbackReasoner` wrapped inside `SentinelRecoveryReasoner`. Whenever Bedrock fails or is unavailable, the fallback reasoner maps deterministic diagnoses into safe standard scale proposals, explicitly returning `"reasoning_source": "deterministic_fallback"`. Furthermore, all proposals (whether from Bedrock or fallback) must pass the `RecoveryPolicyEngine` before execution.
- **Rationale:** Guarantees 100% service uptime, observable failure modes, and unconditional policy supremacy over LLM outputs.

---

## ADR-013: Streamable HTTP Network Transport for DronaHQ Integration
- **Status:** Accepted
- **Context:** DronaHQ connects to external MCP tools over network transports (Streamable HTTP or SSE) rather than local OS subprocess `stdio` pipes.
- **Decision:** Implement `HttpMCPServer` in `src/server/http_server.py` as an authenticated transport adapter wrapping the existing `MCPServer.handle_request()` dispatcher. Secure the endpoint with `SENTINEL_API_KEY` validated via constant-time comparison (`secrets.compare_digest`).
- **Rationale:** Preserves the core MCP protocol, tool schemas, and safety policy engine completely unchanged, while providing a secure network gateway for DronaHQ without exposing Kubernetes or AWS credentials.


