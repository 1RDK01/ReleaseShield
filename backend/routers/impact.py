"""GET /api/impact — return the current impact graph."""
from fastapi import APIRouter, HTTPException
from ..state import get_state
from ..models import ImpactGraph

router = APIRouter()


@router.get("/impact", response_model=ImpactGraph)
async def get_impact() -> ImpactGraph:
    state = get_state()
    if not state.impact_graph:
        raise HTTPException(status_code=404, detail="No impact analysis available — run /api/analyze first")
    return state.impact_graph
