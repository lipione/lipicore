from pathlib import Path

from PIL import Image

from app.services import ingestion_service
from app.services import llm_service


def test_image_extraction_uses_open_source_ocr(monkeypatch, tmp_path):
    image_path = tmp_path / "scan.png"
    Image.new("RGB", (80, 40), "white").save(image_path)

    def fake_ocr_image_file(file_path):
        assert Path(file_path) == image_path
        return ingestion_service.OcrResult(text="Open source OCR text", confidence=0.91)

    def fail_vision(*_args, **_kwargs):
        raise AssertionError("vision LLM should not be used for OCR extraction")

    monkeypatch.setattr(ingestion_service, "ocr_image_file", fake_ocr_image_file, raising=False)
    monkeypatch.setattr(llm_service, "call_vision_llm", fail_vision)
    monkeypatch.setattr(ingestion_service, "_transcribe_image_with_lipicore", fail_vision, raising=False)

    pages = ingestion_service.extract_pages(str(image_path), "png")

    assert pages == [
        {
            "page_number": 1,
            "text": "Open source OCR text",
            "extraction_confidence": 0.82,
            "ocr_confidence": 0.91,
            "table_confidence": None,
            "page_bbox_json": None,
        }
    ]


def test_low_confidence_nepali_image_uses_lipicore_handwriting_fallback(monkeypatch, tmp_path):
    image_path = tmp_path / "handwriting.png"
    Image.new("RGB", (120, 80), "white").save(image_path)

    def fake_ocr_image_file(file_path):
        assert Path(file_path) == image_path
        return ingestion_service.OcrResult(text="Hho Sau A\nXO HORT HM EIS =", confidence=0.45)

    def fake_lipicore_transcribe(file_path):
        assert Path(file_path) == image_path
        return "शब्द लेखन\nबाबा काका माला धाता"

    monkeypatch.setattr(ingestion_service, "ocr_image_file", fake_ocr_image_file, raising=False)
    monkeypatch.setattr(ingestion_service, "_transcribe_image_with_lipicore", fake_lipicore_transcribe, raising=False)

    pages = ingestion_service.extract_pages(str(image_path), "png")

    assert pages[0]["text"] == "शब्द लेखन\nबाबा काका माला धाता"
    assert pages[0]["ocr_confidence"] == 0.45
    assert pages[0]["vision_transcription"] is True
    assert pages[0]["vision_model"] == "LipiCore"


def test_scanned_pdf_fallback_uses_open_source_ocr(monkeypatch, tmp_path):
    from reportlab.pdfgen import canvas

    pdf_path = tmp_path / "scan.pdf"
    c = canvas.Canvas(str(pdf_path))
    c.showPage()
    c.save()

    dummy_image = Image.new("RGB", (80, 40), "white")

    def fake_convert_pdf_pages_to_images(file_path, *, first_page, last_page):
        assert Path(file_path) == pdf_path
        assert first_page == 1
        assert last_page == 1
        return [dummy_image]

    def fake_ocr_pil_image_to_text(image):
        assert image is dummy_image
        return ingestion_service.OcrResult(text="OCR text from scanned PDF", confidence=0.88)

    def fail_vision(*_args, **_kwargs):
        raise AssertionError("vision LLM should not be used for scanned PDF OCR")

    monkeypatch.setattr(ingestion_service, "convert_pdf_pages_to_images", fake_convert_pdf_pages_to_images, raising=False)
    monkeypatch.setattr(ingestion_service, "ocr_pil_image_to_text", fake_ocr_pil_image_to_text, raising=False)
    monkeypatch.setattr(llm_service, "call_vision_llm", fail_vision)

    pages = ingestion_service.extract_pages(str(pdf_path), "pdf")

    assert len(pages) == 1
    assert pages[0]["page_number"] == 1
    assert pages[0]["text"] == "OCR text from scanned PDF"
    assert pages[0]["ocr_confidence"] == 0.88
