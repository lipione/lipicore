from sqlmodel import SQLModel, Session, select

from app.api import ocr as ocr_api
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


def test_ocr_vision_review_adds_separate_note_for_image(monkeypatch):
    token = get_token("ocr-staff@test.local")
    calls = []

    def fake_extract_pages(file_path: str, file_type: str):
        assert file_type == "png"
        return [
            {
                "text": "Customer Name: Rama\nAmount: NPR 10,000",
                "extraction_confidence": 0.9,
                "ocr_confidence": 0.88,
            }
        ]

    def fake_call_vision_llm(prompt: str, image_b64: str):
        calls.append((prompt, image_b64))
        return "Vision note: stamp is visible; review account number."

    monkeypatch.setattr(ocr_api, "extract_pages", fake_extract_pages)
    monkeypatch.setattr(ocr_api, "call_vision_llm", fake_call_vision_llm, raising=False)

    response = client.post(
        "/api/ocr/extract",
        headers={"Authorization": f"Bearer {token}"},
        data={"vision_review": "true"},
        files={"file": ("sample.png", b"not-a-real-image-but-not-needed", "image/png")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["vision_review_requested"] is True
    assert payload["vision_review_pages"] == 1
    assert payload["full_text"] == "Customer Name: Rama\nAmount: NPR 10,000"
    assert payload["pages"][0]["vision_review"] == "Vision note: stamp is visible; review account number."
    assert "OCR text for comparison" in calls[0][0]
    assert calls[0][1]


def test_ocr_vision_review_skips_non_visual_files():
    token = get_token("ocr-staff@test.local")

    response = client.post(
        "/api/ocr/extract",
        headers={"Authorization": f"Bearer {token}"},
        data={"vision_review": "true"},
        files={"file": ("sample.txt", b"Plain internal memo", "text/plain")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["vision_review_requested"] is True
    assert payload["vision_review_pages"] == 0
    assert any("Vision review is only available" in warning for warning in payload["warnings"])
    assert payload["pages"][0]["vision_review"] is None


def test_ocr_warns_when_degraded_pdf_text_layer_was_repaired(monkeypatch):
    token = get_token("ocr-staff@test.local")

    def fake_extract_pages(file_path: str, file_type: str):
        assert file_type == "pdf"
        return [
            {
                "page_number": 1,
                "text": "यो ऐन तुरुन्त प्रारम्भ हुनेछ।",
                "extraction_confidence": 0.82,
                "ocr_confidence": 0.93,
                "pdf_text_layer_repaired": True,
            }
        ]

    monkeypatch.setattr(ocr_api, "extract_pages", fake_extract_pages)

    response = client.post(
        "/api/ocr/extract",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("sample.pdf", b"%PDF-1.4 fake", "application/pdf")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert any("degraded embedded PDF text" in warning for warning in payload["warnings"])
