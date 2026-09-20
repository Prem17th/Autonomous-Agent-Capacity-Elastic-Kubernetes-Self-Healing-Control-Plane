/**
 * Domain types and models for Nasiko Sentinel TypeScript Engine.
 */

export type PodPhase = "Pending" | "Running" | "Succeeded" | "Failed" | "Unknown";

export interface PodResources {
  cpu_milli: number;
  memory_bytes: number;
}

export interface PodCondition {
  type: string;
  status: "True" | "False" | "Unknown";
  reason?: string;
  message?: string;
}

export interface Pod {
  name: string;
  namespace: string;
  phase: PodPhase;
  node_name?: string;
  requested_resources: PodResources;
  conditions: PodCondition[];
  created_at: string;
  labels: Record<string, string>;
}

export interface NodeCapacity {
  node_name: string;
  ready: boolean;
  allocatable_cpu_milli: number;
  allocatable_memory_bytes: number;
  requested_cpu_milli: number;
  requested_memory_bytes: number;
  available_cpu_milli: number;
  available_memory_bytes: number;
  allocatable_pods: number;
  requested_pods: number;
  available_pods: number;
  taints: Array<{ key: string; value?: string; effect: string }>;
  node_pool_labels: Record<string, string>;
}

export interface ClusterCapacitySummary {
  total_nodes: number;
  ready_nodes: number;
  total_allocatable_cpu_milli: number;
  total_requested_cpu_milli: number;
  available_cpu_milli: number;
  total_allocatable_memory_bytes: number;
  total_requested_memory_bytes: number;
  available_memory_bytes: number;
  total_allocatable_pods: number;
  total_requested_pods: number;
  available_pods: number;
  nodes: NodeCapacity[];
}

export interface Event {
  reason: string;
  message: string;
  type: "Normal" | "Warning";
  involved_object_name: string;
  involved_object_kind: string;
  first_timestamp: string;
  last_timestamp: string;
  count: number;
}

export interface DiagnosisResult {
  pod_name: string;
  namespace: string;
  is_unschedulable: boolean;
  classification: "insufficient_cpu" | "insufficient_memory" | "too_many_pods" | "resource_quota" | "node_pool_constraint" | "taint_or_constraint" | "unknown";
  evidence_messages: string[];
  recommended_action: "REQUEST_SCALE_UP" | "NO_ACTION";
  summary: string;
}

export interface RecoveryProposal {
  action: "REQUEST_SCALE_UP" | "NO_ACTION";
  node_pool: string;
  target_nodes: number;
  reason: string;
  confidence: number;
  reasoning_source: "bedrock" | "deterministic_fallback";
  agent_id?: string;
}

export interface PolicyDecision {
  allowed: boolean;
  status: "ALLOWED" | "POLICY_DENIED";
  reason?: string;
  details?: Record<string, any>;
  node_pool: string;
  nodes_requested: number;
}

export interface ScaleResult {
  scale_request_id: string;
  status: "ACCEPTED" | "POLICY_DENIED" | "FAILED";
  allowed: boolean;
  reason?: string;
  node_pool: string;
  nodes_requested: number;
  current_ready_nodes?: number;
  target_ready_nodes?: number;
  created_at: string;
  provider: string;
  agent_id?: string;
}
