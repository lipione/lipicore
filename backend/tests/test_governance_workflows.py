import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine, select
from sqlmodel.pool import StaticPool

from app.api import knowledge_gaps, policy_changes
from app.core.security import create_access_token, get_password_hash
from app.db.session import get_session
from app.models.bank import Bank
from app.models.chat import ChatMessage, ChatSession  # noqa: F401
from app.models.document import Document  # noqa: F401
from app.models.feature_flag import BankFeatureFlag  # noqa: F401
from app.models.knowledge_gap import KnowledgeGap
from app.models.policy_change import PolicyChange, PolicyChangeAcknowledgement
from app.models.staff_work_item import StaffWorkItem  # noqa: F401
from app.models.user import User
from app.services.feature_flag_service import set_feature_flag


engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)


def get_session_override():
    with Session(engine) as session:
        yield session


test_app = FastAPI()
test_app.include_router(knowledge_gaps.router, prefix="/api/knowledge-gaps")
test_app.include_router(policy_changes.router, prefix="/api/policy-changes")
test_app.dependency_overrides[get_session] = get_session_override
client = TestClient(test_app)


@pytest.fixture(autouse=True)
def setup_governance_db():
    client.cookies.clear()
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        bank = Bank(name="Governance Bank", code="GOV01")
        other_bank = Bank(name="Other Governance Bank", code="OGOV01")
        session.add(bank)
        session.add(other_bank)
        session.commit()
        session.refresh(bank)
        session.refresh(other_bank)
        users = [
            User(email="super@test.local", password_hash=get_password_hash("Password1"), name="Super Admin", role="super_admin", bank_id=bank.id, is_active=True),
            User(email="admin@test.local", password_hash=get_password_hash("Password1"), name="Bank Admin", role="bank_admin", department="Administration", bank_id=bank.id, is_active=True),
            User(email="ops@test.local", password_hash=get_password_hash("Password1"), name="Ops Staff", role="staff_user", department="Operations", bank_id=bank.id, is_active=True),
            User(email="compliance@test.local", password_hash=get_password_hash("Password1"), name="Compliance Staff", role="compliance_officer", department="Compliance", bank_id=bank.id, is_active=True),
            User(email="other@test.local", password_hash=get_password_hash("Password1"), name="Other Bank Staff", role="staff_user", department="Operations", bank_id=other_bank.id, is_active=True),
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
        bank = session.exec(select(Bank).where(Bank.code == "GOV01")).first()
        admin = session.exec(select(User).where(User.email == "super@test.local")).first()
        assert bank and admin
        set_feature_flag(session, bank_id=bank.id, feature_key=feature_key, enabled=True, configured_by_user_id=admin.id)


def test_knowledge_gaps_reject_disabled_feature():
    response = client.get("/api/knowledge-gaps", headers={"Authorization": f"Bearer {_token('ops@test.local')}"})
    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "feature_disabled"
    assert response.json()["detail"]["feature"] == "knowledge_gaps"


def test_staff_can_create_knowledge_gap_and_admin_can_resolve_it():
    _enable("knowledge_gaps")
    created = client.post(
        "/api/knowledge-gaps",
        headers={"Authorization": f"Bearer {_token('ops@test.local')}"},
        json={"question": "Where is the updated cash vault SOP?", "priority": "high", "source_type": "chat"},
    )
    assert created.status_code == 200
    assert created.json()["status"] == "open"

    admin_list = client.get("/api/knowledge-gaps?scope=bank", headers={"Authorization": f"Bearer {_token('admin@test.local')}"})
    assert admin_list.status_code == 200
    assert len(admin_list.json()) == 1

    resolved = client.patch(
        f"/api/knowledge-gaps/{created.json()['id']}",
        headers={"Authorization": f"Bearer {_token('admin@test.local')}"},
        json={"status": "resolved", "resolution_notes": "Added new SOP to document library."},
    )
    assert resolved.status_code == 200
    assert resolved.json()["status"] == "resolved"
    assert resolved.json()["resolution_notes"] == "Added new SOP to document library."


def test_policy_changes_reject_disabled_feature():
    response = client.get("/api/policy-changes", headers={"Authorization": f"Bearer {_token('ops@test.local')}"})
    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "feature_disabled"
    assert response.json()["detail"]["feature"] == "policy_changes"


def test_bank_admin_publishes_policy_change_and_department_staff_can_acknowledge():
    _enable("policy_changes")
    admin_token = _token("admin@test.local")
    ops_token = _token("ops@test.local")
    compliance_token = _token("compliance@test.local")

    created = client.post(
        "/api/policy-changes",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "title": "Updated branch cash procedure",
            "summary": "Cash vault dual-control timing changed.",
            "impact_summary": "Operations teams must update branch opening checklist.",
            "affected_departments": ["Operations"],
            "action_items": ["Review new checklist", "Acknowledge change"],
            "create_work_items": False,
        },
    )
    assert created.status_code == 200

    ops = client.get("/api/policy-changes", headers={"Authorization": f"Bearer {ops_token}"})
    compliance = client.get("/api/policy-changes", headers={"Authorization": f"Bearer {compliance_token}"})
    assert len(ops.json()) == 1
    assert compliance.json() == []

    ack = client.patch(
        f"/api/policy-changes/{created.json()['id']}/acknowledge",
        headers={"Authorization": f"Bearer {ops_token}"},
    )
    assert ack.status_code == 200
    assert ack.json()["acknowledged_at"] is not None


def test_policy_change_can_create_staff_work_items_when_inbox_enabled():
    _enable("policy_changes")
    _enable("staff_inbox")
    created = client.post(
        "/api/policy-changes",
        headers={"Authorization": f"Bearer {_token('admin@test.local')}"},
        json={
            "title": "Compliance impact review",
            "summary": "New compliance circular.",
            "impact_summary": "Compliance must review customer notice templates.",
            "affected_departments": ["Compliance"],
            "action_items": ["Prepare digest"],
            "create_work_items": True,
        },
    )
    assert created.status_code == 200
    with Session(engine) as session:
        changes = session.exec(select(PolicyChange)).all()
        acks = session.exec(select(PolicyChangeAcknowledgement)).all()
        gaps = session.exec(select(KnowledgeGap)).all()
        work_items = session.exec(select(StaffWorkItem)).all()
    assert len(changes) == 1
    assert acks == []
    assert gaps == []
    assert len(work_items) == 1
    assert work_items[0].source_type == "policy_change"
