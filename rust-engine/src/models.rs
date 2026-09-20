use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum PodPhase {
    Pending,
    Running,
    Succeeded,
    Failed,
    Unknown,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PodResources {
    pub cpu_milli: u32,
    pub memory_bytes: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Pod {
    pub name: String,
    pub namespace: String,
    pub phase: PodPhase,
    pub requested_resources: PodResources,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct K8sEvent {
    pub reason: String,
    pub message: String,
    pub event_type: String,
    pub involved_object_name: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum DiagnosisClassification {
    InsufficientCpu,
    InsufficientMemory,
    TooManyPods,
    ResourceQuota,
    NodePoolConstraint,
    TaintOrConstraint,
    Unknown,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DiagnosisResult {
    pub pod_name: String,
    pub namespace: String,
    pub is_unschedulable: bool,
    pub classification: DiagnosisClassification,
    pub evidence_messages: Vec<String>,
    pub recommended_action: String,
    pub summary: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PolicyDecision {
    pub allowed: bool,
    pub status: String,
    pub reason: Option<String>,
    pub node_pool: String,
    pub nodes_requested: u32,
}
