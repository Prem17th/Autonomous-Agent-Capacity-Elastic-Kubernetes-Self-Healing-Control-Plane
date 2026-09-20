"""Abstract Autoscaler Provider Interface for Aegis Sentinel."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from src.autoscaler.models import NodePoolStatus, ScaleOperation, ScaleRequest


class AutoscalerProvider(ABC):
    """
    Abstract interface for capacity provisioning mechanisms.
    
    Implementations may interact with cloud providers (Karpenter on AWS EKS,
    Cluster Autoscaler with ASGs) or simulated local environments.
    """

    @property
    @abstractmethod
    def provider_type(self) -> str:
        """Name/type of the autoscaler provider (e.g. 'simulated', 'karpenter', 'cluster-autoscaler')."""
        pass

    @abstractmethod
    def request_scale_up(self, request: ScaleRequest) -> ScaleOperation:
        """
        Submit a request to scale up capacity in the target node pool.
        
        Args:
            request: ScaleRequest describing the desired capacity.
            
        Returns:
            ScaleOperation detailing the accepted operation.
        """
        pass

    @abstractmethod
    def get_operation_status(self, operation_id: str) -> Optional[ScaleOperation]:
        """
        Query the current status of a scaling operation.
        
        Args:
            operation_id: Unique identifier of the scaling operation.
            
        Returns:
            ScaleOperation if found, None otherwise.
        """
        pass

    @abstractmethod
    def wait_for_capacity(
        self,
        operation_id: Optional[str] = None,
        target_ready_nodes: Optional[int] = None,
        timeout_seconds: int = 180,
        poll_interval_seconds: float = 1.0,
    ) -> Dict[str, Any]:
        """
        Wait until requested capacity is ready and allocatable or timeout expires.
        
        Args:
            operation_id: Optional operation correlation ID.
            target_ready_nodes: Optional minimum ready node count threshold.
            timeout_seconds: Maximum wait duration.
            poll_interval_seconds: Interval between polling checks.
            
        Returns:
            Dict containing status (READY/TIMEOUT/FAILED), ready_nodes_count, provisioned_nodes, elapsed_seconds.
        """
        pass

    @abstractmethod
    def get_autoscaler_status(self) -> Dict[str, Any]:
        """
        Query the health, readiness, and metrics of the autoscaling subsystem.
        
        Returns:
            Dict describing autoscaler health, provider type, and active operations.
        """
        pass

    @abstractmethod
    def get_node_pool_status(self, node_pool: str = "default") -> NodePoolStatus:
        """
        Query the capacity and instance counts of a specific node pool.
        
        Args:
            node_pool: Target node pool identifier.
            
        Returns:
            NodePoolStatus instance.
        """
        pass

    @abstractmethod
    def list_node_pools(self) -> List[NodePoolStatus]:
        """List all available node pools and their statuses."""
        pass

