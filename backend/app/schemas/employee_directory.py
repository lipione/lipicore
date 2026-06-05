from typing import Optional

from pydantic import BaseModel


class EmployeeDirectoryResult(BaseModel):
    id: int
    name: str
    email: str
    role: str
    department: Optional[str] = None
    branch: Optional[str] = None
    job_title: Optional[str] = None
    phone_extension: Optional[str] = None
    supervisor_user_id: Optional[int] = None
    expertise_tags: list[str] = []
    escalation_areas: list[str] = []
    availability_status: str = "available"
    is_active: bool
    can_message: bool
