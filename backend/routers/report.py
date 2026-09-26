"""GET /api/report — return release evidence."""
from fastapi import APIRouter
from ..state import get_state
from ..models import ReleaseMetrics
from ..evidence import compute_metrics, generate_all_artifacts
from ..config import settings

router = APIRouter()


@router.get("/report")
async def get_report() -> dict:
    state = get_state()
    metrics = compute_metrics(state)
    artifacts = generate_all_artifacts(state)
    return {
        "metrics": metrics.model_dump(),
        "workflow_status": state.status,
        "artifacts": artifacts,
    }
