# MCP Streamable HTTP Compatibility Audit

## Executive Summary
This document provides a protocol-level wire-compatibility audit of the **Nasiko Sentinel Streamable HTTP Transport Adapter** (`src/server/http_server.py` and `MCPServer.handle_request()`).

It benchmarks the server's wire behavior against:
1. The **Model Context Protocol (MCP) Specification** (`https://modelcontextprotocol.io/`).
2. The **DronaHQ Agent Tools Overview & External MCP Connector Documentation** (`https://docs.dronahq.com/agents/getting-started/tools-overview/`).

---

## 1. Implemented Protocol Version
- **Implemented Version:** `2024-11-05` (the foundation Model Context Protocol specification).
- **Capability Negotiation (`initialize`):**
  - Accepts `protocolVersion: "2024-11-05"`, `capabilities`, `clientInfo`.
  - Responds with `protocolVersion: "2024-11-05"`, `capabilities: { "tools": { "listChanged": false } }`, and `serverInfo: { "name": "nasiko-sentinel", "version": "0.1.0" }`.
- **Notifications:**
  - Handles `notifications/initialized` and returns `HTTP 204 No Content`.

---

## 2. Transport Mode
- **Transport Mode:** **B. Stateless Streamable HTTP (JSON-only / Single-Endpoint POST)**.
- **Characteristics:**
  - Single endpoint: `POST /mcp`.
  - Every MCP message (initialization, tool discovery, tool invocation) is sent as an independent JSON-RPC 2.0 `POST` request.
  - Server returns `Content-Type: application/json; charset=utf-8` with JSON-RPC response payloads.
  - No server-side session state or memory leaks across requests.

---

## 3. HTTP Endpoint Behavior

| HTTP Method | Path | Purpose | Behavior & Status Codes |
| :--- | :--- | :--- | :--- |
| `GET` | `/health` | Service Liveness / Readiness | Returns `HTTP 200 OK` with JSON health payload. |
| `POST` | `/mcp` | MCP JSON-RPC Gateway | Authenticates, parses JSON-RPC request, dispatches to `handle_request()`, returns `HTTP 200 OK` (or `HTTP 204 No Content` for notifications). |
| `POST` | `/` | Alias for `/mcp` | Supported as root endpoint fallback. |
| Other | `/*` | Unmapped Endpoints | Returns `HTTP 404 Not Found` with JSON-RPC error `-32601`. |

---

## 4. Headers

### Request Headers Handled:
- **`Content-Type`:** `application/json` (Required for POST body parsing).
- **`Content-Length`:** Enforces maximum limit of 10 MB. Invalid headers rejected with `HTTP 400 Bad Request`.
- **`Accept`:** Tolerant. Supports `application/json`, `text/event-stream`, `*/*`, or unspecified.
- **Authentication Headers:**
  - `Authorization: Bearer <SENTINEL_API_KEY>`
  - `X-Sentinel-API-Key: <SENTINEL_API_KEY>`
  - `X-API-Key: <SENTINEL_API_KEY>`

### Response Headers Returned:
- `Content-Type: application/json; charset=utf-8`
- `Content-Length: <len>`
- `Cache-Control: no-cache`

---

## 5. Session Behavior
- **Design:** Fully **stateless**.
- **`Mcp-Session-Id`:** Not required or utilized. In accordance with modern MCP evolution, request routing is stateless per `POST` message, simplifying scaling and preventing dangling session state.

---

## 6. JSON-RPC Behavior

The server strictly adheres to JSON-RPC 2.0 framing:

| Scenario | JSON-RPC Code | HTTP Status | Response Structure |
| :--- | :--- | :--- | :--- |
| **Success (`tools/list`, `tools/call`, `initialize`)** | `None` (Result) | `HTTP 200` | `{"jsonrpc": "2.0", "id": <id>, "result": {...}}` |
| **Notification (`notifications/initialized`)** | `None` | `HTTP 204` | `(Empty body)` |
| **Unauthorized (Missing/Invalid Key)** | `-32001` | `HTTP 401` | `{"jsonrpc": "2.0", "id": null, "error": {"code": -32001, "message": "Unauthorized..."}}` |
| **Malformed JSON** | `-32700` | `HTTP 200` | `{"jsonrpc": "2.0", "id": null, "error": {"code": -32700, "message": "Parse error..."}}` |
| **Missing/Invalid Method** | `-32600` | `HTTP 200` | `{"jsonrpc": "2.0", "id": <id>, "error": {"code": -32600, "message": "Missing or invalid 'method'..."}}` |
| **Unknown Method** | `-32601` | `HTTP 200` | `{"jsonrpc": "2.0", "id": <id>, "error": {"code": -32601, "message": "Method not found..."}}` |
| **Unknown Tool / Invalid Arguments** | `-32602` | `HTTP 200` | `{"jsonrpc": "2.0", "id": <id>, "error": {"code": -32602, "message": "..."}}` |
| **Internal / Execution Error** | `-32603` | `HTTP 200` | `{"jsonrpc": "2.0", "id": <id>, "error": {"code": -32603, "message": "..."}}` |

---

## 7. Authentication
- **Mechanism:** `SENTINEL_API_KEY` configuration via environment/settings.
- **Verification:** Constant-time comparison using `secrets.compare_digest`.
- **Fail-Safe Startup:** Server refuses to start without `SENTINEL_API_KEY` outside of test mode.
- **Secret Redaction:** `SENTINEL_API_KEY` is redacted in logs and error responses.

---

## 8. DronaHQ Compatibility

Comparing against DronaHQ documentation (`https://docs.dronahq.com/agents/getting-started/tools-overview/`):
- **Transport Compatibility:** DronaHQ natively supports **Streamable HTTP** for External MCP Servers. Sentinel exposes `POST /mcp` for all MCP interactions.
- **Authentication Compatibility:** DronaHQ supports **Bearer Tokens** and **Custom Headers** (e.g. `X-Sentinel-API-Key`). Both are verified and supported by Sentinel.
- **Discovery Compatibility:** DronaHQ discovers tools by calling `tools/list` over the configured MCP endpoint. All 14 tools return compliant JSON Schema schemas.
- **Execution Compatibility:** Tool calls are formatted in standard `tools/call` payloads returning text content blocks (`[{"type": "text", "text": "..."}]`).

---

## 9. Missing Requirements & Known Limitations
1. **SSE (Server-Sent Events) Streaming:** `text/event-stream` response streaming is not currently implemented. Responses are returned as discrete `application/json` HTTP responses. (DronaHQ supports Streamable HTTP without requiring SSE).
2. **Session Persistence:** Stateful session headers (`Mcp-Session-Id`) are not used; all requests are stateless.
3. **Live Cloud Ingress:** Connecting a live DronaHQ Cloud SaaS agent to a local development machine requires a public HTTPS tunnel (e.g. ngrok / Cloudflare Tunnel).

---

## 10. Required Changes
**None.** The current implementation provides clean, compliant Stateless Streamable HTTP transport without requiring changes to domain logic, Bedrock reasoning, autoscaling, or Kubernetes observation.

---

## 11. Test Results

### 1. Protocol Wire Audit (`scripts/audit_mcp_http_protocol.py`):
```
-----------------------------------------------------------------
Audit Check                                   | Result | Details
-----------------------------------------------------------------
GET /health liveness probe                    | PASS   | HTTP 200
POST /mcp initialize (2024-11-05)             | PASS   | HTTP 200, proto=2024-11-05
POST /mcp notifications/initialized           | PASS   | HTTP 204 (204 No Content)
POST /mcp tools/list schema discovery         | PASS   | HTTP 200, 14 tools
POST /mcp tools/call execution                | PASS   | HTTP 200, content blocks returned
Accept header tolerance (application/json, */*) | PASS   | HTTP 200, Content-Type=application/json; charset=utf-8
Custom header auth (X-Sentinel-API-Key)       | PASS   | HTTP 200
Unauthenticated access rejection              | PASS   | HTTP 401, Code=-32001
Unknown JSON-RPC method (-32601)              | PASS   | HTTP 200, Code=-32601
Unknown tool name in tools/call (-32602)      | PASS   | HTTP 200, Code=-32602
Malformed JSON payload parse error (-32700)   | PASS   | HTTP 200, Code=-32700
Invalid Content-Length rejection              | PASS   | HTTP 400
-----------------------------------------------------------------
AUDIT SUMMARY: ALL PROTOCOL CHECKS PASSED.
```

### 2. Standalone HTTP Compatibility Test (`scripts/test_mcp_http_compatibility.py`):
```
RESULT: ALL MCP STREAMABLE HTTP COMPATIBILITY CHECKS PASSED
```

### 3. Full Unit & Integration Test Suite (`python -m unittest discover -s tests -p "test_*.py" -v`):
```
Ran 109 tests in 1.986s
OK
```

---

## 12. Final Classification

**PASS WITH LIMITATIONS — DRONAHQ CONNECTION TEST REQUIRED**

*Rationale:*  
All protocol wire checks, authentication mechanisms, schema discovery, and tool execution routines over Streamable HTTP pass 100% in local automated audits. The "limitations" denote that SSE streaming is not implemented (JSON-only Streamable HTTP) and that actual end-to-end integration with DronaHQ Cloud SaaS will require a live tunnel/network endpoint and live DronaHQ agent configuration in Phase 5.2/6.

