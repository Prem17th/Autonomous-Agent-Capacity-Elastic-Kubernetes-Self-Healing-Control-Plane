# Phase 5 DronaHQ Integration Discovery

## Executive Summary
This document provides the discovery, architecture inspection, and compatibility analysis for integrating **Nasiko Sentinel** with **DronaHQ** in **Phase 5**.

Following strict Phase 5 discovery constraints:
- **No implementation code has been written.**
- **No architectural redesign or changes have been made.**
- **No DronaHQ credentials or API tokens have been inspected or stored.**

---

## 1. Current MCP Architecture

Nasiko Sentinel currently implements a standards-compliant **Model Context Protocol (MCP)** server conforming to the `2024-11-05` protocol specification:

### Protocol & Dispatch Details
- **Specification Version:** `2024-11-05`
- **Transport Mechanism:** Standard I/O (`stdio`) via `src/server/mcp_server.py`.
- **Message Encoding:** JSON-RPC 2.0 (`jsonrpc: "2.0"`).
- **Supported Methods:**
  - `initialize`: Capability negotiation (`protocolVersion`, `capabilities`, `serverInfo`).
  - `ping`: Liveness probe (`{}`).
  - `tools/list`: Dynamic discovery of all registered tools with JSON Schema input definitions.
  - `tools/call`: Dispatches tool requests to structured internal handlers and formats results in MCP standard content blocks (`[{ "type": "text", "text": "..." }]`).

### Registered Tools (14 Active Tools)
1. `get_health`: Foundation & dependency reachability probe.
2. `get_agent_status`: Nasiko UUID workload & pod status observation.
3. `get_pending_pods`: Unschedulable pod listing and request normalization.
4. `get_pod_events`: Pod event extraction & `FailedScheduling` analysis.
5. `get_node_capacity`: Cluster and per-node compute allocatables.
6. `diagnose_capacity`: Deterministic classification of capacity bottlenecks.
7. `request_scale_up`: Controlled autoscaling with safety policy enforcement.
8. `wait_for_capacity`: Asynchronous capacity polling and readiness check.
9. `get_autoscaler_status`: Autoscaler provider metrics and health.
10. `get_node_pool_status`: Node pool instance counts and limits.
11. `get_recovery_status`: Recovery audit trails and lifecycle state machine.
12. `verify_agent_recovery`: Confirms agent deployment and pod reached `Running`.
13. `retry_agent`: Auxiliary deployment reconciliation trigger.
14. `reason_recovery`: AI reasoning proposal generation with deterministic fallback.

---

## 2. DronaHQ Requirements

Based on official DronaHQ documentation and platform specifications:

### DronaHQ Integration Characteristics
- **Platform Architecture:** DronaHQ is a cloud SaaS low-code / workflow / AI agent builder platform.
- **MCP Client / Server Architecture:** DronaHQ connects to external tools and backends using network protocols (HTTP REST APIs, DronaHQ RPC, and HTTP/SSE for remote MCP servers).
- **Transport Requirements:** DronaHQ requires a network-accessible transport (**HTTP POST / Server-Sent Events (SSE)** or **REST API Webhook**). DronaHQ **does not support subprocess `stdio` execution** to remote host environments.
- **Tool Discovery & Invocation:** 
  - Over MCP: Calls `tools/list` on initialization or configuration to discover tools dynamically.
  - Over REST Connector: Maps specific endpoints (e.g. `POST /api/tools/{tool_name}`) with configured JSON payload schemas.
- **Network Reachability:**
  - For DronaHQ Cloud SaaS: Requires an externally reachable HTTPS endpoint (e.g. through an ingress, reverse proxy, or secure tunneling mechanism such as ngrok/Cloudflare tunnel during local development/demos).
  - For DronaHQ On-Prem / VPC Agent: Can communicate directly with internal HTTP endpoints within the private network.
- **Authentication Support:** DronaHQ REST/RPC connectors support API Keys (Header / Query / Body), Bearer Tokens, Basic Auth, OAuth2, and Custom Headers.

*Sources:*
- DronaHQ Connector & Authentication Documentation: `https://community.dronahq.com` / `https://www.dronahq.com`
- DronaHQ Custom Connector & REST API Guide: `https://docs.dronahq.com`
- Model Context Protocol Specification (Transports: stdio, SSE): `https://modelcontextprotocol.io`

---

## 3. Compatibility Matrix

| Capability | Current Sentinel MCP | DronaHQ Requirement | Status |
| :--- | :--- | :--- | :--- |
| **Protocol Format** | JSON-RPC 2.0 | JSON-RPC 2.0 / REST | **COMPATIBLE** |
| **Tool Schema Standard** | JSON Schema (Draft-07) | JSON Schema | **COMPATIBLE** |
| **Capability Negotiation** | `initialize`, `ping`, `tools/list`, `tools/call` | Standard MCP lifecycle / REST queries | **COMPATIBLE** |
| **Transport Layer** | `stdio` (Standard Input/Output) | HTTP / SSE / REST Webhook | **ADAPTER REQUIRED** |
| **Network Reachability** | Local process stdin/stdout | Network HTTP(S) endpoint | **ADAPTER REQUIRED** |
| **Authentication** | Process boundary (OS-level) | HTTP Header API Key / Bearer Token | **ADAPTER REQUIRED** |
| **Zero-Credential Exposure**| Backend encapsulates all K8s & AWS keys | Frontend receives only tool outputs | **COMPATIBLE** |

---

## 4. Transport Compatibility

### Finding
Sentinel's MCP engine currently listens and writes on `stdio` (`sys.stdin` / `sys.stdout`). Because DronaHQ operates over network connections, direct `stdio` connection is incompatible without a network transport adapter.

### Classification
**B. COMPATIBLE WITH CONFIGURATION/TRANSPORT ADAPTER**

### Minimum Required Transport Adapter
The internal MCP server design already separates the message dispatcher (`handle_request(dict) -> dict`) from the transport loop. To enable DronaHQ connectivity, Sentinel only needs a lightweight HTTP/SSE transport adapter:
1. `POST /mcp`: Receives JSON-RPC 2.0 requests from DronaHQ and returns JSON-RPC responses.
2. `GET /sse`: (Optional) Provides SSE event stream for streaming progress.
3. `POST /api/tools/{tool_name}`: (Optional) Direct REST endpoint wrapper for non-MCP DronaHQ Custom Connectors.

---

## 5. Authentication Requirements

- **DronaHQ Credentials:**
  > *Credential required — not inspected/exposed.*
  (Strictly compliant with the project security policy: no DronaHQ tokens or API keys have been viewed, copied, stored, or committed).
- **Sentinel Inbound Authentication:**
  - For Phase 5, Sentinel should enforce an API key header (e.g. `X-Sentinel-API-Key` or `Authorization: Bearer <token>`) configured via `Settings` (`SENTINEL_API_KEY`).
  - Unauthenticated requests to Sentinel HTTP endpoints are rejected with HTTP 401 Unauthorized.

---

## 6. Security Considerations

1. **Zero Credential Leakage to DronaHQ:**
   - DronaHQ is treated strictly as an external presentation and operator approval plane.
   - Kubernetes cluster certificates, tokens, ServiceAccount secrets, and AWS Bedrock credentials **remain 100% confined to the Sentinel backend**.
   - DronaHQ only receives structured diagnostic summaries, cluster metrics, and recovery proposals.
2. **Authoritative Safety Enforcement:**
   - Any recovery action triggered from DronaHQ (`request_scale_up`, `reason_recovery`) continues to pass through the authoritative `RecoveryPolicyEngine`.
   - Even if a DronaHQ operator or UI script attempts to scale 100 nodes, the backend policy engine rejects the request with `POLICY_DENIED`.
3. **Localhost & Tunneling Security:**
   - In hackathon/demo environments using tunnel gateways (e.g., ngrok), all traffic must be secured via HTTPS with TLS encryption and Sentinel API Key header verification.

---

## 7. Required Changes (For Phase 5 Implementation)

To support DronaHQ in Phase 5, the following minimal, additive changes will be required:

1. **HTTP/SSE Transport Adapter (`src/server/http_server.py`):**
   - Lightweight HTTP server using standard Python library (`http.server` / `asyncio`) or minimal framework.
   - Routes `POST /mcp` to `MCPServer.handle_request()`.
   - Routes `GET /health` to `get_health_status()`.
2. **Configuration Extension (`src/config/settings.py`):**
   - Enable `MCP_TRANSPORT=http` (already defined in Settings, ready for activation).
   - Add `SENTINEL_API_KEY` for inbound webhook authorization.
3. **CLI Entrypoint Support (`src/main.py`):**
   - Launch HTTP transport when `MCP_TRANSPORT=http` or `--http` flag is passed.
4. **Documentation & DronaHQ Connector Spec:**
   - Provide OpenAPI / cURL specs for importing into DronaHQ Custom Connector builder.

---

## 8. Recommended Integration Boundary

```
┌────────────────────────────────────────────────────────┐
│                   DronaHQ SaaS Platform                │
│  - Operator Dashboard & Approvals                     │
│  - Diagnostic Visualizations & Timelines               │
│  - Custom Connector / MCP Integration                  │
└───────────────────────────┬────────────────────────────┘
                            │ HTTPS (Bearer / API Key Auth)
                            ▼
┌────────────────────────────────────────────────────────┐
│        Nasiko Sentinel HTTP / MCP Gateway              │
│  - HTTP / SSE Transport Adapter                        │
│  - Inbound Authentication Validation                   │
│  - JSON-RPC 2.0 Dispatcher                             │
└───────────────────────────┬────────────────────────────┘
                            │ In-Memory Dispatch
                            ▼
┌────────────────────────────────────────────────────────┐
│             Sentinel Authoritative Engine              │
│  - Deterministic Observation & Diagnosis (Phase 2)     │
│  - AWS Bedrock AI Reasoning & Fallback (Phase 4)       │
│  - Recovery Policy Engine & Tracker (Phase 3)          │
│  - Kubernetes & Autoscaler Providers (Phase 2/3)       │
└────────────────────────────────────────────────────────┘
```

---

## 9. Test Suite Verification

The existing automated test suite was executed prior to producing this report:

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

- **Total Tests:** 94
- **Passed:** 94
- **Failed:** 0
- **Errors:** 0
- **Duration:** 1.44s
- **Zero regressions.**

---

## 10. Phase 5 Implementation Plan (Draft / Pending Approval)

Once approved by the Architect, Phase 5 will proceed in three clean sub-steps:
1. **Step 5.1:** Implement `HttpMCPServer` transport adapter in `src/server/` with API Key validation and unit tests.
2. **Step 5.2:** Provide DronaHQ Custom Connector cURL / OpenAPI schema exports and connector documentation.
3. **Step 5.3:** Verify end-to-end tool invocation over HTTP and validate that all 14 tools remain fully functional without breaking `stdio` compatibility.

---

*Report prepared and submitted. Standing by for Architect review.*

