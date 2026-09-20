"""In-memory recovery state and audit tracker for Aegis Sentinel."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

from src.autoscaler.models import RecoveryRecord, RecoveryState


class RecoveryTracker:
    """Tracks end-to-end recovery lifecycles for Aegis agents."""

    def __init__(self) -> None:
        self._records: Dict[str, RecoveryRecord] = {}
        self._agent_to_recovery: Dict[str, str] = {}

    def start_recovery(
        self,
        agent_id: str,
        pod_name: Optional[str] = None,
        diagnosis_reason: Optional[str] = None,
    ) -> RecoveryRecord:
        """Create and register a new recovery lifecycle record."""
        rec_id = f"rec-{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc).isoformat()
        record = RecoveryRecord(
            recovery_id=rec_id,
            agent_id=agent_id,
            pod_name=pod_name,
            initial_state="DETECTED",
            current_state=RecoveryState.DETECTED,
            diagnosis_reason=diagnosis_reason,
            created_at=now,
            updated_at=now,
            history=[{"state": RecoveryState.DETECTED.value, "timestamp": now}],
        )
        self._records[rec_id] = record
        self._agent_to_recovery[agent_id] = rec_id
        return record

    def get_recovery(self, recovery_id: str) -> Optional[RecoveryRecord]:
        """Retrieve recovery record by recovery_id."""
        return self._records.get(recovery_id)

    def get_recovery_by_agent(self, agent_id: str) -> Optional[RecoveryRecord]:
        """Retrieve latest recovery record for an agent."""
        rec_id = self._agent_to_recovery.get(agent_id)
        if rec_id:
            return self._records.get(rec_id)
        return None

    def update_state(
        self,
        recovery_id: str,
        new_state: RecoveryState,
        detail: Optional[str] = None,
    ) -> Optional[RecoveryRecord]:
        """Update recovery record state."""
        record = self._records.get(recovery_id)
        if record:
            record.transition_to(new_state, detail=detail)
        return record

    def list_recoveries(self) -> List[RecoveryRecord]:
        """List all recovery records ordered by creation timestamp."""
        return sorted(self._records.values(), key=lambda r: r.created_at, reverse=True)

    def clear(self) -> None:
        """Reset all recovery records."""
        self._records.clear()
        self._agent_to_recovery.clear()


# Global singleton instance for runtime tracking
recovery_tracker = RecoveryTracker()

