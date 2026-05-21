from fastapi import APIRouter, Depends

from ..api.deps import get_current_analytics_user
from ..models.user import User
from ..services.llm_gateway import model_registry_snapshot, model_status
from ..services.model_benchmark_service import (
    build_candidate_snapshot,
    latest_benchmark_summary,
    load_candidate_matrix,
)

router = APIRouter()


@router.get("/candidates")
def read_candidates(current_user: User = Depends(get_current_analytics_user)) -> dict:
    matrix = load_candidate_matrix()
    return build_candidate_snapshot(matrix)


@router.get("/benchmarks/latest")
def read_latest_benchmark(current_user: User = Depends(get_current_analytics_user)) -> dict:
    return latest_benchmark_summary()


@router.get("/status")
async def read_model_lab_status(current_user: User = Depends(get_current_analytics_user)) -> dict:
    return {
        "registry": model_registry_snapshot(),
        "models": await model_status(),
        "latest_benchmark": latest_benchmark_summary(),
    }
