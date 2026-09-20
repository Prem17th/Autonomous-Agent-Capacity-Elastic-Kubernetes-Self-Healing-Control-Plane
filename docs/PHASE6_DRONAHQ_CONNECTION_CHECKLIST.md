# Phase 6A: DronaHQ Connection Preparation Checklist

## 1. Executive Summary
This document provides the operational runbook and verification checklist required to connect a **DronaHQ AI Agent** to the **Nasiko Sentinel Model Context Protocol (MCP) Server** over Streamable HTTP.

---

## 2. Server Configuration & Startup

### Required Environment Variables
Set the following environment variables on the Sentinel host before launching:

```ini
# Core Configuration
ENVIRONMENT=development
LOG_LEVEL=INFO

# HTTP Network Transport
MCP_TRANSPORT=http
MCP_HTTP_HOST=127.0.0.1
MCP_HTTP_PORT=8000

# Authentication (Must be set to a secure random string)
SENTINEL_API_KEY=<SET_YOUR_SECRET_API_KEY_HERE>

# Bedrock Simulation (Default for local development)
BEDROCK_MOCK_MODE=true
```

### Sentinel Startup Command
Launch the MCP server in Streamable HTTP transport mode:

#### On Windows (PowerShell):
```powershell
$env:SENTINEL_API_KEY="<SET_YOUR_SECRET_API_KEY_HERE>"
$env:MCP_TRANSPORT="http"
python src/main.py --http
```

#### On Linux / macOS (Bash):
```bash
SENTINEL_API_KEY="<SET_YOUR_SECRET_API_KEY_HERE>" MCP_TRANSPORT="http" python src/main.py --http
```

---

## 3. Local & Remote URLs

| Endpoint | Local URL | Public / Tunnel URL (Example) | Purpose |
| :--- | :--- | :--- | :--- |
| **Health Probe** | `http://127.0.0.1:8000/health` | `https://<tunnel-domain>/health` | Verify server liveness & component readiness |
| **MCP Gateway** | `http://127.0.0.1:8000/mcp` | `https://<tunnel-domain>/mcp` | Main JSON-RPC 2.0 endpoint for DronaHQ |

---

## 4. Authentication Headers Expected by Sentinel

Sentinel accepts any of the following standard authentication headers:
1. `Authorization: Bearer <SENTINEL_API_KEY>`
2. `X-Sentinel-API-Key: <SENTINEL_API_KEY>`
3. `X-API-Key: <SENTINEL_API_KEY>`

---

## 5. DronaHQ-Side Configuration Fields

Verified against official DronaHQ documentation (`https://docs.dronahq.com/agents/getting-started/tools-overview/`):

| DronaHQ Field | Required Value | Notes |
| :--- | :--- | :--- |
| **Tool Type** | `Model Context Protocol (MCP)` | Add via Agent Builder > Tools |
| **Server Name** | `Nasiko-Sentinel` | Logical identifier in DronaHQ |
| **Transport Type** | `Streamable HTTP` | Native MCP network transport |
| **Server URL** | `https://<your-public-tunnel-domain>/mcp` | Must be an externally reachable HTTPS URL |
| **Authentication** | `Bearer Token` or `Custom Header` | Select preferred auth mode |
| **Token / Header Value** | `{{SENTINEL_API_KEY}}` | Stored securely in DronaHQ Environment Secrets |

---

## 6. Network & Tunnel Requirements

Because DronaHQ Cloud SaaS (`app.dronahq.com`) runs in the cloud, it cannot connect directly to `http://127.0.0.1:8000`.

### Tunnel Prerequisite (For Local Development / Demos):
- A secure TLS reverse tunnel must be active (e.g. `ngrok http 8000` or `cloudflared tunnel --url http://127.0.0.1:8000`).
- The resulting HTTPS forwarding URL (e.g. `https://abc-123.ngrok-free.app/mcp`) must be entered as the **Server URL** in DronaHQ.
- Local endpoint `http://127.0.0.1:8000` continues serving the requests via the tunnel.

---

## 7. Security Checklist

- [ ] `SENTINEL_API_KEY` is a strong random secret and NOT stored in Git.
- [ ] `SENTINEL_API_KEY` is referenced via DronaHQ's Environment Secrets Vault, not hardcoded into prompts or UI fields.
- [ ] No Kubernetes certificates, tokens, or AWS credentials are provided to DronaHQ.
- [ ] Constant-time comparison verifies incoming requests on Sentinel.
- [ ] Error responses return structured JSON-RPC errors with zero Python stack traces.
- [ ] Recovery Policy Engine strictly authorizes all scale requests.

---

## 8. Staged Tool Testing Protocol

To ensure safe, controlled verification during the first live DronaHQ connection, execute tool tests in strictly separated tiers:

### Tier 1: Read-Only Tools (TEST FIRST)
Verify DronaHQ can discover and invoke these non-mutating inspection tools:
1. `get_health`: Service health check.
2. `get_agent_status`: Inspect Nasiko deployment status (`agent_id`).
3. `get_pending_pods`: Query unscheduled pods and normalized requests.
4. `get_pod_events`: Inspect pod scheduler events.
5. `get_node_capacity`: Query allocatable compute headroom.
6. `diagnose_capacity`: Classify pod bottleneck deterministically (`insufficient_cpu`).
7. `get_autoscaler_status`: Check autoscaler provider mode.
8. `get_node_pool_status`: Query node pool bounds and instance counts.
9. `get_recovery_status`: Query audit history.

> [!IMPORTANT]
> **Tier 1 Gate:** Do NOT proceed to Tier 2 until Tier 1 read-only tools successfully execute from the DronaHQ agent interface.

### Tier 2: AI Reasoning & Recovery Tools (TEST ONLY AFTER TIER 1 SUCCEEDS)
1. `reason_recovery`: Generates structured scaling proposals via Bedrock / Mock reasoner.
2. `request_scale_up`: Evaluates policy and dispatches scale request.
3. `wait_for_capacity`: Polls until newly provisioned capacity reaches Ready.
4. `verify_agent_recovery`: Verifies agent reached Running status.
5. `retry_agent`: (Auxiliary only) Manual deployment reconciliation.

---

## 9. Verification Status

Prior to issuing this checklist, all automated verification steps completed successfully:
- **Wire Audit (`scripts/audit_mcp_http_protocol.py`):** 12/12 checks PASSED.
- **Compatibility Test (`scripts/test_mcp_http_compatibility.py`):** ALL CHECKS PASSED.
- **Full Unit & Integration Suite (`python -m unittest discover -s tests -p "test_*.py" -v`):** 109/109 tests PASSED (0 failures, 0 errors).

