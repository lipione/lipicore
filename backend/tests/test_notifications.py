import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine, select
from sqlmodel.pool import StaticPool

from app.api import notifications
from app.core.security import create_access_token, get_password_hash
from app.db.session import get_session
from app.models.bank import Bank
from app.models.chat import ChatMessage, ChatSession  # noqa: F401 - registers SQLModel relationships
from app.models.document import Document  # noqa: F401 - registers SQLModel relationships
from app.models.feature_flag import BankFeatureFlag  # noqa: F401 - registers feature flag table
from app.models.notification import Notification
from app.models.user import User
from app.services.feature_flag_service import set_feature_flag


sqlite_url = "sqlite://"
engine = create_engine(
    sqlite_url,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


def get_session_override():
    with Session(engine) as session:
        yield session


test_app = FastAPI()
test_app.include_router(notifications.router, prefix="/api/notifications")
test_app.dependency_overrides[get_session] = get_session_override
client = TestClient(test_app)


@pytest.fixture(autouse=True)
def setup_notifications_db():
    client.cookies.clear()
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        bank = Bank(name="Notification Bank", code="NOTE01")
        other_bank = Bank(name="Other Notification Bank", code="ONOTE01")
        session.add(bank)
        session.add(other_bank)
        session.commit()
        session.refresh(bank)
        session.refresh(other_bank)

        users = [
            User(
                email="super@test.local",
                password_hash=get_password_hash("Password1"),
                name="Super Admin",
                role="super_admin",
                bank_id=bank.id,
                is_active=True,
            ),
            User(
                email="admin@test.local",
                password_hash=get_password_hash("Password1"),
                name="Bank Admin",
                role="bank_admin",
                department="Administration",
                bank_id=bank.id,
                is_active=True,
            ),
            User(
                email="staff@test.local",
                password_hash=get_password_hash("Password1"),
                name="Staff User",
                role="staff_user",
                department="Operations",
                bank_id=bank.id,
                is_active=True,
            ),
            User(
                email="other@test.local",
                password_hash=get_password_hash("Password1"),
                name="Other Staff",
                role="staff_user",
                department="Operations",
                bank_id=other_bank.id,
                is_active=True,
            ),
        ]
        session.add_all(users)
        session.commit()

    yield
    client.cookies.clear()
    SQLModel.metadata.drop_all(engine)


def _token(email: str) -> str:
    with Session(engine) as session:
        user = session.exec(select(User).where(User.email == email)).first()
        assert user is not None
        assert user.id is not None
        return create_access_token(user.id)


def _bank_id(code: str = "NOTE01") -> int:
    with Session(engine) as session:
        bank = session.exec(select(Bank).where(Bank.code == code)).first()
        assert bank is not None
        assert bank.id is not None
        return bank.id


def _enable_notifications(bank_code: str = "NOTE01"):
    with Session(engine) as session:
        bank_id = _bank_id(bank_code)
        admin = session.exec(select(User).where(User.email == "super@test.local")).first()
        assert admin is not None
        set_feature_flag(
            session,
            bank_id=bank_id,
            feature_key="notifications",
            enabled=True,
            configured_by_user_id=admin.id,
            reason="Notification pilot",
        )


def test_notifications_reject_disabled_feature():
    token = _token("staff@test.local")

    response = client.get(
        "/api/notifications",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "feature_disabled"
    assert response.json()["detail"]["feature"] == "notifications"


def test_bank_admin_can_create_bank_alert_for_active_users():
    _enable_notifications()
    admin_token = _token("admin@test.local")
    staff_token = _token("staff@test.local")

    created = client.post(
        "/api/notifications",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "title": "Treasury rate batch updated",
            "body": "Morning exchange rates are ready for branch use.",
            "category": "system",
            "severity": "urgent",
            "audience_type": "bank",
            "action_url": "/market-time",
        },
    )

    assert created.status_code == 200
    assert created.json()["created_count"] == 3

    inbox = client.get(
        "/api/notifications",
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    assert inbox.status_code == 200
    assert len(inbox.json()) == 1
    assert inbox.json()[0]["title"] == "Treasury rate batch updated"
    assert inbox.json()[0]["severity"] == "urgent"


def test_staff_cannot_create_notifications():
    _enable_notifications()
    token = _token("staff@test.local")

    response = client.post(
        "/api/notifications",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Unapproved alert",
            "body": "Should fail",
            "category": "system",
            "severity": "info",
            "audience_type": "bank",
        },
    )

    assert response.status_code == 403


def test_user_can_mark_notification_read_and_acknowledged():
    _enable_notifications()
    admin_token = _token("admin@test.local")
    staff_token = _token("staff@test.local")

    client.post(
        "/api/notifications",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "title": "Policy acknowledgement",
            "body": "Acknowledge updated teller procedure.",
            "category": "policy",
            "severity": "warning",
            "audience_type": "role",
            "role": "staff_user",
            "requires_acknowledgement": True,
        },
    )
    inbox = client.get("/api/notifications", headers={"Authorization": f"Bearer {staff_token}"})
    notification_id = inbox.json()[0]["id"]

    read = client.patch(
        f"/api/notifications/{notification_id}/read",
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    ack = client.patch(
        f"/api/notifications/{notification_id}/acknowledge",
        headers={"Authorization": f"Bearer {staff_token}"},
    )

    assert read.status_code == 200
    assert read.json()["read_at"] is not None
    assert ack.status_code == 200
    assert ack.json()["acknowledged_at"] is not None


def test_notifications_are_bank_scoped():
    _enable_notifications()
    _enable_notifications("ONOTE01")
    admin_token = _token("admin@test.local")
    other_token = _token("other@test.local")

    client.post(
        "/api/notifications",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "title": "Bank-only notice",
            "body": "Only primary bank should see this.",
            "category": "system",
            "severity": "info",
            "audience_type": "bank",
        },
    )
    other_inbox = client.get(
        "/api/notifications",
        headers={"Authorization": f"Bearer {other_token}"},
    )

    assert other_inbox.status_code == 200
    assert other_inbox.json() == []
    with Session(engine) as session:
        rows = session.exec(select(Notification)).all()
    assert len(rows) == 3
