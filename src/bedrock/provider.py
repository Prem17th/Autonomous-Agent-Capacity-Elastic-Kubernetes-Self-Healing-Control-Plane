"""Abstract Reasoner Interface for Sentinel Phase 4."""

from abc import ABC, abstractmethod

from src.bedrock.models import RecoveryContext, RecoveryProposal


class BedrockReasoner(ABC):
    """
    Abstract interface for AI reasoning and recovery planning.
    
    Implementations may invoke Amazon Bedrock Runtime via boto3,
    a high-fidelity Mock reasoner for tests, or a deterministic fallback rule engine.
    """

    @property
    @abstractmethod
    def reasoner_name(self) -> str:
        """Identifier of the reasoning backend (e.g. 'bedrock', 'mock_bedrock', 'deterministic_fallback')."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check whether the reasoning backend is configured and reachable."""
        pass

    @abstractmethod
    def propose_recovery(self, context: RecoveryContext) -> RecoveryProposal:
        """
        Evaluate structured cluster context and return a structured recovery proposal.
        
        Args:
            context: Sanitized, typed facts regarding the pending pod and cluster state.
            
        Returns:
            RecoveryProposal containing recommended action, parameters, and rationale.
        """
        pass

