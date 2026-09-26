"""
Demo control endpoints for ReleaseShield.
Allows resetting and re-introducing the deliberate change directly from the UI or API.
"""
from fastapi import APIRouter
from pathlib import Path
from ..state import reset_state, add_audit_event, get_state, update_state
from ..models import WorkflowStatus
from ..config import settings
from ..remediation_templates import apply_reset, AFTER_MODEL
from ..git_service import get_git_state

router = APIRouter(prefix="/demo", tags=["demo"])


@router.post("/introduce-change")
async def introduce_change() -> dict:
    """Introduce the deliberate 1-file developer change to the repository."""
    repo = Path(settings.DEMO_REPO_PATH)
    model_path = repo / "backend" / "models" / "payment.py"

    # Backup if exists
    backup_path = model_path.with_suffix(".py.bak")
    if model_path.exists():
        backup_path.write_text(model_path.read_text(encoding="utf-8"), encoding="utf-8")

    model_path.write_text(AFTER_MODEL, encoding="utf-8")
    reset_state()
    update_state(status=WorkflowStatus.IDLE)

    git_state = get_git_state(str(repo))
    update_state(git_state=git_state)

    add_audit_event(
        "Demo: Deliberate change introduced — Payment.amount: Integer -> Decimal in backend/models/payment.py",
        details={"developer_changed": "backend/models/payment.py"}
    )

    return {
        "status": "change_introduced",
        "file_modified": "backend/models/payment.py",
        "description": "Payment.amount changed from Integer to Numeric(10,2)",
        "changed_files_count": len(git_state.changed_files),
    }


@router.post("/reset")
async def reset_demo() -> dict:
    """Reset the demo repository to the clean BEFORE state."""
    restored = apply_reset(settings.DEMO_REPO_PATH)
    reset_state()
    update_state(status=WorkflowStatus.IDLE)

    git_state = get_git_state(settings.DEMO_REPO_PATH)
    update_state(git_state=git_state)

    add_audit_event("Demo: Reset to clean BEFORE state (integer cents)")

    return {
        "status": "reset",
        "files_restored": len(restored),
        "is_clean": git_state.is_clean,
    }


@router.get("/state")
async def demo_state() -> dict:
    """Return the entire current workflow state."""
    return get_state().model_dump()
