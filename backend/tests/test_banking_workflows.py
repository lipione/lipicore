import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine, select
from sqlmodel.pool import StaticPool

from app.api import (
    audit_evidence,
    branch_responses,
    checklist_workspace,
    circular_impact,
    complaint_workspace,
    kyc_case_prep,
)
from app.core.security import create_access_token, get_password_hash
from app.db.session import get_session
from app.models.audit_evidence import AuditEvidencePack
from app.models.bank import Bank
from app.models.banking_workflow import BankingWorkflowCase
from app.models.chat import ChatMessage, ChatSession  # noqa: F401
from app.models.document import Document  # noqa: F401
from app.models.feature_flag import BankFeatureFlag  # noqa: F401
from app.models.user import User
from app.services.feature_flag_service import set_feature_flag


engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)


def get_session_override():
    with Session(engine) as session:
        yield session


test_app = FastAPI()
test_app.include_router(complaint_workspace.router, prefix="/api/complaint-workspace")
test_app.include_router(circular_impact.router, prefix="/api/circular-impact")
test_app.include_router(branch_responses.router, prefix="/api/branch-responses")
test_app.include_router(kyc_case_prep.router, prefix="/api/kyc-case-prep")
test_app.include_router(checklist_workspace.router, prefix="/api/checklist-workspace")
test_app.include_router(audit_evidence.router, prefix="/api/audit-evidence")
test_app.dependency_overrides[get_session] = get_session_override
client = TestClient(test_app)


@pytest.fixture(autouse=True)
def setup_workflow_db():
    client.cookies.clear()
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        bank = Bank(name="Workflow Bank", code="FLOW01")
        other_bank = Bank(name="Other Workflow Bank", code="OFLOW01")
        session.add(bank)
        session.add(other_bank)
        session.commit()
        session.refresh(bank)
        session.refresh(other_bank)
        users = [
            User(email="super@test.local", password_hash=get_password_hash("Password1"), name="Super Admin", role="super_admin", bank_id=bank.id, is_active=True),
            User(email="admin@test.local", password_hash=get_password_hash("Password1"), name="Bank Admin", role="bank_admin", bank_id=bank.id, is_active=True),
            User(email="staff@test.local", password_hash=get_password_hash("Password1"), name="Staff User", role="staff_user", bank_id=bank.id, is_active=True),
            User(email="other@test.local", password_hash=get_password_hash("Password1"), name="Other Staff", role="staff_user", bank_id=other_bank.id, is_active=True),
        ]
        session.add_all(users)
        session.commit()
    yield
    client.cookies.clear()
    SQLModel.metadata.drop_all(engine)


def _token(email: str) -> str:
    with Session(engine) as session:
        user = session.exec(select(User).where(User.email == email)).first()
        assert user and user.id
        return create_access_token(user.id)


def _enable(feature_key: str):
    with Session(engine) as session:
        bank = session.exec(select(Bank).where(Bank.code == "FLOW01")).first()
        admin = session.exec(select(User).where(User.email == "super@test.local")).first()
        assert bank and admin
        set_feature_flag(session, bank_id=bank.id, feature_key=feature_key, enabled=True, configured_by_user_id=admin.id)


def test_complaint_workspace_rejects_disabled_feature():
    response = client.get("/api/complaint-workspace/cases", headers={"Authorization": f"Bearer {_token('staff@test.local')}"})
    assert response.status_code == 403
    assert response.json()["detail"]["feature"] == "complaint_workspace"


def test_staff_can_create_complaint_case_and_bank_admin_can_list_bank_wide():
    _enable("complaint_workspace")
    created = client.post(
        "/api/complaint-workspace/cases",
        headers={"Authorization": f"Bearer {_token('staff@test.local')}"},
        json={"title": "ATM card complaint", "prompt": "Customer says ATM retained card.", "customer_reference": "CUST-120"},
    )
    assert created.status_code == 200
    assert "ATM card complaint" in created.json()["title"]
    assert created.json()["workflow_type"] == "complaint_workspace"
    admin_list = client.get("/api/complaint-workspace/cases?scope=bank", headers={"Authorization": f"Bearer {_token('admin@test.local')}"})
    assert len(admin_list.json()) == 1


def test_circular_impact_and_branch_response_generate_staff_ready_outputs():
    _enable("circular_impact_analyzer")
    _enable("branch_response_builder")
    circular = client.post(
        "/api/circular-impact/cases",
        headers={"Authorization": f"Bearer {_token('staff@test.local')}"},
        json={"title": "New NRB circular", "prompt": "Circular changes KYC refresh timing for high-risk customers."},
    )
    branch = client.post(
        "/api/branch-responses/cases",
        headers={"Authorization": f"Bearer {_token('staff@test.local')}"},
        json={"title": "Dormant account query", "prompt": "Customer asks how to reactivate dormant account."},
    )
    assert circular.status_code == 200
    assert "Impact summary" in circular.json()["output_summary"]
    assert branch.status_code == 200
    assert "Response draft" in branch.json()["output_summary"]


def test_kyc_case_prep_and_checklist_validation_outputs_are_structured():
    _enable("kyc_case_prep")
    _enable("checklist_validator")
    kyc = client.post(
        "/api/kyc-case-prep/cases",
        headers={"Authorization": f"Bearer {_token('staff@test.local')}"},
        json={"title": "KYC review C-009", "prompt": "Customer has expired citizenship copy and missing beneficial owner declaration."},
    )
    checklist = client.post(
        "/api/checklist-workspace/validate",
        headers={"Authorization": f"Bearer {_token('staff@test.local')}"},
        json={"title": "Loan file checklist", "required_items": ["application", "KYC", "income proof"], "provided_items": ["application", "KYC"]},
    )
    assert kyc.status_code == 200
    assert "KYC prep" in kyc.json()["output_summary"]
    assert checklist.status_code == 200
    assert checklist.json()["metadata"]["missing_items"] == ["income proof"]


def test_audit_evidence_pack_guard_and_creation():
    response = client.get("/api/audit-evidence/packs", headers={"Authorization": f"Bearer {_token('staff@test.local')}"})
    assert response.status_code == 403
    assert response.json()["detail"]["feature"] == "audit_evidence_pack"

    _enable("audit_evidence_pack")
    created = client.post(
        "/api/audit-evidence/packs",
        headers={"Authorization": f"Bearer {_token('staff@test.local')}"},
        json={"title": "Quarter end evidence", "source_type": "policy_change", "source_id": "42", "summary": "Policy change acknowledgement evidence.", "included_items": ["policy digest", "acknowledgement"]},
    )
    assert created.status_code == 200
    assert created.json()["included_items"] == ["policy digest", "acknowledgement"]
    with Session(engine) as session:
        assert session.exec(select(BankingWorkflowCase)).all() == []
        assert len(session.exec(select(AuditEvidencePack)).all()) == 1
