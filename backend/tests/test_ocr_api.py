from sqlmodel import SQLModel, Session, select

from app.core.security import get_password_hash
from app.models.bank import Bank
from app.models.document import Document
from app.models.user import User
from test_main import client, engine, get_token


def setup_function():
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        bank = Bank(name="OCR Bank", code="OCR01")
        session.add(bank)
        session.commit()
        session.refresh(bank)

        user = User(
            email="ocr-staff@test.local",
            password_hash=get_password_hash("password"),
            name="OCR Staff",
            role="staff_user",
            bank_id=bank.id,
            is_active=True,
        )
        session.add(user)
        session.commit()


def teardown_function():
    SQLModel.metadata.drop_all(engine)


def test_ocr_extracts_text_without_creating_document_record():
    token = get_token("ocr-staff@test.local")

    response = client.post(
        "/api/ocr/extract",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("sample.txt", b"Customer name: Test User\nAmount: NPR 10,000", "text/plain")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["file_name"] == "sample.txt"
    assert payload["file_type"] == "txt"
    assert payload["page_count"] == 1
    assert "Customer name: Test User" in payload["full_text"]
    assert payload["pages"][0]["label"] == "Text"

    with Session(engine) as session:
        docs = session.exec(select(Document)).all()
    assert docs == []


def test_ocr_rejects_unsupported_files():
    token = get_token("ocr-staff@test.local")

    response = client.post(
        "/api/ocr/extract",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("sample.exe", b"not allowed", "application/octet-stream")},
    )

    assert response.status_code == 400
    assert "Supported" in response.json()["detail"]
