from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class BankingWorkflowCaseCreate(BaseModel):
    title: str
    prompt: str
    customer_reference: Optional[str] = None
    priority: str = "normal"
    assigned_to_user_id: Optional[int] = None
    metadata: dict[str, Any] = {}


class ChecklistValidationCreate(BaseModel):
    title: str
    required_items: list[str]
    provided_items: list[str]
    prompt: str = ""


class BankingWorkflowCaseResponse(BaseModel):
    id: int
    bank_id: int
    workflow_type: str
    title: str
    prompt: str
    output_summary: str
    customer_reference: Optional[str] = None
    status: str
    priority: str
    created_by_user_id: Optional[int] = None
    assigned_to_user_id: Optional[int] = None
    metadata: dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime
