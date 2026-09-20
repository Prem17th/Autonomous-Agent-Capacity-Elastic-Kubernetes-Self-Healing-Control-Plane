use crate::models::PolicyDecision;
use std::collections::HashMap;
use std::time::Instant;

pub struct PolicyConfig {
    pub max_nodes_per_request: u32,
    pub cluster_max_nodes: u32,
    pub cooldown_seconds: u64,
    pub allowed_node_pools: Vec<String>,
}

impl Default for PolicyConfig {
    fn default() -> Self {
        Self {
            max_nodes_per_request: 2,
            cluster_max_nodes: 10,
            cooldown_seconds: 120,
            allowed_node_pools: vec![
                "default".to_string(),
                "general-compute".to_string(),
                "memory-optimized".to_string(),
            ],
        }
    }
}

pub struct RecoveryPolicyEngine {
    config: PolicyConfig,
    pool_last_scaled: HashMap<String, Instant>,
}

impl RecoveryPolicyEngine {
    pub fn new(config: Option<PolicyConfig>) -> Self {
        Self {
            config: config.unwrap_or_default(),
            pool_last_scaled: HashMap::new(),
        }
    }

    pub fn evaluate(&self, node_pool: &str, nodes_requested: u32, current_cluster_nodes: u32) -> PolicyDecision {
        // 1. Max nodes per request check
        if nodes_requested > self.config.max_nodes_per_request {
            return PolicyDecision {
                allowed: false,
                status: "POLICY_DENIED".to_string(),
                reason: Some("MAX_NODES_PER_REQUEST_EXCEEDED".to_string()),
                node_pool: node_pool.to_string(),
                nodes_requested,
            };
        }

        // 2. Minimum nodes check
        if nodes_requested == 0 {
            return PolicyDecision {
                allowed: false,
                status: "POLICY_DENIED".to_string(),
                reason: Some("INVALID_TARGET_NODES".to_string()),
                node_pool: node_pool.to_string(),
                nodes_requested,
            };
        }

        // 3. Allowed node pool check
        if !self.config.allowed_node_pools.iter().any(|p| p == node_pool) {
            return PolicyDecision {
                allowed: false,
                status: "POLICY_DENIED".to_string(),
                reason: Some("DISALLOWED_NODE_POOL".to_string()),
                node_pool: node_pool.to_string(),
                nodes_requested,
            };
        }

        // 4. Cluster max capacity bounds
        if current_cluster_nodes + nodes_requested > self.config.cluster_max_nodes {
            return PolicyDecision {
                allowed: false,
                status: "POLICY_DENIED".to_string(),
                reason: Some("CLUSTER_CAPACITY_LIMIT_EXCEEDED".to_string()),
                node_pool: node_pool.to_string(),
                nodes_requested,
            };
        }

        // 5. Cooldown timer check
        if let Some(last_time) = self.pool_last_scaled.get(node_pool) {
            if last_time.elapsed().as_secs() < self.config.cooldown_seconds {
                return PolicyDecision {
                    allowed: false,
                    status: "POLICY_DENIED".to_string(),
                    reason: Some("COOLDOWN_ACTIVE".to_string()),
                    node_pool: node_pool.to_string(),
                    nodes_requested,
                };
            }
        }

        PolicyDecision {
            allowed: true,
            status: "ALLOWED".to_string(),
            reason: None,
            node_pool: node_pool.to_string(),
            nodes_requested,
        }
    }

    pub fn record_scale(&mut self, node_pool: &str) {
        self.pool_last_scaled.insert(node_pool.to_string(), Instant::now());
    }
}

