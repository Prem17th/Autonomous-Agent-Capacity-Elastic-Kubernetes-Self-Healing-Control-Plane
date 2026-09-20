"""
Phase 3 MCP Interface End-to-End Verification Script for Nasiko Sentinel.

Demonstrates:
1. Agent in Pending state with PodScheduled=False & FailedScheduling events.
2. diagnose_capacity deterministic classification.
3. Policy validation & request_scale_up via MCP JSON-RPC.
4. Simulated autoscaler lifecycle transition (REQUESTED -> PROVISIONING -> READY).
5. Simulated capacity availability in cluster adapter.
6. verify_agent_recovery confirming readyReplicas >= 1 and Running status.
7. get_recovery_status showing complete audit trail.
8. Safety policy violation demonstration (Cooldown debounce rejection & Max nodes rejection).
"""

import copy
import json
from pathlib import Path
import sys
import time
from typing import Any, Dict

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.autoscaler.policy import RecoveryPolicyEngine
from src.autoscaler.recovery_tracker import recovery_tracker
from src.autoscaler.simulated_provider import SimulatedAutoscalerProvider
from src.config.settings import Settings
from src.kubernetes.adapter import KubernetesAdapter
from src.kubernetes.client import MockKubernetesClient
from src.server.mcp_server import MCPServer
from tests.fixtures.k8s_fixtures import (
    DEPLOYMENT_PENDING,
    DEPLOYMENT_RUNNING,
    EVENTS_LIST,
    NODES_LIST,
    POD_PENDING_CPU,
    POD_RUNNING,
    SAMPLE_NAMESPACE,
)


def run_mcp_call(server: MCPServer, req_id: int, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a tool/call request through the JSON-RPC interface."""
    rpc_req = {
        "jsonrpc": "2.0",
        "id": req_id,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments,
        },
    }
    print(f"\n=======================================================")
    print(f"--> [JSON-RPC Request #{req_id}] Tool: {tool_name}")
    print(f"--> Payload: {json.dumps(arguments, indent=2)}")
    
    resp = server.handle_request(rpc_req)
    if not resp:
        print("--> [No response returned]")
        return {}

    if "error" in resp:
        print(f"<-- [JSON-RPC Error]: {json.dumps(resp['error'], indent=2)}")
        return resp

    text_result = resp["result"]["content"][0]["text"]
    parsed_result = json.loads(text_result)
    print(f"<-- [JSON-RPC Result]:\n{json.dumps(parsed_result, indent=2)}")
    return parsed_result


def main() -> None:
    print("================================================================================")
    print("NASIKO SENTINEL - PHASE 3 MCP VERIFICATION RUNNER")
    print("================================================================================")

    recovery_tracker.clear()
    settings = Settings(environment="development")
    
    # 1. Setup mock cluster with Pending agent
    mock_client = MockKubernetesClient(
        deployments=copy.deepcopy([DEPLOYMENT_RUNNING, DEPLOYMENT_PENDING]),
        pods=copy.deepcopy([POD_RUNNING, POD_PENDING_CPU]),
        events=copy.deepcopy(EVENTS_LIST),
        nodes=copy.deepcopy(NODES_LIST),
        connected=True,
    )
    adapter = KubernetesAdapter(mock_client)
    provider = SimulatedAutoscalerProvider(adapter=adapter, provision_delay_seconds=0.3)
    policy_engine = RecoveryPolicyEngine(cooldown_seconds=120, max_nodes_per_request=2)

    server = MCPServer(
        settings=settings,
        adapter=adapter,
        autoscaler_provider=provider,
        policy_engine=policy_engine,
    )

    agent_id = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"
    pod_name = "agent-pending-cpu"

    print("\n--- STEP 1 & 2: Observe Pending Agent & FailedScheduling Evidence ---")
    run_mcp_call(server, 1, "get_agent_status", {"agent_id": agent_id, "namespace": SAMPLE_NAMESPACE})
    run_mcp_call(server, 2, "get_pending_pods", {"namespace": SAMPLE_NAMESPACE})
    run_mcp_call(server, 3, "get_pod_events", {"pod_name": pod_name, "namespace": SAMPLE_NAMESPACE})

    print("\n--- STEP 3: Deterministic Bottleneck Diagnosis ---")
    diag_res = run_mcp_call(server, 4, "diagnose_capacity", {"pod_name": pod_name, "namespace": SAMPLE_NAMESPACE})
    assert diag_res["classification"] == "insufficient_cpu", "Expected insufficient_cpu diagnosis"

    print("\n--- STEP 4 & 5: Policy Validation & Request Scale-Up ---")
    scale_res = run_mcp_call(
        server,
        5,
        "request_scale_up",
        {
            "node_pool": "default",
            "target_nodes": 1,
            "reason": diag_res["classification"],
            "agent_id": agent_id,
        },
    )
    assert scale_res["status"] == "ACCEPTED", "Scale request should be accepted"
    op_id = scale_res["scale_request_id"]

    print("\n--- STEP 6 & 7: Asynchronous Polling & Simulated Capacity Provisioning ---")
    print(f"Polling wait_for_capacity for operation {op_id}...")
    wait_res = run_mcp_call(
        server,
        6,
        "wait_for_capacity",
        {
            "scale_request_id": op_id,
            "timeout_seconds": 10,
            "poll_interval_seconds": 0.05,
            "agent_id": agent_id,
        },
    )
    assert wait_res["status"] == "READY", "Capacity should reach READY state"
    
    # Inspect node capacity tool to confirm new simulated node is visible
    run_mcp_call(server, 7, "get_node_capacity", {})

    print("\n--- STEP 8: Simulate Pod Scheduling on New Node & Verify Agent Recovery ---")
    # Simulate Kubernetes default-scheduler placing the pending workload
    dep_dict = mock_client.deployments.get(agent_id)
    if dep_dict:
        dep_dict["status"]["readyReplicas"] = 1
        dep_dict["status"]["availableReplicas"] = 1
        dep_dict["status"]["conditions"] = [{"type": "Available", "status": "True"}]

    verify_res = run_mcp_call(server, 8, "verify_agent_recovery", {"agent_id": agent_id, "namespace": SAMPLE_NAMESPACE})
    assert verify_res["recovered"] is True, "Agent should be verified recovered"
    assert verify_res["status"] == "Running", "Agent status should be Running"

    print("\n--- STEP 9: Audit Trail / Recovery State Machine Inspection ---")
    rec_res = run_mcp_call(server, 9, "get_recovery_status", {"agent_id": agent_id})
    assert rec_res["found"] is True
    assert rec_res["recovery"]["current_state"] == "RUNNING"
    print(f"\n[Audit Trail States Recorded]: {[h['state'] for h in rec_res['recovery']['history']]}")

    print("\n--- STEP 10: Demonstrate Safety Policy Violations ---")
    print("\n[Safety Check A]: Cooldown Debounce Window Violation (120s cooldown)")
    cooldown_violation = run_mcp_call(
        server,
        10,
        "request_scale_up",
        {"node_pool": "default", "target_nodes": 1},
    )
    assert cooldown_violation["status"] == "POLICY_DENIED"
    assert cooldown_violation["reason"] == "COOLDOWN_ACTIVE"

    print("\n[Safety Check B]: Max Nodes Per Request Exceeded (> 2 nodes)")
    max_nodes_violation = run_mcp_call(
        server,
        11,
        "request_scale_up",
        {"node_pool": "general-compute", "target_nodes": 5},
    )
    assert max_nodes_violation["status"] == "POLICY_DENIED"
    assert max_nodes_violation["reason"] == "MAX_NODES_PER_REQUEST_EXCEEDED"

    print("\n[Safety Check C]: Disallowed Node Pool")
    disallowed_pool_violation = run_mcp_call(
        server,
        12,
        "request_scale_up",
        {"node_pool": "forbidden-untrusted-pool", "target_nodes": 1},
    )
    assert disallowed_pool_violation["status"] == "POLICY_DENIED"
    assert disallowed_pool_violation["reason"] == "DISALLOWED_NODE_POOL"

    print("\n================================================================================")
    print("ALL 10 VERIFICATION OBJECTIVES SUCCESSFULLY DEMONSTRATED OVER JSON-RPC INTERFACE!")
    print("================================================================================")


if __name__ == "__main__":
    main()

