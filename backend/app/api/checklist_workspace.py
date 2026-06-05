from fastapi import APIRouter, Depends
from sqlmodel import Session

from ..db.session import get_session
from ..models.user import User
from ..schemas.banking_workflow import BankingWorkflowCaseResponse, ChecklistValidationCreate
from ..services.banking_workflow_service import list_cases, validate_checklist
from .deps import get_current_user

router = APIRouter()
WORKFLOW_TYPE = "checklist_validator"


@router.get("/cases", response_model=list[BankingWorkflowCaseResponse])
def read_cases(scope: str = "mine", db: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    return list_cases(db, current_user=current_user, workflow_type=WORKFLOW_TYPE, scope=scope)


@router.post("/validate", response_model=BankingWorkflowCaseResponse)
def validate_file_checklist(payload: ChecklistValidationCreate, db: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    return validate_checklist(db, current_user=current_user, payload=payload)
