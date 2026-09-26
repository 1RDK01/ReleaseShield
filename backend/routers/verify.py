"""POST /api/verify — run verification suite with self-healing loop."""
from fastapi import APIRouter, HTTPException
from ..state import get_state, update_state, add_audit_event
from ..models import WorkflowStatus
from ..verification import run_full_verification, get_failure_summary
from ..remediation_service import run_repair_attempt
from ..config import settings
import logging

router = APIRouter()
logger = logging.getLogger("releaseshield.routers.verify")


@router.post("/verify")
async def verify() -> dict:
    state = get_state()

    update_state(status=WorkflowStatus.VERIFYING)
    add_audit_event("Verification started")

    try:
        repo_path = settings.DEMO_REPO_PATH
        attempt = 1
        result = run_full_verification(repo_path, attempt=attempt)

        # Self-healing loop
        while not result.all_passed and attempt <= settings.MAX_REPAIR_ATTEMPTS:
            failure_summary = get_failure_summary(result)
            add_audit_event(
                f"Verification failed (attempt {attempt}) — running Bob repair",
                level="warning",
                details={"failures": [c.label for c in result.commands if not c.passed]},
            )
            repair = run_repair_attempt(failure_summary, repo_path, attempt)
            fresh_state = get_state()
            current_results = list(fresh_state.remediation_results) if fresh_state.remediation_results else []
            current_results.append(repair)
            update_state(remediation_results=current_results)

            attempt += 1
            result = run_full_verification(repo_path, attempt=attempt)

        update_state(
            status=WorkflowStatus.VERIFIED if result.all_passed else WorkflowStatus.FAILED,
            verification_result=result,
        )

        passed = sum(1 for c in result.commands if c.passed)
        total = len(result.commands)
        add_audit_event(
            f"Verification {'passed' if result.all_passed else 'failed'}: {passed}/{total} checks",
            level="info" if result.all_passed else "error",
        )

        return {
            "status": "verified" if result.all_passed else "failed",
            "all_passed": result.all_passed,
            "checks_passed": passed,
            "checks_total": total,
            "attempts": attempt,
        }

    except Exception as e:
        logger.exception("Verification error")
        add_audit_event(f"Verification error: {e}", level="error")
        update_state(status=WorkflowStatus.FAILED, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
