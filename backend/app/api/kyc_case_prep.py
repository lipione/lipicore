from fastapi import APIRouter, Depends
from sqlmodel import Session

from ..db.session import get_session
from ..models.user import User
from ..schemas.banking_workflow import BankingWorkflowCaseCreate, BankingWorkflowCaseResponse
from ..services.banking_workflow_service import create_case, list_cases
from .deps import get_current_user

router = APIRouter()
WORKFLOW_TYPE = "kyc_case_prep"


@router.get("/cases", response_model=list[BankingWorkflowCaseResponse])
def read_cases(scope: str = "mine", db: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    return list_cases(db, current_user=current_user, workflow_type=WORKFLOW_TYPE, scope=scope)


@router.post("/cases", response_model=BankingWorkflowCaseResponse)
def create_kyc_case(payload: BankingWorkflowCaseCreate, db: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    return create_case(db, current_user=current_user, workflow_type=WORKFLOW_TYPE, payload=payload)
