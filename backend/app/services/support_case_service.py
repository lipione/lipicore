from sqlmodel import Session

from ..models.support_case import SupportCase
from ..schemas.support_case import SupportCaseCreate
from .workflow_utils import encode_json, extract_source_document_ids, touch


def create_support_case(
    db: Session,
    *,
    bank_id: int,
    created_by: int,
    data: SupportCaseCreate,
) -> SupportCase:
    record = SupportCase(
        bank_id=bank_id,
        created_by=created_by,
        assigned_to=data.assigned_to,
        category=data.category,
        channel=data.channel,
        priority=data.priority,
        customer_issue=data.customer_issue,
        escalation_target=data.escalation_target,
        staff_review_required=True,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def save_support_case_draft(
    db: Session,
    *,
    case_id: int,
    generated_by: int,
    draft_response: str,
    sources: list[dict] | None = None,
) -> SupportCase:
    record = db.get(SupportCase, case_id)
    if record is None:
        raise ValueError("Support case not found")

    record.draft_response = draft_response
    record.status = "draft_ready"
    record.staff_review_required = True
    record.source_document_ids_json = encode_json(extract_source_document_ids(sources))
    record.answer_metadata_json = encode_json({
        "generated_by": generated_by,
        "staff_review_required": True,
        "source_count": len(sources or []),
        "allowed_use": "staff_assistance_only",
    })
    touch(record)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record
