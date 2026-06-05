import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine, select
from sqlmodel.pool import StaticPool

from app.api import staff_work_items
from app.core.security import create_access_token, get_password_hash
from app.db.session import get_session
from app.models.bank import Bank
from app.models.chat import ChatMessage, ChatSession  # noqa: F401
from app.models.document import Document  # noqa: F401
from app.models.feature_flag import BankFeatureFlag  # noqa: F401
from app.models.staff_work_item import StaffWorkItem
from app.models.user import User
from app.services.feature_flag_service import set_feature_flag


engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)


def get_session_override():
    with Session(engine) as session:
        yield session


test_app = FastAPI()
test_app.include_router(staff_work_items.router, prefix="/api/staff-work-items")
test_app.dependency_overrides[get_session] = get_session_override
client = TestClient(test_app)


@pytest.fixture(autouse=True)
def setup_staff_work_items_db():
    client.cookies.clear()
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        bank = Bank(name="Inbox Bank", code="INBOX01")
        other_bank = Bank(name="Other Inbox Bank", code="OINBOX01")
        session.add(bank)
        session.add(other_bank)
        session.commit()
        session.refresh(bank)
        session.refresh(other_bank)

        users = [
            User(email="super@test.local", password_hash=get_password_hash("Password1"), name="Super Admin", role="super_admin", bank_id=bank.id, is_active=True),
            User(email="admin@test.local", password_hash=get_password_hash("Password1"), name="Bank Admin", role="bank_admin", bank_id=bank.id, is_active=True),
            User(email="staff@test.local", password_hash=get_password_hash("Password1"), name="Staff User", role="staff_user", bank_id=bank.id, is_active=True),
            User(email="other-staff@test.local", password_hash=get_password_hash("Password1"), name="Other Staff", role="staff_user", bank_id=bank.id, is_active=True),
            User(email="external@test.local", password_hash=get_password_hash("Password1"), name="External Staff", role="staff_user", bank_id=other_bank.id, is_active=True),
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


def _user_id(email: str) -> int:
    with Session(engine) as session:
        user = session.exec(select(User).where(User.email == email)).first()
        assert user and user.id
        return user.id


def _enable_staff_inbox():
    with Session(engine) as session:
        admin = session.exec(select(User).where(User.email == "super@test.local")).first()
        bank = session.exec(select(Bank).where(Bank.code == "INBOX01")).first()
        assert admin and bank
        set_feature_flag(session, bank_id=bank.id, feature_key="staff_inbox", enabled=True, configured_by_user_id=admin.id)


def test_staff_work_items_reject_disabled_feature():
    response = client.get("/api/staff-work-items", headers={"Authorization": f"Bearer {_token('staff@test.local')}"})
    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "feature_disabled"
    assert response.json()["detail"]["feature"] == "staff_inbox"


def test_bank_admin_creates_work_item_for_staff_and_staff_lists_assigned_item():
    _enable_staff_inbox()
    admin_token = _token("admin@test.local")
    staff_id = _user_id("staff@test.local")

    created = client.post(
        "/api/staff-work-items",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "assigned_to_user_id": staff_id,
            "source_type": "policy_change",
            "source_id": "17",
            "title": "Review circular impact",
            "description": "Check operations impact by EOD.",
            "priority": "high",
            "due_at": "2026-06-03T10:00:00",
        },
    )
    assert created.status_code == 200
    assert created.json()["assigned_to_user_id"] == staff_id

    inbox = client.get("/api/staff-work-items", headers={"Authorization": f"Bearer {_token('staff@test.local')}"})
    assert inbox.status_code == 200
    assert [item["title"] for item in inbox.json()] == ["Review circular impact"]


def test_staff_cannot_see_other_users_work_items():
    _enable_staff_inbox()
    admin_token = _token("admin@test.local")
    other_staff_id = _user_id("other-staff@test.local")
    client.post(
        "/api/staff-work-items",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"assigned_to_user_id": other_staff_id, "title": "Other task", "priority": "normal"},
    )

    response = client.get("/api/staff-work-items", headers={"Authorization": f"Bearer {_token('staff@test.local')}"})
    assert response.status_code == 200
    assert response.json() == []


def test_bank_admin_can_list_bank_wide_items_and_filter_status():
    _enable_staff_inbox()
    admin_token = _token("admin@test.local")
    staff_id = _user_id("staff@test.local")
    created = client.post(
        "/api/staff-work-items",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"assigned_to_user_id": staff_id, "title": "Complete checklist", "priority": "urgent"},
    )
    item_id = created.json()["id"]
    client.patch(
        f"/api/staff-work-items/{item_id}",
        headers={"Authorization": f"Bearer {_token('staff@test.local')}"},
        json={"status": "completed"},
    )

    all_items = client.get("/api/staff-work-items?scope=bank", headers={"Authorization": f"Bearer {admin_token}"})
    completed = client.get("/api/staff-work-items?scope=bank&status=completed", headers={"Authorization": f"Bearer {admin_token}"})
    assert all_items.status_code == 200
    assert len(all_items.json()) == 1
    assert completed.status_code == 200
    assert completed.json()[0]["status"] == "completed"


def test_users_cannot_assign_work_item_to_another_bank():
    _enable_staff_inbox()
    response = client.post(
        "/api/staff-work-items",
        headers={"Authorization": f"Bearer {_token('admin@test.local')}"},
        json={"assigned_to_user_id": _user_id("external@test.local"), "title": "Invalid task"},
    )
    assert response.status_code == 403

    with Session(engine) as session:
        assert session.exec(select(StaffWorkItem)).all() == []
