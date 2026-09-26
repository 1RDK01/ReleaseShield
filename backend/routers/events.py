"""GET /api/events — return audit log and workflow state."""
from fastapi import APIRouter
from ..state import get_state, reset_state
from ..models import WorkflowState

router = APIRouter()


@router.get("/events")
async def get_events() -> dict:
    state = get_state()
    return {
        "status": state.status,
        "audit_log": [
            {
                "timestamp": e.timestamp.strftime("%H:%M:%S"),
                "level": e.level,
                "message": e.message,
                "details": e.details,
            }
            for e in state.audit_log
        ],
        "error": state.error,
    }


@router.get("/state")
async def get_full_state() -> dict:
    state = get_state()
    return {
        "status": state.status,
        "workflow_status": state.status,
        "git_state": state.git_state.model_dump() if state.git_state else None,
        "impact_summary": {
            "developer_files": len(state.git_state.changed_files) if state.git_state else 0,
            "bob_discovered": len(state.impact_graph.bob_discovered_files) if state.impact_graph else 0,
            "findings": len(state.impact_graph.findings) if state.impact_graph else 0,
        } if state.impact_graph else None,
        "impact_graph": state.impact_graph.model_dump() if state.impact_graph else None,
        "remediation_results": [r.model_dump() for r in state.remediation_results] if state.remediation_results else [],
        "verification_result": state.verification_result.model_dump() if state.verification_result else None,
        "remediation_attempts": len(state.remediation_results),
        "verification_passed": state.verification_result.all_passed if state.verification_result else None,
        "started_at": state.started_at.isoformat() if state.started_at else None,
        "error": state.error,
    }


@router.post("/reset")
async def reset() -> dict:
    reset_state()
    return {"status": "reset", "message": "Workflow state cleared"}
