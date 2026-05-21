from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ComplianceReviewCreate(BaseModel):
    title: str
    circular_document_id: Optional[int] = None
    affected_departments: list[str] = []
    assigned_to: Optional[int] = None


class ComplianceReviewSummaryUpdate(BaseModel):
    impact_summary: str
    obligations: list[dict] = []
    sources: list[dict] = []


class ComplianceReviewResponse(BaseModel):
    id: int
    bank_id: int
    created_by: int
    assigned_to: Optional[int] = None
    title: str
    circular_document_id: Optional[int] = None
    status: str
    approval_status: str
    affected_departments_json: str
    impact_summary: Optional[str] = None
    obligations_json: str
    source_document_ids_json: str
    reviewer_notes: Optional[str] = None
    disclaimer: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
