import json

import pytest
from sqlmodel import SQLModel, Session, select

from app.core.security import get_password_hash
from app.models.bank import Bank
from app.models.document import Document
from app.models.long_document_analysis import LongDocumentAnalysisJob
from app.models.user import User
from app.schemas.long_document_analysis import LongDocumentAnalysisCreate
from app.services.long_document_analysis_service import (
    create_long_document_analysis_job,
    process_long_document_analysis_job,
)
from test_main import engine


@pytest.fixture(autouse=True)
def setup_long_analysis_db():
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        bank = Bank(name="Long Analysis Bank", code="LA01")
        session.add(bank)
        session.commit()
        session.refresh(bank)

        staff = User(
            email="long-analysis-staff@test.local",
            password_hash=get_password_hash("password"),
            name="Long Analysis Staff",
            role="staff_user",
            bank_id=bank.id,
            is_active=True,
        )
        session.add(staff)
        session.commit()
        session.refresh(staff)

        document = Document(
            bank_id=bank.id,
            uploaded_by=staff.id,
            title="Large policy",
            file_name="large-policy.pdf",
            file_type="pdf",
            file_path="/tmp/large-policy.pdf",
            status="indexed",
            document_scope="session_upload",
        )
        session.add(document)
        session.commit()

    yield
    SQLModel.metadata.drop_all(engine)


def _fixtures(session: Session):
    bank = session.exec(select(Bank).where(Bank.code == "LA01")).first()
    staff = session.exec(select(User).where(User.email == "long-analysis-staff@test.local")).first()
    document = session.exec(select(Document).where(Document.file_name == "large-policy.pdf")).first()
    return bank, staff, document


def test_process_long_document_analysis_selects_relevant_excerpts_and_records_result(monkeypatch):
    captured = {}
    monkeypatch.setattr("app.services.long_document_analysis_service.engine", engine)

    def fake_extract_pages(file_path: str, file_type: str):
        return [
            {"page_number": 1, "text": "General introduction. " + ("noise " * 3000)},
            {
                "page_number": 88,
                "text": "Loan exception approval must be reviewed by Credit Risk and branch operations.",
            },
        ]

    def fake_model_call(prompt: str, system: str | None = None) -> str:
        captured["prompt"] = prompt
        captured["system"] = system
        return "Credit Risk must review loan exception approval."

    monkeypatch.setattr("app.services.long_document_analysis_service.extract_pages", fake_extract_pages)
    monkeypatch.setattr("app.services.long_document_analysis_service.call_deep_model", fake_model_call)

    with Session(engine) as session:
        bank, staff, document = _fixtures(session)
        job = create_long_document_analysis_job(
            session,
            bank_id=bank.id,
            requested_by=staff.id,
            data=LongDocumentAnalysisCreate(
                document_id=document.id,
                prompt="Who reviews loan exception approval?",
                analysis_type="targeted_question",
            ),
        )
        job_id = job.id

    process_long_document_analysis_job(job_id)

    with Session(engine) as session:
        saved = session.get(LongDocumentAnalysisJob, job_id)

    assert saved.status == "completed"
    assert saved.progress == 100
    assert saved.result_text == "Credit Risk must review loan exception approval."
    assert saved.completed_at is not None
    assert "Loan exception approval" in captured["prompt"]
    assert "noise " not in captured["prompt"][:1000]
    metadata = json.loads(saved.metadata_json)
    assert metadata["shortened"] is True
    assert metadata["selected_chunks"] >= 1
    assert metadata["total_pages"] == 2


def test_process_long_document_analysis_marks_failed_when_no_text(monkeypatch):
    monkeypatch.setattr("app.services.long_document_analysis_service.engine", engine)
    monkeypatch.setattr("app.services.long_document_analysis_service.extract_pages", lambda *_: [])

    with Session(engine) as session:
        bank, staff, document = _fixtures(session)
        job = create_long_document_analysis_job(
            session,
            bank_id=bank.id,
            requested_by=staff.id,
            data=LongDocumentAnalysisCreate(
                document_id=document.id,
                prompt="Summarize this file.",
            ),
        )
        job_id = job.id

    process_long_document_analysis_job(job_id)

    with Session(engine) as session:
        saved = session.get(LongDocumentAnalysisJob, job_id)

    assert saved.status == "failed"
    assert saved.progress == 100
    assert "No text could be extracted" in saved.error_message
