use crate::models::{DiagnosisClassification, DiagnosisResult, K8sEvent, Pod, PodPhase};

pub struct CapacityDiagnosisEngine;

impl CapacityDiagnosisEngine {
    pub fn new() -> Self {
        Self
    }

    pub fn diagnose(&self, pod: &Pod, events: &[K8sEvent]) -> DiagnosisResult {
        if pod.phase == PodPhase::Running || pod.phase == PodPhase::Succeeded {
            return DiagnosisResult {
                pod_name: pod.name.clone(),
                namespace: pod.namespace.clone(),
                is_unschedulable: false,
                classification: DiagnosisClassification::Unknown,
                evidence_messages: vec![format!("Pod is healthy in phase {:?}", pod.phase)],
                recommended_action: "NO_ACTION".to_string(),
                summary: format!("Pod '{}' is already healthy.", pod.name),
            };
        }

        let failure_events: Vec<&K8sEvent> = events
            .iter()
            .filter(|e| e.involved_object_name == pod.name && (e.reason == "FailedScheduling" || e.event_type == "Warning"))
            .collect();

        let messages: Vec<String> = failure_events.iter().map(|e| e.message.to_lowercase()).collect();
        let raw_evidence: Vec<String> = failure_events.iter().map(|e| format!("{}: {}", e.reason, e.message)).collect();

        if messages.iter().any(|m| m.contains("insufficient cpu")) {
            return DiagnosisResult {
                pod_name: pod.name.clone(),
                namespace: pod.namespace.clone(),
                is_unschedulable: true,
                classification: DiagnosisClassification::InsufficientCpu,
                evidence_messages: raw_evidence,
                recommended_action: "REQUEST_SCALE_UP".to_string(),
                summary: format!("Pod '{}' unschedulable due to Insufficient CPU.", pod.name),
            };
        }

        if messages.iter().any(|m| m.contains("insufficient memory")) {
            return DiagnosisResult {
                pod_name: pod.name.clone(),
                namespace: pod.namespace.clone(),
                is_unschedulable: true,
                classification: DiagnosisClassification::InsufficientMemory,
                evidence_messages: raw_evidence,
                recommended_action: "REQUEST_SCALE_UP".to_string(),
                summary: format!("Pod '{}' unschedulable due to Insufficient Memory.", pod.name),
            };
        }

        DiagnosisResult {
            pod_name: pod.name.clone(),
            namespace: pod.namespace.clone(),
            is_unschedulable: pod.phase == PodPhase::Pending,
            classification: DiagnosisClassification::Unknown,
            evidence_messages: raw_evidence,
            recommended_action: "NO_ACTION".to_string(),
            summary: format!("Pod '{}' pending without recognized bottleneck.", pod.name),
        }
    }
}
