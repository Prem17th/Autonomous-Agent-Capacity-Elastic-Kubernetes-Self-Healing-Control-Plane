"""Deterministic fallback reasoner when AI models are unreachable or fail."""

from typing import Optional

from src.bedrock.models import ActionType, RecoveryContext, RecoveryProposal
from src.bedrock.provider import BedrockReasoner
from src.logger.logger import get_logger

logger = get_logger("bedrock.fallback")


class DeterministicFallbackReasoner(BedrockReasoner):
    """
    Deterministic rule-based reasoner used as an explicit fallback when Bedrock
    is unconfigured, unavailable, timed out, or returns a malformed response.
    
    Ensures zero downtime while maintaining complete transparency regarding
    the source of the recovery reasoning.
    """

    def __init__(
        self,
        bedrock_status: str = "UNAVAILABLE",
        bedrock_error: Optional[str] = None,
    ) -> None:
        self._bedrock_status = bedrock_status
        self._bedrock_error = bedrock_error

    @property
    def reasoner_name(self) -> str:
        return "deterministic_fallback"

    def is_available(self) -> bool:
        return True

    def set_bedrock_error(self, status: str, error_message: Optional[str]) -> None:
        """Update Bedrock failure status for audit transparency."""
        self._bedrock_status = status
        self._bedrock_error = error_message

    def propose_recovery(self, context: RecoveryContext) -> RecoveryProposal:
        """Map deterministic diagnosis to a safe recovery proposal."""
        diag = context.deterministic_diagnosis
        classification = str(diag.get("classification") or "unknown").lower()
        reason = diag.get("reason", "UnknownReason")

        logger.info(
            f"Generating deterministic fallback proposal for pod '{context.pod_name}' (classification: {classification})"
        )

        if classification in {"insufficient_cpu", "insufficient_memory", "too_many_pods"}:
            action = ActionType.REQUEST_SCALE_UP
            target_pool = "default"
            # If diagnosis indicated a specific pool constraint, match it if allowed
            node_pool_hint = diag.get("details", {}).get("node_pool")
            if node_pool_hint:
                target_pool = str(node_pool_hint).strip()

            params = {
                "node_pool": target_pool,
                "target_nodes": 1,
                "reason": classification,
                "agent_id": context.agent_id,
            }
            explanation = (
                f"Deterministic fallback reasoning: Scheduling failure classified as '{classification}' ({reason}). "
                f"Proposing +1 node scale-up in pool '{target_pool}' to provision required compute headroom."
            )
        else:
            action = ActionType.NO_ACTION
            params = {
                "reason": classification,
                "agent_id": context.agent_id,
            }
            explanation = (
                f"Deterministic fallback reasoning: Scheduling failure classified as '{classification}' ({reason}). "
                f"Automated compute node scaling cannot resolve this constraint without cluster configuration or quota changes."
            )

        return RecoveryProposal(
            diagnosis=classification,
            action=action,
            parameters=params,
            confidence=1.0,
            explanation=explanation,
            reasoning_source="deterministic_fallback",
            bedrock_status=self._bedrock_status,
            bedrock_error=self._bedrock_error,
            latency_ms=0.5,
        )

