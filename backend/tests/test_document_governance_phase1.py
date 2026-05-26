import json

import pytest
from sqlmodel import SQLModel, Session, select

from app.core.security import get_password_hash
from app.models.bank import Bank
from app.models.chat import ChatSession
from app.models.document import Document, DocumentChunk
from app.models.user import User
from app.services import qdrant_service
from test_main import client, engine, get_token


@pytest.fixture(autouse=True)
def setup_governance_db(monkeypatch):
    client.cookies.clear()
    SQLModel.metadata.create_all(engine)
    updates = []

    def fake_update_points(document_id, bank_id, payload):
        updates.append({"document_id": document_id, "bank_id": bank_id, "payload": payload})

    monkeypatch.setattr(qdrant_service, "update_points_by_document_payload", fake_update_points)

    with Session(engine) as session:
        bank = Bank(name="Phase Bank", code="PHASE01")
        other_bank = Bank(name="Other Bank", code="OTHER01")
        session.add(bank)
        session.add(other_bank)
        session.commit()
        session.refresh(bank)
        session.refresh(other_bank)

        users = [
            User(
                email="admin@test.local",
                password_hash=get_password_hash("password"),
                name="Bank Admin",
                role="bank_admin",
                bank_id=bank.id,
                is_active=True,
            ),
            User(
                email="staff@test.local",
                password_hash=get_password_hash("password"),
                name="Staff User",
                role="staff_user",
                bank_id=bank.id,
                department="Operations",
                is_active=True,
            ),
            User(
                email="other-admin@test.local",
                password_hash=get_password_hash("password"),
                name="Other Admin",
                role="bank_admin",
                bank_id=other_bank.id,
                is_active=True,
            ),
        ]
        session.add_all(users)
        session.commit()

    yield updates
    client.cookies.clear()
    SQLModel.metadata.drop_all(engine)


def _create_document(
    *,
    bank_id: int,
    uploaded_by: int,
    status: str = "ready",
    version_state: str = "draft",
    department: str | None = "General",
    document_scope: str = "global_knowledge",
    session_id: int | None = None,
) -> int:
    with Session(engine) as session:
        doc = Document(
            bank_id=bank_id,
            uploaded_by=uploaded_by,
            title="Policy.pdf",
            file_name="Policy.pdf",
            file_type="pdf",
            file_path="/tmp/policy.pdf",
            document_type="policy",
            department=department,
            access_level=0,
            status=status,
            version_state=version_state,
            document_scope=document_scope,
            session_id=session_id,
        )
        session.add(doc)
        session.commit()
        session.refresh(doc)
        session.add(
            DocumentChunk(
                bank_id=bank_id,
                document_id=doc.id,
                chunk_index=0,
                chunk_text="Section 1. Staff must verify customer identity before account opening.",
                page_number=3,
                qdrant_point_id="point-1",
                department=department,
                access_level=0,
                document_scope=document_scope,
                session_id=session_id,
                document_status=status,
                version_state=version_state,
            )
        )
        session.commit()
        return doc.id


def _user_id(email: str) -> int:
    with Session(engine) as session:
        return session.exec(select(User).where(User.email == email)).first().id


def _bank_id(code: str) -> int:
    with Session(engine) as session:
        return session.exec(select(Bank).where(Bank.code == code)).first().id


def test_bank_admin_updates_governance_metadata_and_chunk_payload(setup_governance_db):
    bank_id = _bank_id("PHASE01")
    admin_id = _user_id("admin@test.local")
    doc_id = _create_document(bank_id=bank_id, uploaded_by=admin_id)
    token = get_token("admin@test.local")

    response = client.patch(
        f"/api/documents/{doc_id}/governance",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "department": "Compliance",
            "access_level": 1,
            "document_type": "compliance",
            "regulator": "Nepal Rastra Bank",
            "jurisdiction": "Nepal",
        },
    )

    assert response.status_code == 200
    assert response.json()["department"] == "Compliance"
    with Session(engine) as session:
        chunk = session.exec(select(DocumentChunk).where(DocumentChunk.document_id == doc_id)).first()
        assert chunk.department == "Compliance"
        assert chunk.access_level == 1
    assert setup_governance_db[-1]["payload"]["department"] == "Compliance"
    assert setup_governance_db[-1]["payload"]["access_level"] == 1


def test_staff_cannot_update_document_governance():
    bank_id = _bank_id("PHASE01")
    admin_id = _user_id("admin@test.local")
    doc_id = _create_document(bank_id=bank_id, uploaded_by=admin_id)
    token = get_token("staff@test.local")

    response = client.patch(
        f"/api/documents/{doc_id}/governance",
        headers={"Authorization": f"Bearer {token}"},
        json={"department": "Compliance"},
    )

    assert response.status_code == 403


def test_cross_bank_admin_cannot_update_document_governance():
    bank_id = _bank_id("PHASE01")
    admin_id = _user_id("admin@test.local")
    doc_id = _create_document(bank_id=bank_id, uploaded_by=admin_id)
    token = get_token("other-admin@test.local")

    response = client.patch(
        f"/api/documents/{doc_id}/governance",
        headers={"Authorization": f"Bearer {token}"},
        json={"department": "Compliance"},
    )

    assert response.status_code == 404


def test_lifecycle_disable_updates_document_chunks_and_qdrant(setup_governance_db):
    bank_id = _bank_id("PHASE01")
    admin_id = _user_id("admin@test.local")
    doc_id = _create_document(bank_id=bank_id, uploaded_by=admin_id, status="approved", version_state="approved")
    token = get_token("admin@test.local")

    response = client.patch(
        f"/api/documents/{doc_id}/lifecycle",
        headers={"Authorization": f"Bearer {token}"},
        json={"state": "disabled", "reason": "bad source"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "disabled"
    assert response.json()["version_state"] == "disabled"
    with Session(engine) as session:
        chunk = session.exec(select(DocumentChunk).where(DocumentChunk.document_id == doc_id)).first()
        assert chunk.document_status == "disabled"
        assert chunk.version_state == "disabled"
    assert setup_governance_db[-1]["payload"]["document_status"] == "disabled"
    assert setup_governance_db[-1]["payload"]["version_state"] == "disabled"


def test_source_viewer_returns_bank_scoped_approved_chunks():
    bank_id = _bank_id("PHASE01")
    admin_id = _user_id("admin@test.local")
    doc_id = _create_document(
        bank_id=bank_id,
        uploaded_by=admin_id,
        status="approved",
        version_state="approved",
        department="Operations",
    )
    token = get_token("staff@test.local")

    response = client.get(
        f"/api/documents/{doc_id}/source?page_number=3",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["document"]["id"] == doc_id
    assert payload["chunks"][0]["text"].startswith("Section 1")
    assert payload["chunks"][0]["page_number"] == 3


def test_staff_cannot_view_draft_global_source():
    bank_id = _bank_id("PHASE01")
    admin_id = _user_id("admin@test.local")
    doc_id = _create_document(bank_id=bank_id, uploaded_by=admin_id, status="ready", version_state="draft")
    token = get_token("staff@test.local")

    response = client.get(
        f"/api/documents/{doc_id}/source",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404


def test_session_upload_source_is_visible_only_to_owner():
    bank_id = _bank_id("PHASE01")
    staff_id = _user_id("staff@test.local")
    admin_id = _user_id("admin@test.local")
    with Session(engine) as session:
        chat = ChatSession(bank_id=bank_id, user_id=staff_id, title="Upload")
        session.add(chat)
        session.commit()
        session.refresh(chat)
        session_id = chat.id
    doc_id = _create_document(
        bank_id=bank_id,
        uploaded_by=staff_id,
        status="ready",
        version_state="draft",
        document_scope="session_upload",
        session_id=session_id,
    )
    staff_token = get_token("staff@test.local")
    admin_token = get_token("admin@test.local")

    assert client.get(
        f"/api/documents/{doc_id}/source",
        headers={"Authorization": f"Bearer {staff_token}"},
    ).status_code == 200

    response = client.get(
        f"/api/documents/{doc_id}/source",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 404
