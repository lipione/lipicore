import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine, select
from sqlmodel.pool import StaticPool

from app.api import ceo_messages, notifications
from app.core.security import create_access_token, get_password_hash
from app.db.session import get_session
from app.models.bank import Bank
from app.models.ceo_message import CeoMessage, CeoMessageAcknowledgement
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
test_app.include_router(ceo_messages.router, prefix="/api/ceo-messages")
test_app.include_router(notifications.router, prefix="/api/notifications")
test_app.dependency_overrides[get_session] = get_session_override
client = TestClient(test_app)


@pytest.fixture(autouse=True)
def setup_ceo_message_db():
    client.cookies.clear()
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        bank = Bank(name="CEO Bank", code="CEO01")
        session.add(bank)
        session.commit()
        session.refresh(bank)

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
                email="ops@test.local",
                password_hash=get_password_hash("Password1"),
                name="Ops Staff",
                role="staff_user",
                department="Operations",
                bank_id=bank.id,
                is_active=True,
            ),
            User(
                email="compliance@test.local",
                password_hash=get_password_hash("Password1"),
                name="Compliance Staff",
                role="compliance_officer",
                department="Compliance",
                bank_id=bank.id,
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


def _bank_id() -> int:
    with Session(engine) as session:
        bank = session.exec(select(Bank).where(Bank.code == "CEO01")).first()
        assert bank is not None
        assert bank.id is not None
        return bank.id


def _enable(feature_key: str):
    with Session(engine) as session:
        bank_id = _bank_id()
        admin = session.exec(select(User).where(User.email == "super@test.local")).first()
        assert admin is not None
        set_feature_flag(
            session,
            bank_id=bank_id,
            feature_key=feature_key,
            enabled=True,
            configured_by_user_id=admin.id,
            reason="CEO message pilot",
        )


def test_ceo_messages_reject_disabled_feature():
    token = _token("ops@test.local")

    response = client.get(
        "/api/ceo-messages",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "feature_disabled"
    assert response.json()["detail"]["feature"] == "ceo_messages"


def test_bank_admin_can_publish_and_staff_can_acknowledge_ceo_message():
    _enable("ceo_messages")
    admin_token = _token("admin@test.local")
    staff_token = _token("ops@test.local")

    published = client.post(
        "/api/ceo-messages",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "title": "Service excellence week",
            "body": "Focus on fast, verified customer responses.",
            "audience_type": "bank",
            "priority": "important",
            "requires_acknowledgement": True,
        },
    )
    assert published.status_code == 200
    assert published.json()["title"] == "Service excellence week"

    inbox = client.get("/api/ceo-messages", headers={"Authorization": f"Bearer {staff_token}"})
    assert inbox.status_code == 200
    assert len(inbox.json()) == 1
    assert inbox.json()[0]["acknowledged_at"] is None

    ack = client.patch(
        f"/api/ceo-messages/{published.json()['id']}/acknowledge",
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    assert ack.status_code == 200
    assert ack.json()["acknowledged_at"] is not None


def test_staff_cannot_publish_ceo_message():
    _enable("ceo_messages")
    token = _token("ops@test.local")

    response = client.post(
        "/api/ceo-messages",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Unapproved",
            "body": "Should fail",
            "audience_type": "bank",
        },
    )

    assert response.status_code == 403


def test_ceo_message_role_audience_filters_recipients():
    _enable("ceo_messages")
    admin_token = _token("admin@test.local")
    ops_token = _token("ops@test.local")
    compliance_token = _token("compliance@test.local")

    client.post(
        "/api/ceo-messages",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "title": "Compliance message",
            "body": "Compliance officers only.",
            "audience_type": "role",
            "role": "compliance_officer",
        },
    )

    ops = client.get("/api/ceo-messages", headers={"Authorization": f"Bearer {ops_token}"})
    compliance = client.get("/api/ceo-messages", headers={"Authorization": f"Bearer {compliance_token}"})
    assert ops.status_code == 200
    assert ops.json() == []
    assert len(compliance.json()) == 1


def test_ceo_message_creates_notifications_when_enabled():
    _enable("ceo_messages")
    _enable("notifications")
    admin_token = _token("admin@test.local")
    staff_token = _token("ops@test.local")

    response = client.post(
        "/api/ceo-messages",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "title": "Quarter-end readiness",
            "body": "Complete customer-facing pending work today.",
            "audience_type": "bank",
            "priority": "urgent",
            "requires_acknowledgement": True,
            "notify": True,
        },
    )
    assert response.status_code == 200

    staff_notifications = client.get("/api/notifications", headers={"Authorization": f"Bearer {staff_token}"})
    assert staff_notifications.status_code == 200
    assert len(staff_notifications.json()) == 1
    assert staff_notifications.json()[0]["category"] == "ceo_message"
    assert staff_notifications.json()[0]["requires_acknowledgement"] is True

    with Session(engine) as session:
        messages = session.exec(select(CeoMessage)).all()
        acknowledgements = session.exec(select(CeoMessageAcknowledgement)).all()
        notifications_rows = session.exec(select(Notification)).all()
    assert len(messages) == 1
    assert acknowledgements == []
    assert len(notifications_rows) == 4
