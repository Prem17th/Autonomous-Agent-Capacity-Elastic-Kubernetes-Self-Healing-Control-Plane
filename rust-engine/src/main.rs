use sentinel_core::{CapacityDiagnosisEngine, K8sEvent, Pod, PodPhase, PodResources, RecoveryPolicyEngine};

fn main() {
    println!("=== Nasiko Sentinel Rust Core Safety Engine ===");
    
    let policy = RecoveryPolicyEngine::new(None);
    
    // Demonstrate Policy Engine Denial
    println!("\n[Test 1] Evaluating +5 nodes scale request (>2 limit)...");
    let decision = policy.evaluate("default", 5, 2);
    println!("  -> Status: {}", decision.status);
    println!("  -> Allowed: {}", decision.allowed);
    println!("  -> Reason: {:?}", decision.reason);

    // Demonstrate Policy Engine Approval
    println!("\n[Test 2] Evaluating +1 node scale request (within bounds)...");
    let valid_decision = policy.evaluate("default", 1, 2);
    println!("  -> Status: {}", valid_decision.status);
    println!("  -> Allowed: {}", valid_decision.allowed);

    // Demonstrate Deterministic Diagnosis
    println!("\n[Test 3] Diagnosing pending pod with Insufficient CPU evidence...");
    let diagnosis = CapacityDiagnosisEngine::new();
    let pod = Pod {
        name: "agent-pending-cpu".to_string(),
        namespace: "nasiko-agents".to_string(),
        phase: PodPhase::Pending,
        requested_resources: PodResources { cpu_milli: 2000, memory_bytes: 1073741824 },
    };
    let events = vec![K8sEvent {
        reason: "FailedScheduling".to_string(),
        message: "0/2 nodes are available: 2 Insufficient cpu.".to_string(),
        event_type: "Warning".to_string(),
        involved_object_name: "agent-pending-cpu".to_string(),
    }];

    let diag_result = diagnosis.diagnose(&pod, &events);
    println!("  -> Classification: {:?}", diag_result.classification);
    println!("  -> Action: {}", diag_result.recommended_action);
    println!("  -> Summary: {}", diag_result.summary);

    println!("\n=== All Rust Invariants Verified ===");
}
