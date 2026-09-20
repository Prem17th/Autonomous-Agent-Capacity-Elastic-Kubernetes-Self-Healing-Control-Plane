"""Mock Bedrock Reasoner for offline execution and test suites."""

import time
from typing import Any, Dict, Optional

from src.bedrock.models import ActionType, RecoveryContext, RecoveryProposal
from src.bedrock.provider import BedrockReasoner
from src.logger.logger import get_logger

logger = get_logger("bedrock.mock")


class MockBedrockReasoner(BedrockReasoner):
    """
    High-fidelity Mock reasoner that emulates Amazon Bedrock Claude/Nova reasoning
    without requiring AWS credentials, network access, or boto3.
    """

    def __init__(
        self,
        model_id: str = "mock-bedrock-model",
        simulate_timeout: bool = False,
        simulate_error: bool = False,
        simulate_malformed: bool = False,
        simulate_invalid_action: bool = False,
        latency_ms: float = 25.0,
    ) -> None:
        self.model_id = model_id
        self.simulate_timeout = simulate_timeout
        self.simulate_error = simulate_error
        self.simulate_malformed = simulate_malformed
        self.simulate_invalid_action = simulate_invalid_action
        self.latency_ms = latency_ms

    @property
    def reasoner_name(self) -> str:
        return f"mock_bedrock({self.model_id})"

    def is_available(self) -> bool:
        return True

    def propose_recovery(self, context: RecoveryContext) -> RecoveryProposal:
        """Emulate AI reasoning based on structured context."""
        time.sleep(self.latency_ms / 1000.0)

        if self.simulate_timeout:
            raise TimeoutError("Simulated Amazon Bedrock request timed out after 15.0s")

        if self.simulate_error:
            raise RuntimeError("Simulated Bedrock ServiceUnavailableException: 503 Service Unavailable")

        if self.simulate_malformed:
            # Return invalid object format to test validator
            return RecoveryProposal(
                diagnosis="unknown",
                action="INVALID_MUTATION_CMD",  # type: ignore
                parameters={"raw_command": "rm -rf /"},
                confidence=0.5,
                explanation="Malformed model response",
                reasoning_source="bedrock",
            )

        if self.simulate_invalid_action:
            return RecoveryProposal(
                diagnosis="insufficient_cpu",
                action="UNAUTHORIZED_RESTART_ALL",  # type: ignore
                parameters={},
                confidence=0.8,
                explanation="Model suggested an unauthorized action",
                reasoning_source="bedrock",
            )

        # Realistic AI reasoning logic
        diag = context.deterministic_diagnosis
        classification = str(diag.get("classification") or "unknown").lower()
        req_cpu = context.resource_requests.get("cpu_milli", 0)
        req_mem = context.resource_requests.get("memory_bytes", 0)

        # Check if malicious text was injected in events
        for evt in context.events_summary:
            if "ignore previous instructions" in evt.lower() or "system:" in evt.lower():
                logger.warning("Mock reasoner observed prompt injection pattern in events; ignoring instruction safely")

        if classification in {"insufficient_cpu", "insufficient_memory", "too_many_pods"}:
            action = ActionType.REQUEST_SCALE_UP
            # Determine appropriate pool based on memory vs compute
            if req_mem > 8 * 1024**3:
                target_pool = "memory-optimized"
            else:
                target_pool = "default"

            params = {
                "node_pool": target_pool,
                "target_nodes": 1,
                "reason": classification,
                "requested_cpu": context.resource_requests.get("raw_cpu", f"{req_cpu}m"),
                "requested_memory": context.resource_requests.get("raw_memory", f"{req_mem}B"),
                "agent_id": context.agent_id,
            }
            explanation = (
                f"AI Reasoning ({self.model_id}): Workload requires {req_cpu}m CPU / {req_mem}B RAM. "
                f"Cluster allocatable capacity is insufficient on individual worker nodes. "
                f"Recommending scale-up of pool '{target_pool}' by +1 node."
            )
            confidence = 0.96
        else:
            action = ActionType.NO_ACTION
            params = {
                "reason": classification,
                "agent_id": context.agent_id,
            }
            explanation = (
                f"AI Reasoning ({self.model_id}): Workload failure stems from constraint '{classification}'. "
                f"Infrastructure scaling will not resolve this bottleneck. Recommending operator review."
            )
            confidence = 0.90

        return RecoveryProposal(
            diagnosis=classification,
            action=action,
            parameters=params,
            confidence=confidence,
            explanation=explanation,
            reasoning_source="bedrock",
            bedrock_status="AVAILABLE",
            bedrock_error=None,
            latency_ms=self.latency_ms,
        )

