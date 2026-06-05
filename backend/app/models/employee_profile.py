from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class EmployeeProfile(SQLModel, table=True):
    __tablename__ = "employeeprofile"

    id: Optional[int] = Field(default=None, primary_key=True)
    bank_id: int = Field(foreign_key="bank.id", index=True)
    user_id: int = Field(foreign_key="user.id", unique=True, index=True)
    branch: Optional[str] = Field(default=None, index=True)
    job_title: Optional[str] = Field(default=None, index=True)
    phone_extension: Optional[str] = None
    supervisor_user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    expertise_tags_json: str = Field(default="[]")
    escalation_areas_json: str = Field(default="[]")
    availability_status: str = Field(default="available")
    public_notes: Optional[str] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)
