# Aegis Sentinel - Phase 4 AWS Bedrock Reasoning Design Specification

## Executive Summary
This document defines the architectural and technical design for **Phase 4: AI Reasoning & AWS Bedrock Integration** for Aegis Sentinel. It establishes how Sentinel leverages large language model (LLM) reasoning to synthesize deterministic Kubernetes capacity diagnostics into structured remediation plans while strictly enforcing safety guardrails, policy engine supremacy, zero-hallucination execution, and deterministic fallback.

---

## 1. Classification Index

Every technical finding and architectural specification in this document is strictly classified:
- **`[VERIFIED]`**: Empirically proven from local inspection, environment tests, or Kubernetes/AWS API specs.
- **`[INFERENCE]`**: Logical deduction based on verified evidence.
- **`[DESIGN PROPOSAL]`**: Recommended architectural design for Phase 4 implementation.
- **`[UNKNOWN]`**: External cloud dependency or account permission requiring organizer/user configuration.

---

## 2. Environment & AWS Inspection Findings

| Item | Status | Classification | Details |
| :--- | :--- | :--- | :--- |
| **AWS CLI** | Not installed / Not in PATH | `[VERIFIED]` | `aws : The term 'aws' is not recognized` returned on Windows host. |
| **AWS Credentials** | Not configured | `[VERIFIED]` | No `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`, or `~/.aws/credentials` exist. |
| **AWS Region** | None set | `[VERIFIED]` | `AWS_REGION` is unset (defaults to `None` in `Settings`). Target region: `us-east-1` or `us-west-2`. |
| **Bedrock Account Access** | Unknown | `[UNKNOWN]` | Cannot be queried until AWS credentials or IAM role are provided. |
| **Accessible Bedrock Models**| Unknown | `[UNKNOWN]` | Model enablement in AWS account (Claude 3.5 Sonnet / Haiku / Nova) pending cloud credentials. |
| **Python SDK (`boto3`)** | Not installed | `[VERIFIED]` | `ModuleNotFoundError: No module named 'boto3'` in local Python environment. |

---

## 3. Preserved Architecture & Execution Boundary

```
                     ┌─────────────────────────────────────────┐
                     │         Kubernetes Infrastructure       │
                     └────────────────────┬────────────────────┘
                                          │
                                          ▼
                     ┌─────────────────────────────────────────┐
                     │ Sentinel Deterministic Observation      │
                     │ - get_pending_pods / get_pod_events     │
                     │ - get_node_capacity                     │
                     │ - diagnose_capacity (Deterministic)     │
                     └────────────────────┬────────────────────┘
                                          │
                                          ▼
                     ┌─────────────────────────────────────────┐
                     │ Structured Facts Payload                │
                     │ (Sanitized, Whitelisted Parameters)     │
                     └────────────────────┬────────────────────┘
                                          │
                                          ▼
                     ┌─────────────────────────────────────────┐
                     │ AWS Bedrock AI Reasoning                │
                     │ (Claude 3.5 Haiku / Sonnet via boto3)   │
                     │ or MockBedrockClient (Offline Fallback) │
                     └────────────────────┬────────────────────┘
                                          │
                                          ▼
                     ┌─────────────────────────────────────────┐
                     │ Structured Action Proposal              │
                     │ (Strict JSON Schema: action, pool, etc) │
                     └────────────────────┬────────────────────┘
                                          │
                                          ▼
                     ┌─────────────────────────────────────────┐
                     │ RECOVERY POLICY ENGINE (Authoritative)  │
                     │ - Enforces max 2 nodes / req            │
                     │ - Enforces max 10 cluster nodes         │
                     │ - Enforces 120s cooldown debounce       │
                     │ - Enforces rate limit (3 ops/15min)     │
                     │ - Enforces node pool whitelist          │
                     └────────────────────┬────────────────────┘
                                          │ (Approved)
                                          ▼
                     ┌─────────────────────────────────────────┐
                     │ MCP Server Actions & AutoscalerProvider │
                     │ (Controlled mutation: request_scale_up) │
                     └─────────────────────────────────────────┘
```

> [!CAUTION]
> **Strict Execution Guardrails:**
> 1. Bedrock **MUST NOT** receive raw shell access, arbitrary Kubernetes API tokens, or AWS CLI execution privileges.
> 2. Bedrock **MUST NOT** directly execute infrastructure mutations.
> 3. Bedrock produces **structured JSON action proposals only**.
> 4. The **Recovery Policy Engine remains 100% authoritative**. Any Bedrock proposal violating safety bounds is intercepted and denied with `POLICY_DENIED`.

---

## 4. Architectural Analysis & Technical Questions

### Q1: Is AWS CLI available?
- **Result:** No `[VERIFIED]`. The Windows shell does not have `aws` in PATH.

### Q2: Are AWS credentials available?
- **Result:** No `[VERIFIED]`. Environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`) are unset and `~/.aws/` does not exist.

### Q3: What AWS region is configured, if any?
- **Result:** None `[VERIFIED]`. `AWS_REGION` is currently `None`. Default recommendation: `us-east-1` (US East N. Virginia) or `us-west-2` (Oregon) where Anthropic Claude models on Bedrock have high availability `[DESIGN PROPOSAL]`.

### Q4: Is Amazon Bedrock available to this account/environment?
- **Result:** Unknown `[UNKNOWN]`. Cannot be verified without AWS credentials. Sentinel will implement a dual-mode client (`BedrockClient` + `MockBedrockClient`) so Phase 4 runs 100% offline in local development/tests `[DESIGN PROPOSAL]`.

### Q5: Which Bedrock models are actually accessible?
- **Result:** Unknown `[UNKNOWN]`. Pending AWS model access permissions in the target account.

### Q6: What model is appropriate for structured reasoning/tool selection?
- **Primary Recommendation:** `anthropic.claude-3-5-haiku-20241022-v1:0` `[DESIGN PROPOSAL]`.
  - *Rationale:* Fastest time-to-first-token (< 800ms), low cost (~\$0.001 per recovery), and strong structured JSON / tool calling compliance.
- **Secondary / Heavy Reasoning:** `anthropic.claude-3-5-sonnet-20241022-v2:0` `[DESIGN PROPOSAL]`.
  - *Rationale:* Ideal for ambiguous scheduling failures requiring complex cross-node topology analysis.
- **Alternative AWS Model:** `amazon.nova-pro-v1:0` or `amazon.nova-lite-v1:0` `[DESIGN PROPOSAL]`.

### Q7: What AWS SDK should Sentinel use?
- **Result:** Python `boto3` (`bedrock-runtime` client using `converse` or `invoke_model` API) `[DESIGN PROPOSAL]`.
- For offline test execution and zero-dependency environments, Sentinel will define an abstract `BedrockReasoner` interface with a `MockBedrockReasoner` fallback `[DESIGN PROPOSAL]`.

### Q8: How should authentication be handled?
- **Result:** Standard AWS credential resolution chain:
  1. In-Cluster (EKS): EKS Pod Identity or IAM Roles for Service Accounts (IRSA) via `AWS_WEB_IDENTITY_TOKEN_FILE`.
  2. Local Cloud: Environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`) or `~/.aws/credentials` / `~/.aws/config` profile.
  3. Offline / Test: `BEDROCK_MOCK_MODE=true` (simulates LLM reasoning deterministically without network calls) `[DESIGN PROPOSAL]`.

### Q9: How should model configuration be represented in settings?
- **Result:** Extend `Settings` in `src/config/settings.py` `[DESIGN PROPOSAL]`:
  - `aws_region: Optional[str] = "us-east-1"`
  - `bedrock_model_id: str = "anthropic.claude-3-5-haiku-20241022-v1:0"`
  - `bedrock_max_tokens: int = 1024`
  - `bedrock_temperature: float = 0.0` (zero temperature for deterministic reasoning)
  - `bedrock_timeout_seconds: int = 15`
  - `bedrock_mock_mode: bool = False` (auto-enabled when credentials absent)

### Q10: What structured output/tool-calling capability is available?
- **Result:** Bedrock Converse API Tool Calling (`toolConfig`) or strict JSON mode schema prompting. Sentinel will enforce a strict JSON output schema validated against a Pydantic/dataclass schema parser `[DESIGN PROPOSAL]`.

### Q11: What should happen if Bedrock is unavailable?
- **Result:** **Automatic Deterministic Fallback (`SentinelFallbackReasoner`)** `[DESIGN PROPOSAL]`.
  - If AWS credentials are missing, Bedrock API returns HTTP 5xx, or network times out:
  - Sentinel immediately falls back to its deterministic rule engine (`diagnose_capacity` classification → mapped recovery action).
  - Example: `insufficient_cpu` → `request_scale_up(node_pool='default', target_nodes=1)`.
  - Service remains 100% available; response payload flags `"reasoning_source": "deterministic_fallback"`.

### Q12: How should timeout/retry be handled?
- **Result:**
  - Socket timeout: 15 seconds.
  - Retries: Maximum 1 retry with exponential backoff on transient HTTP 429 (Throttling) or 503 (ServiceUnavailable).
  - Circuit Breaker: If 2 consecutive Bedrock calls fail, trip to deterministic fallback for 60 seconds to prevent blocking recovery loops `[DESIGN PROPOSAL]`.

### Q13: What information from Sentinel should be passed to Bedrock?
- **Result:** Structured, sanitized facts ONLY `[DESIGN PROPOSAL]`:
  ```json
  {
    "agent_id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
    "pod_name": "agent-pending-cpu",
    "namespace": "aegis-agents",
    "resource_requests": { "cpu_milli": 2000, "memory_bytes": 1073741824 },
    "deterministic_diagnosis": {
      "classification": "insufficient_cpu",
      "reason": "InsufficientCPU",
      "message": "0/2 nodes available: 2 Insufficient cpu."
    },
    "cluster_capacity": {
      "total_nodes": 2,
      "ready_nodes": 2,
      "allocatable_cpu_milli": 3860,
      "available_cpu_milli": 3360,
      "allocatable_memory_bytes": 16357785600,
      "available_memory_bytes": 15820914688
    },
    "available_node_pools": [
      { "name": "default", "instance_types": ["t3.xlarge", "m5.xlarge"], "ready_nodes": 2, "max_nodes": 10 },
      { "name": "general-compute", "instance_types": ["c5.2xlarge"], "ready_nodes": 2, "max_nodes": 10 },
      { "name": "memory-optimized", "instance_types": ["r5.2xlarge"], "ready_nodes": 1, "max_nodes": 6 }
    ],
    "policy_constraints": {
      "max_nodes_per_request": 2,
      "max_cluster_nodes": 10,
      "cooldown_active": false
    }
  }
  ```

### Q14: What exact structured response should Bedrock return?
- **Result:** Standardized JSON structure `[DESIGN PROPOSAL]`:
  ```json
  {
    "analysis": "Agent requires 2000m CPU. Existing nodes have 1430m and 1930m available individually; neither single node has enough contiguous capacity. Scale-up of default node pool by +1 node is required.",
    "root_cause": "insufficient_cpu",
    "action": "request_scale_up",
    "parameters": {
      "node_pool": "default",
      "target_nodes": 1,
      "reason": "insufficient_cpu",
      "requested_cpu": "2000m",
      "agent_id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"
    },
    "estimated_recovery_time_seconds": 60,
    "confidence": 0.98,
    "human_explanation": "Scaled up 'default' node pool by 1 node to provide 4000m CPU headroom for pending agent."
  }
  ```

### Q15: How will the Recovery Policy Engine validate Bedrock's proposed action?
- **Result:** The policy engine intercepts the action and parameters proposed by Bedrock BEFORE any MCP tool handler or cloud mutation is triggered.
  - Validates `node_pool` in whitelist.
  - Validates `target_nodes <= 2`.
  - Validates `current_nodes + target_nodes <= 10`.
  - Validates cooldown debounce and rate limits.
  - If invalid: rejects immediately with `POLICY_DENIED` and does NOT execute the scaling action `[DESIGN PROPOSAL]`.

### Q16: How will prompt injection / untrusted Kubernetes text be handled?
- **Result:**
  1. **Strict Input Whitelist:** Only typed metrics (integers, floats, enums, normalized strings) are passed into the prompt template.
  2. **Sanitization:** Freeform pod annotations, user labels, and container image names are sanitized or stripped.
  3. **Delimited XML Isolation:** Inputs are enclosed in `<cluster_context>` tags.
  4. **System Instruction Hierarchy:** System prompt instructs the model to ignore any instructions found within the XML context tags.
  5. **Schema Validation:** Model output is validated against strict JSON schema; non-conforming responses are discarded and redirected to deterministic fallback `[DESIGN PROPOSAL]`.

### Q17: What logging/redaction rules are required?
- **Result:**
  - Raw prompts and LLM completions logged only at `DEBUG` log level.
  - All AWS tokens and credentials redacted by `RedactingFormatter`.
  - `INFO` audit logs capture structured action metadata (`action`, `node_pool`, `target_nodes`, `confidence`, `latency_ms`) without leaking raw context strings `[DESIGN PROPOSAL]`.

### Q18: What cost/latency safeguards are needed?
- **Result:**
  - **Max Output Tokens:** Capped at `1024` tokens.
  - **Temperature:** Set to `0.0` for fastest decoding and zero randomness.
  - **Deduplication / Debounce Cache:** If an agent pod was diagnosed within the last 60 seconds and cluster state has not changed, reuse cached reasoning without calling Bedrock again.
  - **Estimated Cost per Recovery:** ~1,200 input tokens + 300 output tokens on Claude 3.5 Haiku = **\$0.00075** (less than 1/10th of a cent) `[INFERENCE]`.

---

## 5. Proposed Phase 4 Modules & Architecture

```
src/
  ai/
    __init__.py
    bedrock_client.py     # Boto3 Bedrock-Runtime wrapper with Converse API
    mock_bedrock.py       # High-fidelity mock LLM reasoner for offline execution
    prompts.py            # Parameterized system prompt & XML context templates
    models.py             # ReasoningRequest, ReasoningPlan, ActionProposal
    reasoner.py           # Orchestrator with timeout, fallback, and policy linkage
```

---

## 6. Verification Status of Current Test Suite

Before advancing, the Phase 3 test suite was executed to confirm complete stability:

```
python -m unittest discover -s tests -p "test_*.py" -v
Ran 80 tests in 1.237s
OK
```

- **0 Regressions.**
- **80/80 Unit and Integration Tests Passing.**

---

## 7. Next Steps & Summary

This concludes the **Phase 4 Environment & Architectural Design Inspection**. 

No source code in `src/` was modified. No AWS credentials were assumed.

**Standing by for ChatGPT architecture review of `docs/PHASE4_BEDROCK_DESIGN.md`.**

