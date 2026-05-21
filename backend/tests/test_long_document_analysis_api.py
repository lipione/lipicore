import pytest
from sqlmodel import SQLModel, Session, select

from app.core.security import get_password_hash
from app.models.bank import Bank
from app.models.document import Document
from app.models.user import User
from app.models.long_document_analysis import LongDocumentAnalysisJob
from test_main import client, engine, get_token


@pytest.fixture(autouse=True)
def setup_long_analysis_api_db():
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        bank = Bank(name="Long Analysis Bank", code="LAB01")
        other_bank = Bank(name="Other Long Analysis Bank", code="LAB02")
        session.add(bank)
        session.add(other_bank)
        session.commit()
        session.refresh(bank)
        session.refresh(other_bank)

        staff = User(
            email="staff@test.local",
            password_hash=get_password_hash("password"),
            name="Staff User",
            role="staff_user",
            bank_id=bank.id,
            is_active=True,
        )
        peer_staff = User(
            email="peer-staff@test.local",
            password_hash=get_password_hash("password"),
            name="Peer Staff User",
            role="staff_user",
            bank_id=bank.id,
            is_active=True,
        )
        admin = User(
            email="admin@test.local",
            password_hash=get_password_hash("password"),
            name="Bank Admin",
            role="bank_admin",
            bank_id=bank.id,
            is_active=True,
        )
        other_staff = User(
            email="other-staff@test.local",
            password_hash=get_password_hash("password"),
            name="Other Staff User",
            role="staff_user",
            bank_id=other_bank.id,
            is_active=True,
        )
        session.add(staff)
        session.add(peer_staff)
        session.add(admin)
        session.add(other_staff)
        session.commit()

    yield
    SQLModel.metadata.drop_all(engine)


def _user(email: str) -> User:
    with Session(engine) as session:
        user = session.exec(select(User).where(User.email == email)).first()
        assert user is not None
        return user


def test_staff_can_queue_long_analysis_for_approved_bank_document(monkeypatch):
    queued_job_ids = []

    def fake_enqueue(job_id: int, _db: Session) -> str:
        queued_job_ids.append(job_id)
        return f"long-analysis-{job_id}"

    monkeypatch.setattr("app.api.long_document_analysis.enqueue_long_document_analysis_job", fake_enqueue)

    staff = _user("staff@test.local")
    with Session(engine) as session:
        doc = Document(
            bank_id=staff.bank_id,
            uploaded_by=staff.id,
            title="Large Loan SOP.pdf",
            file_name="Large Loan SOP.pdf",
            file_type="pdf",
            file_path="/tmp/large-loan-sop.pdf",
            document_type="policy",
            status="approved",
            version_state="approved",
            document_scope="global_knowledge",
            processing_progress=100,
        )
        session.add(doc)
        session.commit()
        session.refresh(doc)
        doc_id = doc.id

    token = get_token("staff@test.local")
    response = client.post(
        "/api/long-document-analysis",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "document_id": doc_id,
            "prompt": "Summarize the eligibility and missing-document rules.",
            "analysis_type": "summary",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["document_id"] == doc_id
    assert payload["status"] == "queued"
    assert payload["progress"] >= 5
    assert queued_job_ids == [payload["id"]]


def test_staff_cannot_queue_long_analysis_for_unapproved_global_document(monkeypatch):
    monkeypatch.setattr(
        "app.api.long_document_analysis.enqueue_long_document_analysis_job",
        lambda _job_id, _db: "not-called",
    )

    staff = _user("staff@test.local")
    with Session(engine) as session:
        doc = Document(
            bank_id=staff.bank_id,
            uploaded_by=staff.id,
            title="Draft Procedure.pdf",
            file_name="Draft Procedure.pdf",
            file_type="pdf",
            file_path="/tmp/draft-procedure.pdf",
            document_type="procedure",
            status="ready",
            version_state="draft",
            document_scope="global_knowledge",
        )
        session.add(doc)
        session.commit()
        session.refresh(doc)
        doc_id = doc.id

    token = get_token("staff@test.local")
    response = client.post(
        "/api/long-document-analysis",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "document_id": doc_id,
            "prompt": "Summarize this draft.",
        },
    )

    assert response.status_code == 403
    with Session(engine) as session:
        jobs = session.exec(select(LongDocumentAnalysisJob)).all()
    assert jobs == []


def test_long_analysis_list_is_scoped_to_current_bank(monkeypatch):
    monkeypatch.setattr(
        "app.api.long_document_analysis.enqueue_long_document_analysis_job",
        lambda job_id, _db: f"long-analysis-{job_id}",
    )

    staff = _user("staff@test.local")
    other_staff = _user("other-staff@test.local")
    with Session(engine) as session:
        own_doc = Document(
            bank_id=staff.bank_id,
            uploaded_by=staff.id,
            title="Own Approved Policy.pdf",
            file_name="Own Approved Policy.pdf",
            file_type="pdf",
            file_path="/tmp/own-approved-policy.pdf",
            document_type="policy",
            status="approved",
            version_state="approved",
            document_scope="global_knowledge",
        )
        other_doc = Document(
            bank_id=other_staff.bank_id,
            uploaded_by=other_staff.id,
            title="Other Bank Policy.pdf",
            file_name="Other Bank Policy.pdf",
            file_type="pdf",
            file_path="/tmp/other-bank-policy.pdf",
            document_type="policy",
            status="approved",
            version_state="approved",
            document_scope="global_knowledge",
        )
        session.add(own_doc)
        session.add(other_doc)
        session.commit()
        session.refresh(own_doc)
        session.refresh(other_doc)

        session.add(
            LongDocumentAnalysisJob(
                bank_id=other_staff.bank_id,
                document_id=other_doc.id,
                requested_by=other_staff.id,
                prompt="Summarize other bank doc",
                status="completed",
                progress=100,
                result_text="Other bank result",
            )
        )
        session.commit()
        own_doc_id = own_doc.id

    token = get_token("staff@test.local")
    create_response = client.post(
        "/api/long-document-analysis",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "document_id": own_doc_id,
            "prompt": "Summarize the approved policy.",
        },
    )
    assert create_response.status_code == 200

    list_response = client.get(
        "/api/long-document-analysis",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert list_response.status_code == 200
    jobs = list_response.json()
    assert len(jobs) == 1
    assert jobs[0]["document_id"] == own_doc_id
    assert jobs[0]["result_text"] is None


def test_staff_only_reads_own_long_analysis_jobs_inside_bank():
    staff = _user("staff@test.local")
    peer_staff = _user("peer-staff@test.local")
    with Session(engine) as session:
        doc = Document(
            bank_id=staff.bank_id,
            uploaded_by=staff.id,
            title="Shared Policy.pdf",
            file_name="Shared Policy.pdf",
            file_type="pdf",
            file_path="/tmp/shared-policy.pdf",
            document_type="policy",
            status="approved",
            version_state="approved",
            document_scope="global_knowledge",
        )
        session.add(doc)
        session.commit()
        session.refresh(doc)
        own_job = LongDocumentAnalysisJob(
            bank_id=staff.bank_id,
            document_id=doc.id,
            requested_by=staff.id,
            prompt="Summarize my work",
            status="completed",
            progress=100,
            result_text="Own result",
        )
        peer_job = LongDocumentAnalysisJob(
            bank_id=peer_staff.bank_id,
            document_id=doc.id,
            requested_by=peer_staff.id,
            prompt="Summarize peer work",
            status="completed",
            progress=100,
            result_text="Peer result",
        )
        session.add(own_job)
        session.add(peer_job)
        session.commit()
        session.refresh(own_job)
        session.refresh(peer_job)
        own_job_id = own_job.id
        peer_job_id = peer_job.id

    staff_token = get_token("staff@test.local")
    list_response = client.get(
        "/api/long-document-analysis",
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    assert list_response.status_code == 200
    jobs = list_response.json()
    assert [job["id"] for job in jobs] == [own_job_id]

    peer_response = client.get(
        f"/api/long-document-analysis/{peer_job_id}",
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    assert peer_response.status_code == 404

    admin_token = get_token("admin@test.local")
    admin_response = client.get(
        f"/api/long-document-analysis/{peer_job_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert admin_response.status_code == 200
