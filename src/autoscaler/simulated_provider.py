"""Simulated Autoscaler Provider for local testing and zero-cloud execution."""

from datetime import datetime, timezone
import time
from typing import Any, Dict, List, Optional
import uuid

from src.autoscaler.models import (
    NodePoolStatus,
    OperationState,
    ScaleOperation,
    ScaleRequest,
)
from src.autoscaler.provider import AutoscalerProvider
from src.errors.exceptions import InfrastructureError, ValidationError
from src.kubernetes.adapter import KubernetesAdapter
from src.logger.logger import get_logger

logger = get_logger("autoscaler.simulated")


class SimulatedAutoscalerProvider(AutoscalerProvider):
    """
    Simulated Autoscaler Provider for local offline execution, demonstration, and tests.
    
    Accurately emulates cloud autoscaler mechanics (Karpenter/CAS) including
    provisioning delays, node readiness transitions, capacity injection into
    the KubernetesAdapter client, and fault injection (timeouts, failures).
    """

    def __init__(
        self,
        adapter: Optional[KubernetesAdapter] = None,
        provision_delay_seconds: float = 0.1,
        simulate_failure: bool = False,
        simulate_timeout: bool = False,
    ) -> None:
        self.adapter = adapter
        self.provision_delay_seconds = provision_delay_seconds
        self.simulate_failure = simulate_failure
        self.simulate_timeout = simulate_timeout

        self._operations: Dict[str, ScaleOperation] = {}
        self._node_pools: Dict[str, NodePoolStatus] = {
            "default": NodePoolStatus(
                node_pool="default",
                current_nodes=2,
                ready_nodes=2,
                pending_nodes=0,
                min_nodes=1,
                max_nodes=10,
                instance_types=["t3.xlarge", "m5.xlarge"],
                status="Ready",
            ),
            "general-compute": NodePoolStatus(
                node_pool="general-compute",
                current_nodes=2,
                ready_nodes=2,
                pending_nodes=0,
                min_nodes=0,
                max_nodes=10,
                instance_types=["c5.2xlarge", "c6i.2xlarge"],
                status="Ready",
            ),
            "memory-optimized": NodePoolStatus(
                node_pool="memory-optimized",
                current_nodes=1,
                ready_nodes=1,
                pending_nodes=0,
                min_nodes=0,
                max_nodes=6,
                instance_types=["r5.2xlarge", "r6i.2xlarge"],
                status="Ready",
            ),
        }

    @property
    def provider_type(self) -> str:
        return "simulated"

    def request_scale_up(self, request: ScaleRequest) -> ScaleOperation:
        """Submit a simulated scale-up operation."""
        if request.nodes_requested <= 0:
            raise ValidationError(f"Invalid nodes_requested: {request.nodes_requested}")

        pool_name = request.node_pool
        pool = self._node_pools.get(pool_name)
        current_ready = pool.ready_nodes if pool else 2
        target_ready = current_ready + request.nodes_requested

        op_id = f"scale-op-{uuid.uuid4().hex[:8]}"

        if request.dry_run:
            logger.info(f"Dry-run scale request {op_id} evaluated successfully for pool '{pool_name}'")
            return ScaleOperation(
                operation_id=op_id,
                node_pool=pool_name,
                nodes_requested=request.nodes_requested,
                state=OperationState.READY,
                current_ready_nodes=current_ready,
                target_ready_nodes=target_ready,
                estimated_latency_seconds=0,
                error_message=None,
            )

        operation = ScaleOperation(
            operation_id=op_id,
            node_pool=pool_name,
            nodes_requested=request.nodes_requested,
            state=OperationState.PROVISIONING,
            current_ready_nodes=current_ready,
            target_ready_nodes=target_ready,
            estimated_latency_seconds=max(int(self.provision_delay_seconds), 1),
        )
        self._operations[op_id] = operation

        if pool:
            pool.pending_nodes += request.nodes_requested
            pool.current_nodes += request.nodes_requested

        logger.info(
            f"Created simulated scale operation {op_id}: requesting +{request.nodes_requested} nodes in '{pool_name}'"
        )
        return operation

    def get_operation_status(self, operation_id: str) -> Optional[ScaleOperation]:
        """Retrieve operation status and check if time-based provisioning has completed."""
        op = self._operations.get(operation_id)
        if op is None:
            return None

        if op.state == OperationState.PROVISIONING:
            created_ts = datetime.fromisoformat(op.created_at).timestamp()
            now_ts = datetime.now(timezone.utc).timestamp()
            elapsed = now_ts - created_ts

            if self.simulate_failure:
                op.state = OperationState.FAILED
                op.error_message = "Simulated cloud provider error: InsufficientInstanceCapacity"
                op.updated_at = datetime.now(timezone.utc).isoformat()
            elif not self.simulate_timeout and elapsed >= self.provision_delay_seconds:
                self._complete_provisioning(op)

        return op

    def _complete_provisioning(self, op: ScaleOperation) -> None:
        """Mark operation ready and generate provisioned node details."""
        op.state = OperationState.READY
        op.updated_at = datetime.now(timezone.utc).isoformat()
        
        now_iso = datetime.now(timezone.utc).isoformat()
        pool = self._node_pools.get(op.node_pool)

        provisioned_list: List[Dict[str, Any]] = []
        for i in range(op.nodes_requested):
            node_name = f"sentinel-sim-{op.node_pool}-{uuid.uuid4().hex[:6]}"
            node_info = {
                "node_name": node_name,
                "node_pool": op.node_pool,
                "instance_type": pool.instance_types[0] if pool else "t3.xlarge",
                "allocatable_cpu_milli": 4000,
                "allocatable_memory_bytes": 17179869184,  # 16 GiB
                "ready": True,
                "taints": [],
                "joined_at": now_iso,
            }
            provisioned_list.append(node_info)

            # If an adapter with a mock client is connected, inject this node into the cluster view
            if self.adapter and hasattr(self.adapter.client, "nodes") and isinstance(self.adapter.client.nodes, list):
                raw_node_dict = {
                    "metadata": {
                        "name": node_name,
                        "labels": {
                            "topology.kubernetes.io/zone": "us-east-1a",
                            "karpenter.sh/nodepool": op.node_pool,
                        },
                        "creationTimestamp": now_iso,
                    },
                    "status": {
                        "capacity": {"cpu": "4000m", "memory": "16Gi", "pods": "110"},
                        "allocatable": {"cpu": "4000m", "memory": "16Gi", "pods": "110"},
                        "conditions": [{"type": "Ready", "status": "True"}],
                    },
                    "spec": {"taints": []},
                }
                self.adapter.client.nodes.append(raw_node_dict)

        op.provisioned_nodes = provisioned_list

        if pool:
            pool.pending_nodes = max(0, pool.pending_nodes - op.nodes_requested)
            pool.ready_nodes += op.nodes_requested

        logger.info(f"Scale operation {op.operation_id} reached READY state with {len(provisioned_list)} new node(s)")

    def wait_for_capacity(
        self,
        operation_id: Optional[str] = None,
        target_ready_nodes: Optional[int] = None,
        timeout_seconds: int = 180,
        poll_interval_seconds: float = 0.05,
    ) -> Dict[str, Any]:
        """Poll until operation finishes provisioning or timeout occurs."""
        start_time = time.time()

        if operation_id:
            op = self.get_operation_status(operation_id)
            if op is None:
                raise ValidationError(f"Scale operation '{operation_id}' not found")
        else:
            op = None

        while True:
            now = time.time()
            elapsed = now - start_time

            if op is not None:
                current_op = self.get_operation_status(operation_id)
                if current_op.state == OperationState.READY:
                    return {
                        "status": "READY",
                        "operation_id": current_op.operation_id,
                        "ready_nodes_count": current_op.target_ready_nodes,
                        "provisioned_nodes": current_op.provisioned_nodes,
                        "elapsed_seconds": round(elapsed, 2),
                    }
                elif current_op.state == OperationState.FAILED:
                    return {
                        "status": "FAILED",
                        "operation_id": current_op.operation_id,
                        "error": current_op.error_message or "Provisioning failed",
                        "elapsed_seconds": round(elapsed, 2),
                    }

            if target_ready_nodes is not None:
                pool = self._node_pools.get("default")
                if pool and pool.ready_nodes >= target_ready_nodes:
                    return {
                        "status": "READY",
                        "ready_nodes_count": pool.ready_nodes,
                        "provisioned_nodes": [],
                        "elapsed_seconds": round(elapsed, 2),
                    }

            if elapsed >= timeout_seconds:
                if op is not None:
                    op.state = OperationState.TIMEOUT
                return {
                    "status": "TIMEOUT",
                    "operation_id": operation_id,
                    "error": f"Timed out waiting for capacity after {round(elapsed, 2)}s",
                    "elapsed_seconds": round(elapsed, 2),
                }

            time.sleep(poll_interval_seconds)

    def get_autoscaler_status(self) -> Dict[str, Any]:
        """Return status and health metrics of the simulated autoscaler."""
        total_ops = len(self._operations)
        ready_ops = sum(1 for op in self._operations.values() if op.state == OperationState.READY)
        prov_ops = sum(1 for op in self._operations.values() if op.state == OperationState.PROVISIONING)
        failed_ops = sum(1 for op in self._operations.values() if op.state in {OperationState.FAILED, OperationState.TIMEOUT})

        return {
            "status": "HEALTHY",
            "provider": self.provider_type,
            "mode": "simulation",
            "active_operations_count": prov_ops,
            "completed_operations_count": ready_ops,
            "failed_operations_count": failed_ops,
            "total_operations_count": total_ops,
            "configured_node_pools": list(self._node_pools.keys()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def get_node_pool_status(self, node_pool: str = "default") -> NodePoolStatus:
        """Get status of a specific node pool."""
        pool = self._node_pools.get(node_pool)
        if pool is None:
            raise ValidationError(
                f"Unknown node pool '{node_pool}'. Available pools: {sorted(self._node_pools.keys())}"
            )
        return pool

    def list_node_pools(self) -> List[NodePoolStatus]:
        """List all node pools."""
        return list(self._node_pools.values())

