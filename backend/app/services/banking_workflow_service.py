import json

from fastapi import HTTPException
from sqlmodel import Session, select

from ..models.banking_workflow import BankingWorkflowCase
from ..models.user import User
from ..services.feature_flag_service import require_feature_enabled


ADMIN_ROLES = {"super_admin", "bank_admin", "compliance_officer"}

WORKFLOW_CONFIG = {
    "complaint_workspace": {
        "feature_key": "complaint_workspace",
        "prefix": "Complaint response draft",
    },
    "circular_impact_analyzer": {
        "feature_key": "circular_impact_analyzer",
        "prefix": "Impact summary",
    },
    "branch_response_builder": {
        "feature_key": "branch_response_builder",
        "prefix": "Response draft",
    },
    "kyc_case_prep": {
        "feature_key": "kyc_case_prep",
        "prefix": "KYC prep",
    },
    "checklist_validator": {
        "feature_key": "checklist_validator",
        "prefix": "Checklist validation",
    },
}


def _require_bank(user: User) -> int:
    if user.bank_id is None:
        raise HTTPException(status_code=400, detail="No bank selected")
    return user.bank_id


def _metadata(value: str | None) -> dict:
    if not value:
        return {}
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _response(case: BankingWorkflowCase) -> dict:
    return {
        "id": case.id,
        "bank_id": case.bank_id,
        "workflow_type": case.workflow_type,
        "title": case.title,
        "prompt": case.prompt,
        "output_summary": case.output_summary,
        "customer_reference": case.customer_reference,
        "status": case.status,
        "priority": case.priority,
        "created_by_user_id": case.created_by_user_id,
        "assigned_to_user_id": case.assigned_to_user_id,
        "metadata": _metadata(case.metadata_json),
        "created_at": case.created_at,
        "updated_at": case.updated_at,
    }


def _generate_output(workflow_type: str, title: str, prompt: str, metadata: dict) -> str:
    prefix = WORKFLOW_CONFIG[workflow_type]["prefix"]
    if workflow_type == "checklist_validator":
        missing = metadata.get("missing_items", [])
        return f"{prefix}: {len(missing)} missing item(s). Missing: {', '.join(missing) if missing else 'none'}."
    return f"{prefix}: {title}. Key facts: {prompt.strip()[:600]}"


def create_case(db: Session, *, current_user: User, workflow_type: str, payload) -> dict:
    if workflow_type not in WORKFLOW_CONFIG:
        raise HTTPException(status_code=400, detail="Unknown workflow type")
    bank_id = _require_bank(current_user)
    require_feature_enabled(db, bank_id, WORKFLOW_CONFIG[workflow_type]["feature_key"])
    if payload.assigned_to_user_id:
        assignee = db.get(User, payload.assigned_to_user_id)
        if not assignee or assignee.bank_id != bank_id:
            raise HTTPException(status_code=403, detail="Cannot assign workflow outside this bank")
    metadata = payload.metadata or {}
    output = _generate_output(workflow_type, payload.title, payload.prompt, metadata)
    case = BankingWorkflowCase(
        bank_id=bank_id,
        workflow_type=workflow_type,
        title=payload.title.strip(),
        prompt=payload.prompt.strip(),
        output_summary=output,
        customer_reference=payload.customer_reference,
        priority=payload.priority,
        created_by_user_id=current_user.id,
        assigned_to_user_id=payload.assigned_to_user_id,
        metadata_json=json.dumps(metadata),
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return _response(case)


def validate_checklist(db: Session, *, current_user: User, payload) -> dict:
    required = [item.strip() for item in payload.required_items if item.strip()]
    provided = {item.strip().casefold() for item in payload.provided_items if item.strip()}
    missing = [item for item in required if item.casefold() not in provided]
    metadata = {
        "required_items": required,
        "provided_items": payload.provided_items,
        "missing_items": missing,
    }
    case_payload = type("ChecklistCasePayload", (), {
        "title": payload.title,
        "prompt": payload.prompt or f"Validate {payload.title}",
        "customer_reference": None,
        "priority": "normal",
        "assigned_to_user_id": None,
        "metadata": metadata,
    })()
    return create_case(db, current_user=current_user, workflow_type="checklist_validator", payload=case_payload)


def list_cases(db: Session, *, current_user: User, workflow_type: str, scope: str = "mine") -> list[dict]:
    if workflow_type not in WORKFLOW_CONFIG:
        raise HTTPException(status_code=400, detail="Unknown workflow type")
    bank_id = _require_bank(current_user)
    require_feature_enabled(db, bank_id, WORKFLOW_CONFIG[workflow_type]["feature_key"])
    query = select(BankingWorkflowCase).where(BankingWorkflowCase.bank_id == bank_id, BankingWorkflowCase.workflow_type == workflow_type)
    if scope == "bank":
        if current_user.role not in ADMIN_ROLES:
            raise HTTPException(status_code=403, detail="Only admins can list bank-wide workflow cases")
    else:
        query = query.where(BankingWorkflowCase.created_by_user_id == current_user.id)
    query = query.order_by(BankingWorkflowCase.created_at.desc(), BankingWorkflowCase.id.desc())
    return [_response(case) for case in db.exec(query).all()]
