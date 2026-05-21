import json

import pytest
from sqlmodel import SQLModel, Session, select

from app.core.security import get_password_hash
from app.models.bank import Bank
from app.models.document import Document
from app.models.user import User
from app.schemas.document_intelligence import DocumentExtractionPageCreate
from app.services.document_intelligence_service import (
    build_extraction_flags,
    create_extraction_page,
    low_confidence_queue,
    mark_extraction_reviewed,
)
from app.services.ingestion_service import create_extraction_review_records
from test_main import engine


@pytest.fixture(autouse=True)
def setup_document_intelligence_db():
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        bank = Bank(name="Document AI Bank", code="DOCINT01")
        session.add(bank)
        session.commit()
        session.refresh(bank)
        user = User(
            email="doc-reviewer@test.local",
            password_hash=get_password_hash("password"),
            name="Document Reviewer",
            role="document_reviewer",
            bank_id=bank.id,
            is_active=True,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        session.add(Document(
            bank_id=bank.id,
            uploaded_by=user.id,
            title="Scanned KYC Form",
            file_name="kyc.pdf",
            file_type="pdf",
            file_path="/tmp/kyc.pdf",
            document_type="form",
            status="indexed",
        ))
        session.commit()

    yield
    SQLModel.metadata.drop_all(engine)


def _bank_and_document(session: Session):
    bank = session.exec(select(Bank).where(Bank.code == "DOCINT01")).first()
    document = session.exec(select(Document).where(Document.title == "Scanned KYC Form")).first()
    return bank, document


def test_extraction_flags_capture_low_confidence_and_visual_risk():
    flags = build_extraction_flags(
        ocr_confidence=0.61,
        table_confidence=0.93,
        has_handwriting=True,
        has_signature_like_region=True,
        has_stamp_like_region=False,
    )

    assert flags == ["low_ocr_confidence", "handwriting_detected", "signature_like_region"]


def test_low_confidence_queue_returns_unverified_pages_only():
    with Session(engine) as session:
        bank, document = _bank_and_document(session)
        low_page = create_extraction_page(
            session,
            bank_id=bank.id,
            document_id=document.id,
            data=DocumentExtractionPageCreate(
                page_number=1,
                extracted_text="Handwritten customer name and signature.",
                parser="ocr",
                ocr_confidence=0.62,
                has_handwriting=True,
            ),
        )
        create_extraction_page(
            session,
            bank_id=bank.id,
            document_id=document.id,
            data=DocumentExtractionPageCreate(
                page_number=2,
                extracted_text="Clean printed policy page.",
                parser="pdf_text",
                ocr_confidence=0.96,
            ),
        )

        queue = low_confidence_queue(session, bank_id=bank.id)
        reviewed = mark_extraction_reviewed(
            session,
            page_id=low_page.id,
            reviewed_by=123,
            review_status="verified",
            corrected_text="Verified customer name and signature region.",
        )
        queue_after_review = low_confidence_queue(session, bank_id=bank.id)

    assert [page.page_number for page in queue] == [1]
    assert reviewed.review_status == "verified"
    assert reviewed.reviewed_by == 123
    assert "low_ocr_confidence" in json.loads(reviewed.flags_json)
    assert queue_after_review == []


def test_ingestion_creates_review_records_for_extracted_pages():
    with Session(engine) as session:
        bank, document = _bank_and_document(session)
        records = create_extraction_review_records(
            session,
            bank_id=bank.id,
            document_id=document.id,
            pages=[
                {
                    "page_number": 1,
                    "text": "Scanned page text",
                    "ocr_confidence": 0.58,
                    "table_confidence": None,
                    "extraction_confidence": 0.62,
                },
                {
                    "page_number": 2,
                    "text": "Clean text page",
                    "ocr_confidence": 0.95,
                    "table_confidence": None,
                    "extraction_confidence": 0.98,
                },
            ],
        )
        queue = low_confidence_queue(session, bank_id=bank.id)

    assert len(records) == 2
    assert [page.page_number for page in queue] == [1]
    assert "low_ocr_confidence" in json.loads(queue[0].flags_json)
