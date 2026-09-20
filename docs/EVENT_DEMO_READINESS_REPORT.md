# Nasiko Sentinel — Event Demo Readiness

## 1. Overall Status

**READY**

---

## 2. Tests

- **Total:** 109
- **Passed:** 109
- **Failed:** 0
- **Errors:** 0
- **Automated Protocol Checks:** 12/12 Passed (`scripts/audit_mcp_http_protocol.py`)
- **HTTP Compatibility Checks:** 5/5 Passed (`scripts/test_mcp_http_compatibility.py`)
- **Simulated Recovery Demo:** 10/10 Passed (`scripts/demo_phase3_verification.py`)

---

## 3. MCP Status

- **Protocol Version:** `2024-11-05` (Standard JSON-RPC 2.0)
- **Supported Transports:**
  - `stdio` (Standard I/O default CLI transport)
  - `Streamable HTTP` (Authenticated network transport via `POST /mcp`)
- **Tool Count:** 14 Registered Tools
- **HTTP Endpoints:**
  - `GET http://127.0.0.1:8000/health` (Health & Readiness probe)
  - `POST http://127.0.0.1:8000/mcp` (MCP JSON-RPC Gateway)

---

## 4. AI Reasoning

- **Bedrock Adapter:** `BedrockRuntimeReasoner` connecting to Amazon Bedrock Converse API via `boto3`.
- **Mock Reasoning:** `MockBedrockReasoner` for 100% offline local development and automated testing.
- **Deterministic Fallback:** `DeterministicFallbackReasoner` automatically active when Bedrock is unconfigured, times out, or fails.
- **Reasoning Source:** Explicitly returned in all proposals as:
  - `reasoning_source: "bedrock"` OR
  - `reasoning_source: "deterministic_fallback"`
- **Schema Validation:** `ProposalValidator` enforces strict action allowlist (`NO_ACTION`, `REQUEST_SCALE_UP`) and parameter limits before execution.

---

## 5. Recovery Flow

The canonical autonomous recovery sequence is fully implemented and verified:

```
CREATE/OBSERVE AGENT (get_agent_status)
        ↓
POD PENDING (get_pending_pods / get_pod_events)
        ↓
FailedScheduling (Insufficient CPU / Memory)
        ↓
DETERMINISTIC DIAGNOSIS (diagnose_capacity)
        ↓
AI REASONING (reason_recovery → RecoveryProposal)
        ↓
RECOVERY POLICY ENGINE (Authoritative Safety Bounds)
        ↓
CONTROLLED SCALE UP (request_scale_up)
        ↓
CAPACITY POLLING (wait_for_capacity)
        ↓
NEW CAPACITY READY (get_node_capacity)
        ↓
AUTONOMOUS RECOVERY VERIFICATION (verify_agent_recovery)
        ↓
AGENT STATUS: RUNNING (readyReplicas >= 1)
```

---

## 6. Safety & Authorization Controls

- **Maximum Nodes per Single Request:** 2 nodes
- **Maximum Cluster Node Ceiling:** 10 nodes
- **Cooldown Debounce Window:** 120 seconds per node pool
- **Scale Rate Limiting:** Maximum 3 operations per 15-minute window
- **Allowed Node Pools:** `default`, `general-compute`, `memory-optimized`
- **Policy Rejection Test:** Verified deterministic interception (`status: "POLICY_DENIED"`) on:
  - Request exceeding max nodes per request (`target_nodes=5` -> `MAX_NODES_PER_REQUEST_EXCEEDED`)
  - Request inside cooldown window -> `COOLDOWN_ACTIVE`
  - Request targeting disallowed pool -> `DISALLOWED_NODE_POOL`

---

## 7. DronaHQ Integration

- **Local MCP Endpoint:** `http://127.0.0.1:8000/mcp`
- **Authentication:** Constant-time `SENTINEL_API_KEY` verification via `Authorization: Bearer <key>` or `X-Sentinel-API-Key: <key>`
- **Remote Endpoint Requirement:** Requires a public HTTPS reverse tunnel URL (e.g. `https://<tunnel-domain>/mcp` via ngrok or Cloudflare Tunnel)
- **Connection Status:**
  > *DronaHQ live connection has not been verified unless an actual connection test was performed.*  
  (Local MCP Streamable HTTP transport and wire compatibility are 100% verified; SaaS connection requires operator-provisioned HTTPS tunnel).

---

## 8. Known Limitations

- **Live AWS Bedrock:** Real AWS Bedrock access is not verified unless AWS credentials and model enablement are provided in the environment (offline mock verified).
- **Live Kubernetes Cluster:** Real EKS, Karpenter, and Cluster Autoscaler execution is not verified unless connected to a live running cluster (simulated autoscaler provider verified).
- **DronaHQ Cloud SaaS:** DronaHQ live SaaS agent connection is not verified until a live tunnel URL is configured in DronaHQ.
- **Autoscaler Simulation:** Simulated autoscaling models real cloud delays and capacity injection but is not identical to physical cloud hypervisor provisioning.

---

## 9. Live Event Demo Script

### Step 1: Launch Sentinel HTTP Server (Terminal 1)
```powershell
$env:SENTINEL_API_KEY="event-demo-secret-key-2026"
$env:MCP_TRANSPORT="http"
python src/main.py --http
```
*Expected output:* `Started HttpMCPServer on http://127.0.0.1:8000 (Auth enabled: True)`

### Step 2: Verify Health & Tool Discovery (Terminal 2)
```bash
# Health Check:
curl -s http://127.0.0.1:8000/health

# MCP Tool Discovery (tools/list):
curl -s -X POST http://127.0.0.1:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer event-demo-secret-key-2026" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}'
```
*Expected result:* 14 registered tools returned with JSON schemas.

### Step 3: Run Full End-to-End Recovery Flow
```bash
python scripts/demo_phase3_verification.py
```
*Demonstrates:*
1. Observation of stalled agent `a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11` (`Pending`, `PodScheduled=False`).
2. Deterministic bottleneck diagnosis (`insufficient_cpu`).
3. Policy validation & scale request (+1 node in `default` pool).
4. Capacity provisioning transition (`REQUESTED` → `PROVISIONING` → `READY`).
5. Cluster capacity expansion (allocatable CPU: 3860m → 7860m).
6. Agent workload recovery confirmation (`readyReplicas: 1`, `status: Running`).
7. Complete audit trail in `get_recovery_status`.
8. Safety policy rejection demo (`POLICY_DENIED` on cooldown and node limits).

---

*Report prepared and submitted for event demo execution.*

