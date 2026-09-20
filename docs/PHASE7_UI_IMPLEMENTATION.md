# Phase 7 — Nasiko Sentinel Command Center UI & Agent Experience Implementation

## 1. Executive Summary

Phase 7 delivers a high-fidelity, autonomous infrastructure control plane experience for **Nasiko Sentinel**. The UI transforms raw Kubernetes and MCP diagnostic workflows into a visually compelling, evidentiary process graph designed for live stage presentations and architectural evaluations.

All core backend guarantees, security rules, and architectural invariants were strictly preserved with **109 / 109 automated tests passing**.

---

## 2. Key UI Components & Innovations

### A. Hero Header & Live Subsystem State
- **Real-Time Subsystem Indicators**: Accurately reflects live status for MCP transport (`READY`), Kubernetes Adapter (`SIMULATED ADAPTER` or `CONNECTED`), AI Reasoner (`DETERMINISTIC FALLBACK` or `BEDROCK LIVE`), and Autoscaler Provider (`SIMULATED`).
- **Live Presentation Mode**: Toggle for projector and stage screens that enlarges critical nodes and focuses on the recovery story.

### B. Evidentiary Process Pipeline (11 Nodes)
A horizontal, interactive evidentiary graph that visually proves the complete autonomous recovery lifecycle:
1. `AGENT REQUEST` (Nasiko requests workload instantiation)
2. `POD SCHEDULING` (Kubernetes default-scheduler triggered)
3. `PENDING DETECTED` (0/2 nodes available)
4. `KUBERNETES EVIDENCE` (Event: `FailedScheduling`, `2 Insufficient cpu`)
5. `ROOT CAUSE` (Deterministic diagnosis: `insufficient_cpu`)
6. `AI REASONING` (Synthesizes allocatable headroom into proposal)
7. `RECOVERY PROPOSAL` (Action: `REQUEST_SCALE_UP +1 node`)
8. `POLICY GATE` (Constraint audit: Max 2, Cooldown 120s &rarr; `ALLOWED`)
9. `SCALE ACTION` (Autoscaler triggered for `default` pool)
10. `CAPACITY READY` (Node provisioned and marked Ready)
11. `AGENT RUNNING` (Deployment reached `1/1 Ready`)

### C. Evidentiary Deep Inspector
Clicking any step in the pipeline updates the inspector with categorical badges:
- `[OBSERVED FACT]`
- `[DETERMINISTIC DIAGNOSIS]`
- `[AI INFERENCE]`
- `[POLICY DECISION]`
- `[EXECUTED ACTION]`

### D. Recovery Policy Gate & AI Checkpoint
- **Prominent Architectural Principle**: Displays the core motto: **"AI proposes. Policy decides."**
- **Safety Rule Grid**: Visualizes real limits (Max 2 nodes/request, 10 cluster max, 120s pool cooldown).
- **Interactive Policy Denial Demonstration**: A dedicated **"SIMULATE POLICY BLOCK"** action requests +5 nodes and visually proves that the authoritative Policy Engine blocks excessive scaling with `POLICY_DENIED (MAX_NODES_PER_REQUEST_EXCEEDED)`.

### E. Autonomous Agent Activity Stream
- Real-time stream logging timestamped decisions, scheduler observations, tool execution parameters, and structured JSON-RPC outputs.

---

## 3. Backend APIs Reused

| Endpoint / Method | Purpose | Transport |
| :--- | :--- | :--- |
| `GET /health` | Fetches live subsystem dependencies & reasoner status | HTTP |
| `POST /mcp` (`diagnose_capacity`) | Executes deterministic root-cause diagnosis | JSON-RPC 2.0 |
| `POST /mcp` (`reason_recovery`) | Invokes AI reasoner for structured proposal | JSON-RPC 2.0 |
| `POST /mcp` (`request_scale_up`) | Submits scaling request to Policy Engine | JSON-RPC 2.0 |
| `POST /mcp` (`verify_agent_recovery`) | Confirms deployment readiness | JSON-RPC 2.0 |

---

## 4. Test Verification Results

```
Ran 109 tests in 1.995s
OK
```

All unit, integration, and security tests across Phases 1 through 7 passed with zero regressions.

---

## 5. Live Access Endpoints

- **Local Command Center**: `http://localhost:8000`
- **Public Tunnel Preview**: `https://slick-mice-clean.loca.lt` (Tunnel password: `106.51.85.105`)
- **Health JSON Probe**: `http://localhost:8000/health`
- **Streamable HTTP MCP JSON-RPC**: `https://slick-mice-clean.loca.lt/mcp`

