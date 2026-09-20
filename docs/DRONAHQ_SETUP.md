# DronaHQ AI Agent — Sentinel MCP Server Setup Guide

This guide describes how to configure a **DronaHQ AI Agent** to communicate with the **Nasiko Sentinel MCP Server** using DronaHQ's native External MCP Server tool integration.

*Source Documentation:*  
Official DronaHQ Agent Tools Guide: [https://docs.dronahq.com/agents/getting-started/tools-overview/](https://docs.dronahq.com/agents/getting-started/tools-overview/)

---

## 1. Overview of DronaHQ MCP Integration

DronaHQ supports integrating custom and third-party tools into AI Agents through the **Model Context Protocol (MCP)**. When configuring an external MCP server in DronaHQ:

- **Supported Transports in DronaHQ:**
  - **Streamable HTTP** *(Implemented in Nasiko Sentinel Phase 5)*
  - **Server-Sent Events (SSE)** *(Alternative DronaHQ transport)*
- **Supported Authentication Modes in DronaHQ:**
  - No Authentication
  - Access Tokens / Bearer Token
  - Custom Headers (e.g. `X-Sentinel-API-Key`)

---

## 2. Step-by-Step DronaHQ Agent Configuration

### Step 1: Open DronaHQ AI Agent Builder
1. Log in to your DronaHQ workspace.
2. Navigate to **AI Agents** > Select your Target Agent (or Create a new Agent).
3. In the Agent configuration panel, click on **Tools** > **Add Tool** > **Model Context Protocol (MCP)**.

### Step 2: Configure Server Endpoint
In the MCP configuration modal:
- **Server Name:** `Nasiko-Sentinel`
- **Transport Type:** Select `Streamable HTTP`
- **Server URL:**  
  - For local development with secure tunnel: `https://<your-tunnel-domain>.ngrok-free.app/mcp`
  - For internal Kubernetes/VPC deployment: `http://sentinel-service.nasiko-system.svc.cluster.local:8000/mcp`

### Step 3: Configure Authentication
Select one of the following authentication methods supported by DronaHQ:

#### Option A: Access Token (Bearer Auth)
- **Authentication Type:** `Bearer Token` / `Access Token`
- **Token Value:** `{{SENTINEL_API_KEY}}` *(Referenced securely from DronaHQ Secrets Vault)*

#### Option B: Custom Header
- **Authentication Type:** `Custom Header`
- **Header Name:** `X-Sentinel-API-Key`
- **Header Value:** `{{SENTINEL_API_KEY}}`

### Step 4: Discover Tools & Save
1. Click **Fetch Tools** / **Discover Tools**.
2. DronaHQ executes the `tools/list` JSON-RPC method over HTTP.
3. The following 14 tools will automatically be populated with their JSON schemas:
   - `get_health`
   - `get_agent_status`
   - `get_pending_pods`
   - `get_pod_events`
   - `get_node_capacity`
   - `diagnose_capacity`
   - `request_scale_up`
   - `wait_for_capacity`
   - `get_autoscaler_status`
   - `get_node_pool_status`
   - `get_recovery_status`
   - `verify_agent_recovery`
   - `retry_agent`
   - `reason_recovery`
4. Enable the tools you wish the DronaHQ Agent to invoke and click **Save**.

---

## 3. Security Guidelines for DronaHQ Operators

1. **Vault Storage:** Always store `SENTINEL_API_KEY` in DronaHQ's Environment Secrets Vault rather than plain text.
2. **Authoritative Safety:** The Sentinel backend strictly enforces cluster safety limits on every tool call (`request_scale_up`), regardless of client permissions or prompt instructions.
3. **No Direct Cloud Credentials:** DronaHQ does not require, nor should it be granted, AWS IAM keys or Kubernetes kubeconfigs. All infrastructure access is securely mediated by Sentinel's authenticated MCP gateway.

