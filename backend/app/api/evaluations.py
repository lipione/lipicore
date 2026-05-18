from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from ..api.deps import get_current_analytics_user
from ..db.session import get_session
from ..models.user import User
from ..schemas.rag_evaluation import RagEvaluationRequest, RagEvaluationResponse
from ..services.rag_evaluation_service import evaluate_rag_cases

router = APIRouter()


@router.post("/rag", response_model=RagEvaluationResponse)
def run_rag_evaluation(
    request: RagEvaluationRequest,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_analytics_user),
) -> Any:
    bank_id = request.bank_id or current_user.bank_id
    if bank_id is None:
        raise HTTPException(status_code=400, detail="No bank selected for evaluation")
    if current_user.role != "super_admin" and bank_id != current_user.bank_id:
        raise HTTPException(status_code=403, detail="Cannot evaluate another bank")

    return evaluate_rag_cases(
        cases=request.cases,
        db=db,
        bank_id=bank_id,
        user_role=request.user_role,
        pass_threshold=request.pass_threshold,
    )
