import type { DiagnosisResult, Event, Pod } from "../models/types.ts";

/**
 * Deterministic Capacity Diagnosis Engine for Kubernetes agent pods.
 * 
 * Inspects kube-scheduler events and pod conditions to classify bottlenecks
 * with zero hallucination.
 */
export class CapacityDiagnosisEngine {
  public diagnose(pod: Pod, events: Event[]): DiagnosisResult {
    // Check if pod is already running or succeeded
    if (pod.phase === "Running" || pod.phase === "Succeeded") {
      return {
        pod_name: pod.name,
        namespace: pod.namespace,
        is_unschedulable: false,
        classification: "unknown",
        evidence_messages: [`Pod is currently in phase '${pod.phase}'. No recovery needed.`],
        recommended_action: "NO_ACTION",
        summary: `Pod '${pod.name}' is already healthy in phase '${pod.phase}'.`,
      };
    }

    const failureEvents = events.filter(e => 
      e.involved_object_name === pod.name && 
      (e.reason === "FailedScheduling" || e.reason === "FailedCreate" || e.type === "Warning")
    );

    const messages = failureEvents.map(e => e.message.toLowerCase());
    const rawEvidence = failureEvents.map(e => `${e.reason}: ${e.message}`);

    // Deterministic classification rules
    if (messages.some(m => m.includes("insufficient cpu"))) {
      return {
        pod_name: pod.name,
        namespace: pod.namespace,
        is_unschedulable: true,
        classification: "insufficient_cpu",
        evidence_messages: rawEvidence,
        recommended_action: "REQUEST_SCALE_UP",
        summary: `Deterministic diagnosis: Pod '${pod.name}' unschedulable due to Insufficient CPU headroom.`,
      };
    }

    if (messages.some(m => m.includes("insufficient memory"))) {
      return {
        pod_name: pod.name,
        namespace: pod.namespace,
        is_unschedulable: true,
        classification: "insufficient_memory",
        evidence_messages: rawEvidence,
        recommended_action: "REQUEST_SCALE_UP",
        summary: `Deterministic diagnosis: Pod '${pod.name}' unschedulable due to Insufficient Memory headroom.`,
      };
    }

    if (messages.some(m => m.includes("too many pods"))) {
      return {
        pod_name: pod.name,
        namespace: pod.namespace,
        is_unschedulable: true,
        classification: "too_many_pods",
        evidence_messages: rawEvidence,
        recommended_action: "REQUEST_SCALE_UP",
        summary: `Deterministic diagnosis: Pod '${pod.name}' unschedulable due to node pod limit reached.`,
      };
    }

    if (messages.some(m => m.includes("exceeded quota") || m.includes("resourcequota"))) {
      return {
        pod_name: pod.name,
        namespace: pod.namespace,
        is_unschedulable: true,
        classification: "resource_quota",
        evidence_messages: rawEvidence,
        recommended_action: "NO_ACTION",
        summary: `Deterministic diagnosis: Pod '${pod.name}' blocked by namespace ResourceQuota limit.`,
      };
    }

    if (messages.some(m => m.includes("matchpodaffinity") || m.includes("nodeselector") || m.includes("node(s) didn't match"))) {
      return {
        pod_name: pod.name,
        namespace: pod.namespace,
        is_unschedulable: true,
        classification: "node_pool_constraint",
        evidence_messages: rawEvidence,
        recommended_action: "NO_ACTION",
        summary: `Deterministic diagnosis: Pod '${pod.name}' node selector / affinity mismatch.`,
      };
    }

    if (messages.some(m => m.includes("taint") || m.includes("toleration"))) {
      return {
        pod_name: pod.name,
        namespace: pod.namespace,
        is_unschedulable: true,
        classification: "taint_or_constraint",
        evidence_messages: rawEvidence,
        recommended_action: "NO_ACTION",
        summary: `Deterministic diagnosis: Pod '${pod.name}' untolerated node taints.`,
      };
    }

    return {
      pod_name: pod.name,
      namespace: pod.namespace,
      is_unschedulable: pod.phase === "Pending",
      classification: "unknown",
      evidence_messages: rawEvidence.length > 0 ? rawEvidence : ["No recognized scheduler error patterns found."],
      recommended_action: "NO_ACTION",
      summary: `Pod '${pod.name}' pending without recognized capacity pattern.`,
    };
  }
}
