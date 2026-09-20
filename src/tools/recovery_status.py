"""MCP Tool handler: get_recovery_status."""

from typing import Any, Dict

from src.autoscaler.recovery_tracker import recovery_tracker
from src.logger.logger import get_logger

logger = get_logger("tools.recovery_status")

RECOVERY_STATUS_NAME = "get_recovery_status"
RECOVERY_STATUS_DESC = (
    "Retrieve the execution history, current state, and audit logs of Aegis agent recovery operations."
)
RECOVERY_STATUS_SCHEMA = {
    "type": "object",
    "properties": {
        "recovery_id": {
            "type": "string",
            "description": "Optional specific recovery operation identifier.",
        },
        "agent_id": {
            "type": "string",
            "description": "Optional Aegis agent UUID to query recovery history for.",
        },
    },
}


def handle_get_recovery_status(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Execute get_recovery_status tool."""
    recovery_id = arguments.get("recovery_id")
    agent_id = arguments.get("agent_id")

    if recovery_id:
        rec = recovery_tracker.get_recovery(str(recovery_id).strip())
        if rec:
            return {"found": True, "recovery": rec.to_dict()}
        return {"found": False, "recovery_id": recovery_id, "message": f"Recovery record '{recovery_id}' not found"}

    if agent_id:
        rec = recovery_tracker.get_recovery_by_agent(str(agent_id).strip())
        if rec:
            return {"found": True, "recovery": rec.to_dict()}
        return {"found": False, "agent_id": agent_id, "message": f"No recovery record found for agent '{agent_id}'"}

    all_records = recovery_tracker.list_recoveries()
    return {
        "found": True,
        "count": len(all_records),
        "recoveries": [r.to_dict() for r in all_records],
    }

