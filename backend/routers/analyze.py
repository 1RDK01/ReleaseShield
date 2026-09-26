"""POST /api/analyze — capture git diff and run Bob impact analysis."""
from fastapi import APIRouter, HTTPException
from ..models import WorkflowStatus
from ..state import get_state, update_state, add_audit_event
from ..git_service import get_git_state, verify_repo_exists
from ..bob_runner import run_bob_impact_analysis
from ..impact_service import build_impact_graph
from ..config import settings
from datetime import datetime
import logging

router = APIRouter()
logger = logging.getLogger("releaseshield.routers.analyze")


@router.post("/analyze")
async def analyze() -> dict:
    """Analyze current Git diff using IBM Bob."""
    state = get_state()
    if state.status in (WorkflowStatus.ANALYZING, WorkflowStatus.REMEDIATING, WorkflowStatus.VERIFYING):
        raise HTTPException(status_code=409, detail="Analysis already in progress")

    repo_path = settings.DEMO_REPO_PATH
    if not verify_repo_exists(repo_path):
        raise HTTPException(status_code=404, detail=f"Demo repo not found at {repo_path}")

    update_state(status=WorkflowStatus.ANALYZING, started_at=datetime.utcnow(), error=None)
    add_audit_event("Change detected — analysis started")

    try:
        # Capture Git state
        add_audit_event("Capturing Git diff")
        git_state = get_git_state(repo_path)
        update_state(git_state=git_state)

        if git_state.is_clean:
            add_audit_event("Repository is clean — no changes to analyze", level="warning")
            update_state(status=WorkflowStatus.ANALYZED)
            return {"status": "no_changes", "message": "No changes detected in repository"}

        add_audit_event(
            f"Git diff captured: {len(git_state.changed_files)} developer-changed file(s)",
            details={"files": [f.path for f in git_state.changed_files]},
        )

        # Run Bob impact analysis
        add_audit_event("IBM Bob impact analysis started")
        success, bob_output = run_bob_impact_analysis(
            diff=git_state.diff_summary,
            changed_files=[f.path for f in git_state.changed_files],
            workspace=repo_path,
        )
        add_audit_event(f"IBM Bob analysis complete (success={success})")

        # Build structured impact graph
        impact_graph = build_impact_graph(
            bob_output=bob_output,
            diff=git_state.diff_summary,
            developer_changed_files=[f.path for f in git_state.changed_files],
        )
        update_state(impact_graph=impact_graph)

        n_discovered = len(impact_graph.bob_discovered_files)
        add_audit_event(
            f"{n_discovered} additional affected files identified by Bob",
            details={"files": [f.path for f in impact_graph.bob_discovered_files]},
        )

        update_state(status=WorkflowStatus.ANALYZED)
        return {
            "status": "analyzed",
            "developer_changed_files": len(git_state.changed_files),
            "bob_discovered_files": n_discovered,
            "findings": len(impact_graph.findings),
        }

    except Exception as e:
        logger.exception("Analysis failed")
        add_audit_event(f"Analysis failed: {e}", level="error")
        update_state(status=WorkflowStatus.FAILED, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
