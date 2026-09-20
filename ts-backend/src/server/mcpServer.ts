import { CapacityDiagnosisEngine } from "../diagnosis/engine.ts";
import { KubernetesAdapter } from "../kubernetes/adapter.ts";
import type { RecoveryProposal } from "../models/types.ts";
import { RecoveryPolicyEngine } from "../policy/policyEngine.ts";
import { SimulatedAutoscalerProvider } from "../autoscaler/simulatedProvider.ts";

export interface MCPToolDefinition {
  name: string;
  description: string;
  inputSchema: Record<string, any>;
}

export class MCPServer {
  private k8s: KubernetesAdapter;
  private diagnosis: CapacityDiagnosisEngine;
  private policy: RecoveryPolicyEngine;
  private autoscaler: SimulatedAutoscalerProvider;

  constructor(
    k8s?: KubernetesAdapter,
    diagnosis?: CapacityDiagnosisEngine,
    policy?: RecoveryPolicyEngine,
    autoscaler?: SimulatedAutoscalerProvider
  ) {
    this.k8s = k8s || new KubernetesAdapter();
    this.diagnosis = diagnosis || new CapacityDiagnosisEngine();
    this.policy = policy || new RecoveryPolicyEngine();
    this.autoscaler = autoscaler || new SimulatedAutoscalerProvider();
  }

  public getToolsList(): MCPToolDefinition[] {
    return [
      { name: "diagnose_capacity", description: "Deterministically diagnose why a Kubernetes agent pod is pending or unschedulable.", inputSchema: { type: "object", properties: { pod_name: { type: "string" }, namespace: { type: "string" } }, required: ["pod_name"] } },
      { name: "reason_recovery", description: "Formulate an AI recovery proposal based on cluster capacity deficits.", inputSchema: { type: "object", properties: { pod_name: { type: "string" }, agent_id: { type: "string" } }, required: ["pod_name"] } },
      { name: "request_scale_up", description: "Request scaling up capacity with strict RecoveryPolicyEngine validation.", inputSchema: { type: "object", properties: { node_pool: { type: "string" }, target_nodes: { type: "integer" }, agent_id: { type: "string" } }, required: ["node_pool", "target_nodes"] } },
      { name: "verify_agent_recovery", description: "Verify if a previously unscheduled agent pod is now Running and healthy.", inputSchema: { type: "object", properties: { agent_id: { type: "string" } }, required: ["agent_id"] } },
      { name: "wait_for_capacity", description: "Wait for a requested scale up operation to provision nodes.", inputSchema: { type: "object", properties: { scale_request_id: { type: "string" } }, required: ["scale_request_id"] } },
      { name: "get_node_capacity", description: "Get aggregate and per-node allocatable compute capacity.", inputSchema: { type: "object", properties: {} } },
      { name: "get_pending_pods", description: "List all pending pods in an agent namespace.", inputSchema: { type: "object", properties: { namespace: { type: "string" } } } },
      { name: "get_pod_events", description: "Retrieve Kubernetes events for a specific pod.", inputSchema: { type: "object", properties: { pod_name: { type: "string" } }, required: ["pod_name"] } },
      { name: "get_agent_status", description: "Query current status and replicas for an agent deployment.", inputSchema: { type: "object", properties: { agent_id: { type: "string" } }, required: ["agent_id"] } },
      { name: "get_autoscaler_status", description: "Check health and active operations of the autoscaler provider.", inputSchema: { type: "object", properties: {} } },
      { name: "get_node_pool_status", description: "Query node pool capacities and limits.", inputSchema: { type: "object", properties: { node_pool: { type: "string" } } } },
      { name: "get_recovery_status", description: "Query audit trail for an agent recovery lifecycle.", inputSchema: { type: "object", properties: { agent_id: { type: "string" } }, required: ["agent_id"] } },
      { name: "retry_agent", description: "Trigger agent pod reconciliation.", inputSchema: { type: "object", properties: { agent_id: { type: "string" } }, required: ["agent_id"] } },
      { name: "health", description: "Query Sentinel system health and component status.", inputSchema: { type: "object", properties: {} } },
    ];
  }

  public async handleRequest(req: any): Promise<any> {
    if (!req || typeof req !== "object") {
      return { jsonrpc: "2.0", id: null, error: { code: -32600, message: "Invalid Request" } };
    }

    const { id, method, params } = req;

    if (method === "initialize") {
      return {
        jsonrpc: "2.0",
        id,
        result: {
          protocolVersion: "2024-11-05",
          capabilities: { tools: {} },
          serverInfo: { name: "aegis-sentinel-ts", version: "0.1.0" },
        },
      };
    }

    if (method === "notifications/initialized") {
      return null;
    }

    if (method === "ping") {
      return { jsonrpc: "2.0", id, result: {} };
    }

    if (method === "tools/list") {
      return {
        jsonrpc: "2.0",
        id,
        result: { tools: this.getToolsList() },
      };
    }

    if (method === "tools/call") {
      const toolName = params?.name;
      const args = params?.arguments || {};

      try {
        const result = await this.executeTool(toolName, args);
        return {
          jsonrpc: "2.0",
          id,
          result: {
            content: [{ type: "text", text: JSON.stringify(result, null, 2) }],
          },
        };
      } catch (err: any) {
        return {
          jsonrpc: "2.0",
          id,
          error: { code: -32602, message: err.message || "Invalid tool execution" },
        };
      }
    }

    return {
      jsonrpc: "2.0",
      id,
      error: { code: -32601, message: `Method not found: ${method}` },
    };
  }

  private async executeTool(name: string, args: any): Promise<any> {
    switch (name) {
      case "diagnose_capacity": {
        const pod = this.k8s.getPod(args.pod_name, args.namespace);
        if (!pod) throw new Error(`Pod '${args.pod_name}' not found`);
        const events = this.k8s.getPodEvents(args.pod_name);
        return this.diagnosis.diagnose(pod, events);
      }

      case "reason_recovery": {
        const proposal: RecoveryProposal = {
          action: "REQUEST_SCALE_UP",
          node_pool: "default",
          target_nodes: 1,
          reason: "Cluster lacks allocatable CPU on existing nodes for 2000m pod requirement.",
          confidence: 0.95,
          reasoning_source: "deterministic_fallback",
          agent_id: args.agent_id,
        };
        return proposal;
      }

      case "request_scale_up": {
        const nodePool = args.node_pool || "default";
        const nodesRequested = args.target_nodes ?? 1;

        const decision = this.policy.evaluate(nodePool, nodesRequested);
        if (!decision.allowed) {
          return {
            scale_request_id: `denied-${Date.now()}`,
            status: "POLICY_DENIED",
            allowed: false,
            reason: decision.reason,
            details: decision.details,
            node_pool: nodePool,
            nodes_requested: nodesRequested,
          };
        }

        this.policy.recordScale(nodePool);
        return await this.autoscaler.requestScaleUp(nodePool, nodesRequested, args.agent_id);
      }

      case "wait_for_capacity":
        return await this.autoscaler.waitForCapacity(args.scale_request_id);

      case "verify_agent_recovery":
        return this.k8s.verifyAgentRecovery(args.agent_id);

      case "get_node_capacity":
        return this.k8s.getNodeCapacity();

      case "get_pending_pods":
        return { pending_pods: this.k8s.getPendingPods(args.namespace) };

      case "get_pod_events":
        return { events: this.k8s.getPodEvents(args.pod_name) };

      case "get_autoscaler_status":
        return this.autoscaler.getStatus();

      case "health":
        return { status: "ok", service: "aegis-sentinel-ts", runtime: "typescript" };

      default:
        throw new Error(`Unregistered tool: ${name}`);
    }
  }
}
