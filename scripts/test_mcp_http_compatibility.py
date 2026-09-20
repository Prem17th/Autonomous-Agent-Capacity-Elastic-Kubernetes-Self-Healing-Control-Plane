"""Standalone MCP Streamable HTTP compatibility verification script."""

import copy
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, Tuple

# Add root directory to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.autoscaler.policy import RecoveryPolicyEngine
from src.autoscaler.recovery_tracker import recovery_tracker
from src.autoscaler.simulated_provider import SimulatedAutoscalerProvider
from src.bedrock.mock_reasoner import MockBedrockReasoner
from src.bedrock.orchestrator import SentinelRecoveryReasoner
from src.config.settings import Settings
from src.kubernetes.adapter import KubernetesAdapter
from src.kubernetes.client import MockKubernetesClient
from src.server.http_server import HttpMCPServer
from src.server.mcp_server import MCPServer
from tests.fixtures.k8s_fixtures import (
    DEPLOYMENT_PENDING,
    DEPLOYMENT_RUNNING,
    EVENTS_LIST,
    NODES_LIST,
    POD_PENDING_CPU,
    SAMPLE_NAMESPACE,
)


def run_http_request(url: str, payload: Dict[str, Any], api_key: str) -> Tuple[int, Dict[str, Any]]:
    """Execute JSON-RPC POST request over HTTP."""
    data = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        return e.code, json.loads(body) if body else {}


def main() -> int:
    print("=================================================================")
    print("Nasiko Sentinel - Phase 5 MCP Streamable HTTP Compatibility Test")
    print("=================================================================")

    api_key = "sentinel-local-verification-key"
    settings = Settings(
        environment="test",
        mcp_transport="http",
        mcp_http_host="127.0.0.1",
        mcp_http_port=0,
        sentinel_api_key=api_key,
        bedrock_mock_mode=True,
    )

    recovery_tracker.clear()
    mock_client = MockKubernetesClient(
        deployments=copy.deepcopy([DEPLOYMENT_RUNNING, DEPLOYMENT_PENDING]),
        pods=copy.deepcopy([POD_PENDING_CPU]),
        events=copy.deepcopy(EVENTS_LIST),
        nodes=copy.deepcopy(NODES_LIST),
        connected=True,
    )
    adapter = KubernetesAdapter(mock_client)
    provider = SimulatedAutoscalerProvider(adapter=adapter, provision_delay_seconds=0.01)
    policy_engine = RecoveryPolicyEngine()
    mock_reasoner = MockBedrockReasoner()
    orchestrator = SentinelRecoveryReasoner(primary_reasoner=mock_reasoner)

    mcp_server = MCPServer(
        settings=settings,
        adapter=adapter,
        autoscaler_provider=provider,
        policy_engine=policy_engine,
        reasoner=orchestrator,
    )

    http_server = HttpMCPServer(
        settings=settings,
        mcp_server=mcp_server,
        host="127.0.0.1",
        port=0,
        api_key=api_key,
    )
    http_server.start(threaded=True)
    host, port = http_server.server_address
    mcp_url = f"http://{host}:{port}/mcp"
    print(f"[*] Started local HttpMCPServer on {mcp_url}")

    try:
        # Step 1: initialize
        print("\n[Step 1] Testing MCP initialize...")
        init_req = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "dronahq-agent", "version": "1.0"},
            },
        }
        status, init_resp = run_http_request(mcp_url, init_req, api_key)
        assert status == 200, f"Expected status 200, got {status}"
        assert init_resp.get("result", {}).get("protocolVersion") == "2024-11-05"
        print("  -> MCP initialize succeeded: protocolVersion=2024-11-05")

        # Step 2: tools/list
        print("\n[Step 2] Testing MCP tools/list...")
        list_req = {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
        status, list_resp = run_http_request(mcp_url, list_req, api_key)
        assert status == 200, f"Expected status 200, got {status}"
        tools = list_resp.get("result", {}).get("tools", [])
        assert len(tools) == 14, f"Expected 14 tools, got {len(tools)}"
        print(f"  -> MCP tools/list succeeded: {len(tools)} tools discovered")

        # Step 3: tools/call (diagnose_capacity)
        print("\n[Step 3] Testing MCP tools/call -> diagnose_capacity...")
        diag_req = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "diagnose_capacity",
                "arguments": {"pod_name": "agent-pending-cpu", "namespace": SAMPLE_NAMESPACE},
            },
        }
        status, diag_resp = run_http_request(mcp_url, diag_req, api_key)
        assert status == 200, f"Expected status 200, got {status}"
        content = diag_resp.get("result", {}).get("content", [])
        assert len(content) > 0
        diag_data = json.loads(content[0]["text"])
        assert diag_data.get("classification") == "insufficient_cpu"
        print(f"  -> diagnose_capacity succeeded: classification={diag_data.get('classification')}")

        # Step 4: tools/call (reason_recovery)
        print("\n[Step 4] Testing MCP tools/call -> reason_recovery...")
        reason_req = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "reason_recovery",
                "arguments": {
                    "pod_name": "agent-pending-cpu",
                    "agent_id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
                    "namespace": SAMPLE_NAMESPACE,
                },
            },
        }
        status, reason_resp = run_http_request(mcp_url, reason_req, api_key)
        assert status == 200, f"Expected status 200, got {status}"
        reason_content = reason_resp.get("result", {}).get("content", [])
        reason_data = json.loads(reason_content[0]["text"])
        assert reason_data.get("action") == "REQUEST_SCALE_UP"
        print(f"  -> reason_recovery succeeded: action={reason_data.get('action')}, source={reason_data.get('reasoning_source')}")

        # Step 5: Test Auth Rejection
        print("\n[Step 5] Testing Unauthorized Access Rejection (No Token)...")
        status_unauth, unauth_resp = run_http_request(mcp_url, list_req, "wrong-key")
        assert status_unauth == 401, f"Expected status 401, got {status_unauth}"
        assert unauth_resp.get("error", {}).get("code") == -32001
        print("  -> Unauthenticated request cleanly rejected with HTTP 401")

        print("\n=================================================================")
        print("RESULT: ALL MCP STREAMABLE HTTP COMPATIBILITY CHECKS PASSED")
        print("=================================================================")
        return 0
    finally:
        http_server.stop()


if __name__ == "__main__":
    sys.exit(main())

