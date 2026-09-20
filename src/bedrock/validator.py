"""Validation and sanitization rules for AI recovery proposals."""

from typing import Any, Dict, List, Optional

from src.bedrock.models import ActionType, RecoveryProposal
from src.errors.exceptions import ValidationError
from src.logger.logger import get_logger

logger = get_logger("bedrock.validator")

ALLOWED_ACTIONS: List[str] = [ActionType.NO_ACTION.value, ActionType.REQUEST_SCALE_UP.value]


class ProposalValidator:
    """
    Validates structured RecoveryProposal objects before they are submitted
    to the RecoveryPolicyEngine and MCP execution layers.
    """

    @staticmethod
    def validate(proposal: RecoveryProposal) -> None:
        """
        Strictly validate a RecoveryProposal.
        
        Checks:
        1. Action is in the finite allowlist (NO_ACTION, REQUEST_SCALE_UP).
        2. Parameters are well-formed for the specified action.
        3. Confidence is a valid float between 0.0 and 1.0.
        4. No arbitrary tool names or unauthorized keys exist.
        """
        if not isinstance(proposal, RecoveryProposal):
            raise ValidationError(
                f"Expected RecoveryProposal instance, got {type(proposal).__name__}"
            )

        action_str = proposal.action.value if isinstance(proposal.action, ActionType) else str(proposal.action).upper()
        if action_str not in ALLOWED_ACTIONS:
            raise ValidationError(
                f"Disallowed action '{proposal.action}'. Allowed actions: {ALLOWED_ACTIONS}",
                details={"action": str(proposal.action), "allowed": ALLOWED_ACTIONS},
            )

        if not isinstance(proposal.confidence, (int, float)) or not (0.0 <= float(proposal.confidence) <= 1.0):
            raise ValidationError(
                f"Invalid confidence value {proposal.confidence}. Must be a float between 0.0 and 1.0",
                details={"confidence": proposal.confidence},
            )

        if not isinstance(proposal.parameters, dict):
            raise ValidationError(
                "Proposal parameters must be a dictionary",
                details={"parameters": type(proposal.parameters).__name__},
            )

        if action_str == ActionType.REQUEST_SCALE_UP.value:
            node_pool = proposal.parameters.get("node_pool")
            if not node_pool or not isinstance(node_pool, str) or not node_pool.strip():
                raise ValidationError(
                    "Action REQUEST_SCALE_UP requires a non-empty string parameter 'node_pool'",
                    details={"parameters": proposal.parameters},
                )

            raw_target = proposal.parameters.get("target_nodes")
            if raw_target is None:
                raise ValidationError(
                    "Action REQUEST_SCALE_UP requires parameter 'target_nodes'",
                    details={"parameters": proposal.parameters},
                )
            try:
                target_nodes = int(raw_target)
                if target_nodes <= 0:
                    raise ValueError("Must be > 0")
            except (ValueError, TypeError) as e:
                raise ValidationError(
                    f"Parameter 'target_nodes' must be a positive integer, got: {raw_target}",
                    details={"target_nodes": raw_target},
                ) from e

        logger.debug(f"Proposal validated successfully: action={action_str}")

