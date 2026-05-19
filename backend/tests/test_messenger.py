import os

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, select
from sqlmodel import create_engine
from sqlmodel.pool import StaticPool

from app.api import messenger
from app.core.security import get_password_hash
from app.core.security import create_access_token
from app.db.session import get_session
from app.models.bank import Bank
from app.models.chat import ChatSession
from app.models.document import Document
from app.models.messenger import MessengerAuditEvent
from app.models.user import User


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
test_app.include_router(messenger.router, prefix="/api/messenger")
test_app.dependency_overrides[get_session] = get_session_override
client = TestClient(test_app)


@pytest.fixture(autouse=True)
def setup_messenger_db(tmp_path, monkeypatch):
    client.cookies.clear()
    monkeypatch.setenv("MESSENGER_UPLOAD_DIR", str(tmp_path / "messenger_uploads"))
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        bank = Bank(name="Test Bank", code="TEST01")
        other_bank = Bank(name="Other Bank", code="OTHER")
        session.add(bank)
        session.add(other_bank)
        session.commit()
        session.refresh(bank)
        session.refresh(other_bank)

        users = [
            User(
                email="ops@test.local",
                password_hash=get_password_hash("password"),
                name="Ops Staff",
                role="staff_user",
                department="Operations",
                bank_id=bank.id,
                is_active=True,
            ),
            User(
                email="credit@test.local",
                password_hash=get_password_hash("password"),
                name="Credit Staff",
                role="staff_user",
                department="Credit",
                bank_id=bank.id,
                is_active=True,
            ),
            User(
                email="admin@test.local",
                password_hash=get_password_hash("password"),
                name="Bank Admin",
                role="bank_admin",
                department="Operations",
                bank_id=bank.id,
                is_active=True,
            ),
            User(
                email="other@test.local",
                password_hash=get_password_hash("password"),
                name="Other Bank Staff",
                role="staff_user",
                department="Operations",
                bank_id=other_bank.id,
                is_active=True,
            ),
        ]
        for user in users:
            session.add(user)
        session.commit()

    yield
    client.cookies.clear()
    SQLModel.metadata.drop_all(engine)


def user_id(email: str) -> int:
    with Session(engine) as session:
        user = session.exec(select(User).where(User.email == email)).first()
        assert user is not None
        assert user.id is not None
        return user.id


def get_token(email: str) -> str:
    with Session(engine) as session:
        user = session.exec(select(User).where(User.email == email)).first()
        assert user is not None
        assert user.id is not None
        return create_access_token(user.id)


def create_direct_conversation(token: str, recipient_id: int) -> int:
    response = client.post(
        "/api/messenger/conversations/direct",
        headers={"Authorization": f"Bearer {token}"},
        json={"recipient_id": recipient_id},
    )
    assert response.status_code == 200
    return response.json()["id"]


def test_messenger_staff_can_bootstrap_with_department_channel():
    token = get_token("ops@test.local")

    response = client.get(
        "/api/messenger/bootstrap",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["policy"]["enabled"] is True
    assert data["unread_count"] == 0
    assert any(
        item["type"] == "department" and item["title"] == "Operations"
        for item in data["conversations"]
    )


def test_messenger_directory_returns_same_bank_active_staff_only():
    token = get_token("ops@test.local")

    response = client.get(
        "/api/messenger/directory",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    emails = {user["email"] for user in response.json()}
    assert "credit@test.local" in emails
    assert "admin@test.local" in emails
    assert "other@test.local" not in emails


def test_messenger_custom_group_send_and_unread_count():
    owner_token = get_token("ops@test.local")
    member_token = get_token("credit@test.local")
    credit_id = user_id("credit@test.local")

    response = client.post(
        "/api/messenger/conversations/custom",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"title": "Loan Review", "member_ids": [credit_id]},
    )

    assert response.status_code == 200
    conversation_id = response.json()["id"]
    assert response.json()["type"] == "custom"

    send_response = client.post(
        f"/api/messenger/conversations/{conversation_id}/messages",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"content": "Please review the attached loan checklist."},
    )

    assert send_response.status_code == 200
    unread_response = client.get(
        "/api/messenger/unread-count",
        headers={"Authorization": f"Bearer {member_token}"},
    )
    assert unread_response.status_code == 200
    assert unread_response.json()["unread_count"] == 1


def test_messenger_blocks_cross_bank_group_members():
    owner_token = get_token("ops@test.local")
    other_bank_user_id = user_id("other@test.local")

    response = client.post(
        "/api/messenger/conversations/custom",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"title": "Invalid Group", "member_ids": [other_bank_user_id]},
    )

    assert response.status_code == 404


def test_messenger_announcement_posting_is_admin_only():
    admin_token = get_token("admin@test.local")
    staff_token = get_token("ops@test.local")

    response = client.post(
        "/api/messenger/conversations/announcements",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"title": "IT Notices"},
    )

    assert response.status_code == 200
    conversation_id = response.json()["id"]

    staff_response = client.post(
        f"/api/messenger/conversations/{conversation_id}/messages",
        headers={"Authorization": f"Bearer {staff_token}"},
        json={"content": "Can I reply here?"},
    )
    assert staff_response.status_code == 403

    admin_response = client.post(
        f"/api/messenger/conversations/{conversation_id}/messages",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"content": "Core banking maintenance starts at 9 PM."},
    )
    assert admin_response.status_code == 200


def test_messenger_attachment_upload_is_isolated_from_documents_and_audited(tmp_path):
    token = get_token("ops@test.local")
    conversation_id = create_direct_conversation(token, user_id("credit@test.local"))

    response = client.post(
        f"/api/messenger/conversations/{conversation_id}/attachments",
        headers={"Authorization": f"Bearer {token}"},
        data={"caption": "Screenshot for internal review"},
        files={"file": ("notice.png", b"image-bytes", "image/png")},
    )

    assert response.status_code == 200
    attachment = response.json()["attachments"][0]
    assert attachment["original_filename"] == "notice.png"
    assert os.path.exists(attachment["stored_path"])
    with Session(engine) as session:
        assert session.exec(select(Document)).all() == []
        audit_event = session.exec(
            select(MessengerAuditEvent).where(
                MessengerAuditEvent.action == "attachment_upload"
            )
        ).first()
        assert audit_event is not None


def test_messenger_has_no_rag_or_ai_routes():
    token = get_token("ops@test.local")

    response = client.post(
        "/api/messenger/conversations/1/send-to-ai",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
