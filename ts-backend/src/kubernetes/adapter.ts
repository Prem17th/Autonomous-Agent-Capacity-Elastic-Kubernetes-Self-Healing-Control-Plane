import type { ClusterCapacitySummary, Event, NodeCapacity, Pod } from "../models/types.ts";

export class KubernetesAdapter {
  private pods: Map<string, Pod> = new Map();
  private events: Event[] = [];
  private nodes: NodeCapacity[] = [];

  constructor() {
    this.seedMockData();
  }

  private seedMockData(): void {
    // Seed test pending pod
    this.pods.set("agent-pending-cpu", {
      name: "agent-pending-cpu",
      namespace: "nasiko-agents",
      phase: "Pending",
      requested_resources: { cpu_milli: 2000, memory_bytes: 1073741824 },
      conditions: [{ type: "PodScheduled", status: "False", reason: "Unschedulable" }],
      created_at: new Date().toISOString(),
      labels: { "nasiko.io/agent-id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11" },
    });

    // Seed events
    this.events.push({
      reason: "FailedScheduling",
      message: "0/2 nodes are available: 2 Insufficient cpu.",
      type: "Warning",
      involved_object_name: "agent-pending-cpu",
      involved_object_kind: "Pod",
      first_timestamp: new Date().toISOString(),
      last_timestamp: new Date().toISOString(),
      count: 3,
    });

    // Seed nodes
    this.nodes = [
      {
        node_name: "node-worker-1",
        ready: true,
        allocatable_cpu_milli: 2000,
        allocatable_memory_bytes: 8589934592,
        requested_cpu_milli: 1700,
        requested_memory_bytes: 4294967296,
        available_cpu_milli: 300,
        available_memory_bytes: 4294967296,
        allocatable_pods: 110,
        requested_pods: 45,
        available_pods: 65,
        taints: [],
        node_pool_labels: { "karpenter.sh/nodepool": "default" },
      },
      {
        node_name: "node-worker-2",
        ready: true,
        allocatable_cpu_milli: 2000,
        allocatable_memory_bytes: 8589934592,
        requested_cpu_milli: 1600,
        requested_memory_bytes: 4294967296,
        available_cpu_milli: 400,
        available_memory_bytes: 4294967296,
        allocatable_pods: 110,
        requested_pods: 40,
        available_pods: 70,
        taints: [],
        node_pool_labels: { "karpenter.sh/nodepool": "default" },
      },
    ];
  }

  public getPod(name: string, namespace: string = "nasiko-agents"): Pod | undefined {
    return this.pods.get(name);
  }

  public getPendingPods(namespace: string = "nasiko-agents"): Pod[] {
    return Array.from(this.pods.values()).filter(p => p.phase === "Pending");
  }

  public getPodEvents(podName: string): Event[] {
    return this.events.filter(e => e.involved_object_name === podName);
  }

  public getNodeCapacity(): ClusterCapacitySummary {
    const totalAllocCpu = this.nodes.reduce((acc, n) => acc + n.allocatable_cpu_milli, 0);
    const totalReqCpu = this.nodes.reduce((acc, n) => acc + n.requested_cpu_milli, 0);
    const totalAllocMem = this.nodes.reduce((acc, n) => acc + n.allocatable_memory_bytes, 0);
    const totalReqMem = this.nodes.reduce((acc, n) => acc + n.requested_memory_bytes, 0);

    return {
      total_nodes: this.nodes.length,
      ready_nodes: this.nodes.filter(n => n.ready).length,
      total_allocatable_cpu_milli: totalAllocCpu,
      total_requested_cpu_milli: totalReqCpu,
      available_cpu_milli: totalAllocCpu - totalReqCpu,
      total_allocatable_memory_bytes: totalAllocMem,
      total_requested_memory_bytes: totalReqMem,
      available_memory_bytes: totalAllocMem - totalReqMem,
      total_allocatable_pods: 220,
      total_requested_pods: 85,
      available_pods: 135,
      nodes: this.nodes,
    };
  }

  public verifyAgentRecovery(agentId: string): { agent_id: string; recovered: boolean; status: string; ready_replicas: number } {
    return {
      agent_id: agentId,
      recovered: true,
      status: "Running",
      ready_replicas: 1,
    };
  }

  public checkConnection(): boolean {
    return true;
  }
}
