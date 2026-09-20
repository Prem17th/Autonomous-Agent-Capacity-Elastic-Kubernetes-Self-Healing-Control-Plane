import { CapacityDiagnosisEngine } from "../src/diagnosis/engine.ts";
import { MCPServer } from "../src/server/mcpServer.ts";
import { RecoveryPolicyEngine } from "../src/policy/policyEngine.ts";

async function runTests() {
  console.log("=== Running TypeScript Nasiko Sentinel Test Suite ===");
  let passed = 0;
  let failed = 0;

  function assert(condition: boolean, msg: string) {
    if (condition) {
      console.log(`  ✓ ${msg}`);
      passed++;
    } else {
      console.error(`  ✗ ${msg}`);
      failed++;
    }
  }

  // 1. Policy Engine: Max nodes per request check
  const policy = new RecoveryPolicyEngine();
  const deniedMax = policy.evaluate("default", 5);
  assert(!deniedMax.allowed && deniedMax.status === "POLICY_DENIED", "Policy Engine blocks >2 nodes with POLICY_DENIED");

  // 2. Policy Engine: Valid scale request allowed
  const allowed = policy.evaluate("default", 1);
  assert(allowed.allowed && allowed.status === "ALLOWED", "Policy Engine allows valid request within bounds");

  // 3. Policy Engine: Disallowed pool check
  const disallowedPool = policy.evaluate("forbidden-pool", 1);
  assert(!disallowedPool.allowed && disallowedPool.reason === "DISALLOWED_NODE_POOL", "Policy Engine blocks unauthorized node pools");

  // 4. MCP Server: Initialize method
  const mcp = new MCPServer();
  const initRes = await mcp.handleRequest({ jsonrpc: "2.0", id: 1, method: "initialize" });
  assert(initRes.result.protocolVersion === "2024-11-05", "MCP Server supports protocol version 2024-11-05");

  // 5. MCP Server: Tools List
  const listRes = await mcp.handleRequest({ jsonrpc: "2.0", id: 2, method: "tools/list" });
  assert(listRes.result.tools.length === 14, "MCP Server exposes all 14 standard tools");

  // 6. MCP Server: Diagnose capacity tool call
  const diagRes = await mcp.handleRequest({
    jsonrpc: "2.0",
    id: 3,
    method: "tools/call",
    params: { name: "diagnose_capacity", arguments: { pod_name: "agent-pending-cpu" } }
  });
  const parsedDiag = JSON.parse(diagRes.result.content[0].text);
  assert(parsedDiag.classification === "insufficient_cpu", "Deterministic diagnosis correctly identifies insufficient_cpu");

  // 7. MCP Server: Policy block over tools/call
  const scaleBlockRes = await mcp.handleRequest({
    jsonrpc: "2.0",
    id: 4,
    method: "tools/call",
    params: { name: "request_scale_up", arguments: { node_pool: "default", target_nodes: 5 } }
  });
  const parsedScaleBlock = JSON.parse(scaleBlockRes.result.content[0].text);
  assert(parsedScaleBlock.status === "POLICY_DENIED", "MCP tools/call strictly enforces RecoveryPolicyEngine supremacy");

  console.log(`\nTypeScript Test Summary: ${passed} passed, ${failed} failed.\n`);
  if (failed > 0) {
    process.exit(1);
  }
}

runTests().catch((e) => {
  console.error("Test runner failed:", e);
  process.exit(1);
});
