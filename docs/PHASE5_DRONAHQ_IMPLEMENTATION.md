# Phase 5: DronaHQ Streamable HTTP Transport Implementation

## 1. Overview & Architectural Role
Phase 5 introduces the **Streamable HTTP Network Transport Adapter** (`HttpMCPServer`) for Nasiko Sentinel, enabling remote AI orchestrators, custom frontends, and **DronaHQ AI Agents** to interact with Sentinel's Model Context Protocol (MCP) server over standard HTTP without compromising security, policy supremacy, or existing `stdio` transport capabilities.

---

## 2. Transport Architecture

```
┌────────────────────────────────────────────────────────┐
│                   DronaHQ AI Agent                     │
│  (Remote Low-Code / Workflow / Operator Dashboard)     │
└───────────────────────────┬────────────────────────────┘
                            │
                            │ Streamable HTTP (JSON-RPC 2.0)
                            │ Headers: Authorization: Bearer <SENTINEL_API_KEY>
                            │ Endpoint: POST http://<host>:<port>/mcp
                            ▼
┌────────────────────────────────────────────────────────┐
│           HttpMCPServer (Transport Adapter)            │
│  - Constant-Time API Key Authentication                │
│  - Safe JSON & Content-Length Parsing                  │
│  - Zero Traceback / Secret Redaction                   │
└───────────────────────────┬────────────────────────────┘
                            │ In-Memory Call
                            ▼
┌────────────────────────────────────────────────────────┐
│            Existing MCPServer.handle_request()         │
│  - JSON-RPC 2.0 Protocol Dispatcher                    │
│  - Tools: initialize, ping, tools/list, tools/call     │
└───────────────────────────┬────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│ Kubernetes    │   │ AWS Bedrock / │   │ Recovery      │
│ Observation   │   │ Fallback      │   │ Policy Engine │
│ (Phase 2)     │   │ (Phase 4)     │   │ (Phase 3)     │
└───────────────┘   └───────────────┘   └───────────────┘
```

---

## 3. Protocol & Transport Specifications

| Feature | Supported Specification | Notes |
| :--- | :--- | :--- |
| **Transport** | **Streamable HTTP** (`POST /mcp`, `GET /health`) | Primary remote transport |
| **Protocol** | JSON-RPC 2.0 (MCP version `2024-11-05`) | Exact same schemas as `stdio` |
| **Authentication** | `Authorization: Bearer <key>`, `X-Sentinel-API-Key`, `X-API-Key` | Constant-time validation |
| **Alternative Transport** | `stdio` | Preserved as default CLI runtime |
| **SSE Support** | *Not implemented in this phase* | Available if required by future specs |

---

## 4. Endpoints & Methods

### A. Health & Readiness Probe: `GET /health`
Returns service status, environment, active components, and dependency readiness.
- **Request:** `GET http://127.0.0.1:8000/health`
- **Response:**
  ```json
  {
    "status": "ok",
    "service": "nasiko-sentinel",
    "version": "0.1.0",
    "environment": "development",
    "phase": 5,
    "components": {
      "config": "ready",
      "mcp_server_foundation": "ready",
      "deterministic_diagnosis": "ready",
      "controlled_autoscaling": "ready",
      "ai_reasoning": "ready",
      "http_transport": "ready"
    },
    "dependencies": {
      "kubernetes": { "status": "unreachable" },
      "autoscaler": { "provider": "simulated", "status": "ready" },
      "bedrock": { "model_id": "anthropic.claude-3-5-haiku-20241022-v1:0", "status": "mock", "mock_mode": true }
    }
  }
  ```

### B. MCP JSON-RPC Gateway: `POST /mcp`
Handles all standard MCP interactions (`initialize`, `ping`, `tools/list`, `tools/call`).
- **Headers:**
  - `Content-Type: application/json`
  - `Authorization: Bearer <SENTINEL_API_KEY>` (or `X-Sentinel-API-Key: <SENTINEL_API_KEY>`)
- **Sample Request (`tools/list`):**
  ```json
  {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list"
  }
  ```
- **Sample Request (`tools/call`):**
  ```json
  {
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
      "name": "diagnose_capacity",
      "arguments": { "pod_name": "agent-pending-cpu" }
    }
  }
  ```

---

## 5. Security & Isolation Controls

1. **Constant-Time Key Verification:** Authentication checks use `secrets.compare_digest` to prevent timing attacks.
2. **Fail-Safe Startup:** If `MCP_TRANSPORT=http` is set in production/development without `SENTINEL_API_KEY`, Sentinel aborts startup with `ConfigError` to prevent unauthenticated exposure.
3. **Zero Secret Leakage:** The HTTP transport redacts and masks all secrets. Error responses return standard JSON-RPC codes (`-32001 Unauthorized`, `-32700 Parse Error`, `-32600 Invalid Request`, `-32601 Method Not Found`, `-32602 Invalid Params`, `-32603 Internal Error`) without Python stack traces.
4. **Cloud Credential Isolation:** Kubernetes certificates, tokens, and AWS credentials remain 100% on the Sentinel backend and are never sent over HTTP to DronaHQ.
5. **Authoritative Policy Supremacy:** Scaling actions invoked over HTTP must satisfy all `RecoveryPolicyEngine` checks.

---

## 6. How to Run & Test Locally

### Running Sentinel with Streamable HTTP:
```bash
# In PowerShell:
$env:MCP_TRANSPORT="http"
$env:SENTINEL_API_KEY="my-secret-key-12345"
python src/main.py

# Or via explicit CLI flags:
python src/main.py --http
```

### Running Automated Compatibility Tests:
```bash
python scripts/test_mcp_http_compatibility.py
```

### Running Full Automated Test Suite:
```bash
python -m unittest discover -s tests -p "test_*.py" -v
```
*(All 109 unit and integration tests passing).*

