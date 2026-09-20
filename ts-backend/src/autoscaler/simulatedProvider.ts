import type { ScaleResult } from "../models/types.ts";

export interface AutoscalerStatus {
  provider_type: string;
  status: string;
  ready: boolean;
  active_operations: number;
  managed_node_pools: string[];
}

export class SimulatedAutoscalerProvider {
  private activeOperations: Map<string, any> = new Map();
  private readyNodesCount: number = 2;

  public async requestScaleUp(
    nodePool: string,
    targetNodes: number,
    agentId?: string
  ): Promise<ScaleResult> {
    const opId = `scale-op-${Math.random().toString(36).substring(2, 10)}`;
    const scaleResult: ScaleResult = {
      scale_request_id: opId,
      status: "ACCEPTED",
      allowed: true,
      node_pool: nodePool,
      nodes_requested: targetNodes,
      current_ready_nodes: this.readyNodesCount,
      target_ready_nodes: this.readyNodesCount + targetNodes,
      created_at: new Date().toISOString(),
      provider: "simulated_ts",
      agent_id: agentId,
    };

    this.activeOperations.set(opId, {
      ...scaleResult,
      readyAt: Date.now() + 200, // Simulated provision latency
    });

    return scaleResult;
  }

  public async waitForCapacity(opId: string, timeoutSeconds: number = 10): Promise<any> {
    const op = this.activeOperations.get(opId);
    if (!op) {
      throw new Error(`Scale operation ${opId} not found`);
    }

    this.readyNodesCount = op.target_ready_nodes;

    return {
      status: "READY",
      operation_id: opId,
      ready_nodes_count: this.readyNodesCount,
      provisioned_nodes: [
        {
          node_name: `sentinel-ts-node-${Math.random().toString(36).substring(2, 8)}`,
          node_pool: op.node_pool,
          instance_type: "t3.xlarge",
          allocatable_cpu_milli: 4000,
          allocatable_memory_bytes: 17179869184,
          ready: true,
        },
      ],
      elapsed_seconds: 0.2,
    };
  }

  public getStatus(): AutoscalerStatus {
    return {
      provider_type: "simulated_typescript",
      status: "ready",
      ready: true,
      active_operations: this.activeOperations.size,
      managed_node_pools: ["default", "general-compute", "memory-optimized"],
    };
  }
}
