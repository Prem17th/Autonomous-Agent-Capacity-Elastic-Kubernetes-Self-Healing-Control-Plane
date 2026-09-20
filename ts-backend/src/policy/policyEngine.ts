import type { PolicyDecision } from "../models/types.ts";

export interface PolicyConfig {
  max_nodes_per_request: number;
  cluster_max_nodes: number;
  cooldown_seconds: number;
  allowed_node_pools: string[];
}

export const DEFAULT_POLICY_CONFIG: PolicyConfig = {
  max_nodes_per_request: 2,
  cluster_max_nodes: 10,
  cooldown_seconds: 120,
  allowed_node_pools: ["default", "general-compute", "memory-optimized"],
};

/**
 * Authoritative Recovery Policy Engine for Nasiko Sentinel.
 * 
 * Enforces "AI proposes. Policy decides."
 * Ensures AI models cannot execute unsafe infrastructure modifications.
 */
export class RecoveryPolicyEngine {
  private config: PolicyConfig;
  private poolLastScaled: Map<string, number> = new Map();

  constructor(config: PolicyConfig = DEFAULT_POLICY_CONFIG) {
    this.config = { ...config };
  }

  public evaluate(
    nodePool: string,
    nodesRequested: number,
    currentClusterNodes: number = 2
  ): PolicyDecision {
    // 1. Max nodes per request check
    if (nodesRequested > this.config.max_nodes_per_request) {
      return {
        allowed: false,
        status: "POLICY_DENIED",
        reason: "MAX_NODES_PER_REQUEST_EXCEEDED",
        details: {
          nodes_requested: nodesRequested,
          max_nodes_per_request: this.config.max_nodes_per_request,
        },
        node_pool: nodePool,
        nodes_requested: nodesRequested,
      };
    }

    // 2. Minimum nodes check
    if (nodesRequested <= 0) {
      return {
        allowed: false,
        status: "POLICY_DENIED",
        reason: "INVALID_TARGET_NODES",
        details: { nodes_requested: nodesRequested },
        node_pool: nodePool,
        nodes_requested: nodesRequested,
      };
    }

    // 3. Allowed node pools check
    if (!this.config.allowed_node_pools.includes(nodePool)) {
      return {
        allowed: false,
        status: "POLICY_DENIED",
        reason: "DISALLOWED_NODE_POOL",
        details: {
          node_pool: nodePool,
          allowed_pools: this.config.allowed_node_pools,
        },
        node_pool: nodePool,
        nodes_requested: nodesRequested,
      };
    }

    // 4. Cluster max capacity bounds
    if (currentClusterNodes + nodesRequested > this.config.cluster_max_nodes) {
      return {
        allowed: false,
        status: "POLICY_DENIED",
        reason: "CLUSTER_CAPACITY_LIMIT_EXCEEDED",
        details: {
          current_nodes: currentClusterNodes,
          nodes_requested: nodesRequested,
          cluster_max_nodes: this.config.cluster_max_nodes,
        },
        node_pool: nodePool,
        nodes_requested: nodesRequested,
      };
    }

    // 5. Cooldown debounce timer
    const lastScaled = this.poolLastScaled.get(nodePool) || 0;
    const now = Date.now() / 1000;
    const elapsed = now - lastScaled;

    if (elapsed < this.config.cooldown_seconds && lastScaled > 0) {
      return {
        allowed: false,
        status: "POLICY_DENIED",
        reason: "COOLDOWN_ACTIVE",
        details: {
          node_pool: nodePool,
          cooldown_seconds: this.config.cooldown_seconds,
          remaining_seconds: Math.round((this.config.cooldown_seconds - elapsed) * 10) / 10,
        },
        node_pool: nodePool,
        nodes_requested: nodesRequested,
      };
    }

    return {
      allowed: true,
      status: "ALLOWED",
      node_pool: nodePool,
      nodes_requested: nodesRequested,
    };
  }

  public recordScale(nodePool: string): void {
    this.poolLastScaled.set(nodePool, Date.now() / 1000);
  }

  public resetCooldowns(): void {
    this.poolLastScaled.clear();
  }
}
