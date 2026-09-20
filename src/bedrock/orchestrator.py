"""Unified reasoning orchestrator with transparent fallback and validation."""

from typing import Optional

from src.bedrock.fallback_reasoner import DeterministicFallbackReasoner
from src.bedrock.models import RecoveryContext, RecoveryProposal
from src.bedrock.provider import BedrockReasoner
from src.bedrock.validator import ProposalValidator
from src.errors.exceptions import ValidationError
from src.logger.logger import get_logger

logger = get_logger("bedrock.orchestrator")


class SentinelRecoveryReasoner:
    """
    Orchestrates AI reasoning with mandatory output validation and explicit
    deterministic fallback when Bedrock is unconfigured, timed out, or unavailable.
    """

    def __init__(
        self,
        primary_reasoner: Optional[BedrockReasoner] = None,
        fallback_reasoner: Optional[DeterministicFallbackReasoner] = None,
    ) -> None:
        self.primary_reasoner = primary_reasoner
        self.fallback_reasoner = fallback_reasoner or DeterministicFallbackReasoner()

    def evaluate(self, context: RecoveryContext) -> RecoveryProposal:
        """
        Produce a validated RecoveryProposal from the primary reasoner or fallback.
        
        Guarantees:
        1. Output is strictly validated by ProposalValidator.
        2. If primary reasoner fails, gracefully trips to DeterministicFallbackReasoner.
        3. reasoning_source is explicitly set to 'bedrock' or 'deterministic_fallback'.
        """
        # 1. Check if primary reasoner is available
        if self.primary_reasoner is None or not self.primary_reasoner.is_available():
            logger.info("Primary Bedrock reasoner is unavailable; using deterministic fallback")
            self.fallback_reasoner.set_bedrock_error(
                status="UNAVAILABLE",
                error_message="Primary Bedrock reasoner is unconfigured or unavailable",
            )
            proposal = self.fallback_reasoner.propose_recovery(context)
            ProposalValidator.validate(proposal)
            return proposal

        # 2. Attempt primary reasoning with timeout and error capture
        try:
            proposal = self.primary_reasoner.propose_recovery(context)
            # Validate output schema and action bounds
            ProposalValidator.validate(proposal)
            return proposal

        except TimeoutError as te:
            logger.warning(f"Bedrock reasoning timed out: {te}; falling back to deterministic reasoner")
            self.fallback_reasoner.set_bedrock_error(
                status="TIMEOUT",
                error_message=f"Bedrock reasoning timed out: {te}",
            )
            fallback_prop = self.fallback_reasoner.propose_recovery(context)
            ProposalValidator.validate(fallback_prop)
            return fallback_prop

        except ValidationError as ve:
            logger.warning(f"Bedrock returned invalid proposal: {ve}; falling back to deterministic reasoner")
            self.fallback_reasoner.set_bedrock_error(
                status="ERROR",
                error_message=f"Model output validation failed: {ve.message}",
            )
            fallback_prop = self.fallback_reasoner.propose_recovery(context)
            ProposalValidator.validate(fallback_prop)
            return fallback_prop

        except Exception as e:
            logger.warning(f"Bedrock invocation failed: {e}; falling back to deterministic reasoner")
            self.fallback_reasoner.set_bedrock_error(
                status="ERROR",
                error_message=f"Bedrock execution error: {str(e)}",
            )
            fallback_prop = self.fallback_reasoner.propose_recovery(context)
            ProposalValidator.validate(fallback_prop)
            return fallback_prop

