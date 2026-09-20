"""Protocol-level wire-compatibility audit script for MCP Streamable HTTP transport."""

import copy
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

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


def send_http_raw(
    url: str,
    payload: Optional[Dict[str, Any]] = None,
    raw_body: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None,
    method: str = "POST",
) -> Tuple[int, Dict[str, str], Any]:
    """Execute low-level HTTP request returning status, response headers, and parsed body."""
    req_headers = {}
    if headers:
        req_headers.update(headers)

    body_bytes = None
    if raw_body is not None:
        body_bytes = raw_body.encode("utf-8")
    elif payload is not None:
        body_bytes = json.dumps(payload).encode("utf-8")
        if "Content-Type" not in req_headers:
            req_headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=body_bytes, headers=req_headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            resp_headers = dict(resp.headers)
            body_str = resp.read().decode("utf-8")
            try:
                parsed = json.loads(body_str) if body_str else None
            except Exception:
                parsed = body_str
            return resp.status, resp_headers, parsed
    except urllib.error.HTTPError as e:
        resp_headers = dict(e.headers)
        err_str = e.read().decode("utf-8")
        try:
            parsed = json.loads(err_str) if err_str else None
        except Exception:
            parsed = err_str
        return e.code, resp_headers, parsed


def main() -> int:
    print("=================================================================")
    print("Nasiko Sentinel — Phase 5.1 Protocol Wire-Compatibility Audit")
    print("=================================================================")

    api_key = "sentinel-audit-api-key-999"
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
    health_url = f"http://{host}:{port}/health"

    print(f"[*] Server listening on {mcp_url}\n")
    audit_results = []

    try:
        # Audit 1: GET /health
        status, hdrs, body = send_http_raw(health_url, method="GET")
        check1 = (status == 200 and body.get("status") == "ok")
        audit_results.append(("GET /health liveness probe", check1, f"HTTP {status}"))

        # Audit 2: POST /mcp initialize
        init_payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "audit-client", "version": "1.0"},
            },
        }
        status, hdrs, body = send_http_raw(
            mcp_url,
            payload=init_payload,
            headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json"},
        )
        check2 = (
            status == 200
            and body.get("result", {}).get("protocolVersion") == "2024-11-05"
            and "serverInfo" in body.get("result", {})
            and "application/json" in hdrs.get("Content-Type", "")
        )
        audit_results.append(("POST /mcp initialize (2024-11-05)", check2, f"HTTP {status}, proto={body.get('result', {}).get('protocolVersion')}"))

        # Audit 3: notifications/initialized
        notif_payload = {"jsonrpc": "2.0", "method": "notifications/initialized"}
        status, hdrs, body = send_http_raw(
            mcp_url,
            payload=notif_payload,
            headers={"Authorization": f"Bearer {api_key}"},
        )
        check3 = (status == 204)
        audit_results.append(("POST /mcp notifications/initialized", check3, f"HTTP {status} (204 No Content)"))

        # Audit 4: POST /mcp tools/list
        list_payload = {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
        status, hdrs, body = send_http_raw(
            mcp_url,
            payload=list_payload,
            headers={"Authorization": f"Bearer {api_key}"},
        )
        tools = body.get("result", {}).get("tools", [])
        check4 = (status == 200 and len(tools) == 14)
        audit_results.append(("POST /mcp tools/list schema discovery", check4, f"HTTP {status}, {len(tools)} tools"))

        # Audit 5: POST /mcp tools/call (diagnose_capacity)
        call_payload = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "diagnose_capacity",
                "arguments": {"pod_name": "agent-pending-cpu", "namespace": SAMPLE_NAMESPACE},
            },
        }
        status, hdrs, body = send_http_raw(
            mcp_url,
            payload=call_payload,
            headers={"X-Sentinel-API-Key": api_key},
        )
        check5 = (status == 200 and len(body.get("result", {}).get("content", [])) > 0)
        audit_results.append(("POST /mcp tools/call execution", check5, f"HTTP {status}, content blocks returned"))

        # Audit 6: Accept header handling (application/json, */*, text/event-stream)
        status, hdrs, body = send_http_raw(
            mcp_url,
            payload=list_payload,
            headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json, text/event-stream, */*"},
        )
        check6 = (status == 200 and "application/json" in hdrs.get("Content-Type", ""))
        audit_results.append(("Accept header tolerance (application/json, */*)", check6, f"HTTP {status}, Content-Type={hdrs.get('Content-Type')}"))

        # Audit 7: Authentication with custom header (X-Sentinel-API-Key)
        status, hdrs, body = send_http_raw(
            mcp_url,
            payload={"jsonrpc": "2.0", "id": 4, "method": "ping"},
            headers={"X-Sentinel-API-Key": api_key},
        )
        check7 = (status == 200 and body.get("id") == 4)
        audit_results.append(("Custom header auth (X-Sentinel-API-Key)", check7, f"HTTP {status}"))

        # Audit 8: Unauthenticated access rejection
        status, hdrs, body = send_http_raw(mcp_url, payload=list_payload, headers={})
        check8 = (status == 401 and body.get("error", {}).get("code") == -32001)
        audit_results.append(("Unauthenticated access rejection", check8, f"HTTP {status}, Code={body.get('error', {}).get('code')}"))

        # Audit 9: Unknown JSON-RPC method handling
        status, hdrs, body = send_http_raw(
            mcp_url,
            payload={"jsonrpc": "2.0", "id": 5, "method": "custom/invalid_method"},
            headers={"Authorization": f"Bearer {api_key}"},
        )
        check9 = (status == 200 and body.get("error", {}).get("code") == -32601)
        audit_results.append(("Unknown JSON-RPC method (-32601)", check9, f"HTTP {status}, Code={body.get('error', {}).get('code')}"))

        # Audit 10: Unknown Tool Name handling
        status, hdrs, body = send_http_raw(
            mcp_url,
            payload={"jsonrpc": "2.0", "id": 6, "method": "tools/call", "params": {"name": "unknown_tool", "arguments": {}}},
            headers={"Authorization": f"Bearer {api_key}"},
        )
        check10 = (status == 200 and body.get("error", {}).get("code") == -32602)
        audit_results.append(("Unknown tool name in tools/call (-32602)", check10, f"HTTP {status}, Code={body.get('error', {}).get('code')}"))

        # Audit 11: Malformed JSON payload handling
        status, hdrs, body = send_http_raw(
            mcp_url,
            raw_body="{broken json content",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        )
        check11 = (status == 200 and body.get("error", {}).get("code") == -32700)
        audit_results.append(("Malformed JSON payload parse error (-32700)", check11, f"HTTP {status}, Code={body.get('error', {}).get('code')}"))

        # Audit 12: Content-Length validation
        status, hdrs, body = send_http_raw(
            mcp_url,
            raw_body="{}",
            headers={"Authorization": f"Bearer {api_key}", "Content-Length": "invalid"},
        )
        check12 = (status == 400 and body.get("error", {}).get("code") == -32600)
        audit_results.append(("Invalid Content-Length rejection", check12, f"HTTP {status}"))

        # Print summary table
        print("-" * 65)
        print(f"{'Audit Check':<45} | {'Result':<6} | {'Details'}")
        print("-" * 65)
        all_passed = True
        for name, passed, detail in audit_results:
            result_str = "PASS" if passed else "FAIL"
            if not passed:
                all_passed = False
            print(f"{name:<45} | {result_str:<6} | {detail}")
        print("-" * 65)

        if all_passed:
            print("\nAUDIT SUMMARY: ALL PROTOCOL CHECKS PASSED.")
            return 0
        else:
            print("\nAUDIT SUMMARY: ONE OR MORE CHECKS FAILED.")
            return 1
    finally:
        http_server.stop()


if __name__ == "__main__":
    sys.exit(main())

