from sqlmodel import Session

from ..models.loan_support import LoanSupportCase
from ..schemas.loan_support import LoanSupportCreate
from .workflow_utils import encode_json, extract_source_document_ids, touch


def _missing_documents(required: list[str], received: list[str]) -> list[str]:
    received_normalized = {item.strip().lower() for item in received}
    return [item for item in required if item.strip().lower() not in received_normalized]


def create_loan_support_case(
    db: Session,
    *,
    bank_id: int,
    created_by: int,
    data: LoanSupportCreate,
) -> LoanSupportCase:
    missing = _missing_documents(data.required_documents, data.received_documents)
    record = LoanSupportCase(
        bank_id=bank_id,
        created_by=created_by,
        assigned_to=data.assigned_to,
        applicant_name=data.applicant_name,
        loan_type=data.loan_type,
        requested_amount=data.requested_amount,
        required_documents_json=encode_json(data.required_documents),
        received_documents_json=encode_json(data.received_documents),
        missing_documents_json=encode_json(missing),
        human_review_required=True,
        automated_decision=None,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def save_credit_memo_draft(
    db: Session,
    *,
    loan_id: int,
    generated_by: int,
    memo_draft: str,
    risk_factors: list[str] | None = None,
    sources: list[dict] | None = None,
) -> LoanSupportCase:
    record = db.get(LoanSupportCase, loan_id)
    if record is None:
        raise ValueError("Loan support case not found")

    record.credit_memo_draft = memo_draft
    record.risk_factors_json = encode_json(risk_factors or [])
    record.source_document_ids_json = encode_json(extract_source_document_ids(sources))
    record.status = "memo_draft_ready"
    record.human_review_required = True
    record.automated_decision = None
    touch(record)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record
