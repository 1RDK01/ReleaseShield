"""POST /api/remediate — run Bob remediation."""
from fastapi import APIRouter, HTTPException
from ..state import get_state, update_state, add_audit_event
from ..models import WorkflowStatus
from ..remediation_service import run_remediation
from ..config import settings
import logging

router = APIRouter()
logger = logging.getLogger("releaseshield.routers.remediate")


@router.post("/remediate")
async def remediate() -> dict:
    state = get_state()
    if not state.impact_graph:
        raise HTTPException(status_code=400, detail="Run /api/analyze first")
    if state.status == WorkflowStatus.REMEDIATING:
        raise HTTPException(status_code=409, detail="Remediation already in progress")

    update_state(status=WorkflowStatus.REMEDIATING)
    add_audit_event("Repository synchronization started")

    try:
        result = run_remediation(
            diff=state.git_state.diff_summary if state.git_state else "",
            impact_findings=state.impact_graph.bob_reasoning,
            repo_path=settings.DEMO_REPO_PATH,
            attempt=1,
        )
        current_results = list(state.remediation_results) if state.remediation_results else []
        current_results.append(result)
        update_state(
            status=WorkflowStatus.REMEDIATED,
            remediation_results=current_results,
        )

        add_audit_event(
            f"{len(result.files_modified)} files modified by Bob",
            details={"files": [f.path for f in result.files_modified]},
        )

        return {
            "status": "remediated",
            "files_modified_count": len(result.files_modified),
            "modified_files": [f.path for f in result.files_modified],
            "success": result.success,
        }

    except Exception as e:
        logger.exception("Remediation failed")
        add_audit_event(f"Remediation failed: {e}", level="error")
        update_state(status=WorkflowStatus.FAILED, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
