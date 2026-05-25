from pathlib import Path
from types import SimpleNamespace

from openpyxl import Workbook
from openpyxl.worksheet.table import Table

from app.services import ingestion_service
from app.services.ingestion_service import build_indexable_chunks, extract_pages


def test_build_indexable_chunks_preserves_page_and_section_metadata():
    pages = [
        {
            "page_number": 1,
            "text": "Section 1 Introduction\nThis policy explains account opening responsibilities.",
        },
        {
            "page_number": 2,
            "text": "Section 2 KYC Review\nBranch staff must verify KYC documents before account opening.",
        },
    ]

    chunks = build_indexable_chunks(pages, chunk_size=120, chunk_overlap=20)

    assert chunks[0]["page_number"] == 1
    assert chunks[0]["section_label"] == "Section 1"
    assert chunks[0]["text"].startswith("Section 1 Introduction")
    assert chunks[1]["page_number"] == 2
    assert chunks[1]["section_label"] == "Section 2"
    assert "verify KYC" in chunks[1]["text"]


def test_build_indexable_chunks_falls_back_to_document_level_text():
    chunks = build_indexable_chunks(
        [{"page_number": None, "text": "Clause 3.1 requires supervisor approval for exceptions."}],
        chunk_size=120,
        chunk_overlap=20,
    )

    assert chunks[0]["text"] == "Clause 3.1 requires supervisor approval for exceptions."
    assert chunks[0]["page_number"] is None
    assert chunks[0]["section_label"] == "Clause 3.1"


def test_extract_xlsx_preserves_sheet_tables_merges_and_formulas(tmp_path: Path):
    workbook_path = tmp_path / "complex.xlsx"
    wb = Workbook()
    ws = wb.active
    ws.title = "Loan Pipeline"
    ws.merge_cells("A1:C1")
    ws["A1"] = "Loan Pipeline Summary"
    ws["A2"] = "Borrower"
    ws["B2"] = "Amount"
    ws["C2"] = "Total"
    ws["A3"] = "ACME"
    ws["B3"] = 125000
    ws["C3"] = "=B3*1.1"
    ws.add_table(Table(displayName="LoanTable", ref="A2:C3"))
    wb.save(workbook_path)

    pages = extract_pages(str(workbook_path), "xlsx")

    assert len(pages) == 1
    text = pages[0]["text"]
    assert "--- Sheet: Loan Pipeline ---" in text
    assert "Merged ranges: A1:C1" in text
    assert "Tables: LoanTable=A2:C3" in text
    assert "C3 formula==B3*1.1" in text
    assert "A3=ACME" in text


def test_degraded_nepali_pdf_text_layer_uses_ocr_fallback(monkeypatch, tmp_path: Path):
    pdf_path = tmp_path / "nepali.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 fake")

    corrupt_text = (
        "२. पररभाषा: ववषय वा प्रसङ्गले अकको  अथ न नलागेमा यस ऐनमा,-\n"
        "(२) यो ऐन िरुु न्ि प्रारम्भ हनु ेछ।\n"
        "(क) वस्त ु सम्झन ु पछन।"
    )
    repaired_text = (
        "२. परिभाषा: विषय वा प्रसङ्गले अर्को अर्थ नलागेमा यस ऐनमा,-\n"
        "(२) यो ऐन तुरुन्त प्रारम्भ हुनेछ।\n"
        "(क) वस्तु सम्झनु पर्छ।"
    )

    class FakePage:
        def extract_text(self):
            return corrupt_text

        def extract_tables(self):
            return []

    class FakePdf:
        pages = [FakePage()]

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    class FakeImage:
        def close(self):
            pass

    monkeypatch.setitem(
        __import__("sys").modules,
        "pdfplumber",
        SimpleNamespace(open=lambda _path: FakePdf()),
    )
    monkeypatch.setattr(
        ingestion_service,
        "convert_pdf_pages_to_images",
        lambda path, *, first_page, last_page: [FakeImage()],
    )
    monkeypatch.setattr(
        ingestion_service,
        "ocr_pil_image_to_text",
        lambda _image: ingestion_service.OcrResult(text=repaired_text, confidence=0.93),
    )

    pages = extract_pages(str(pdf_path), "pdf")

    assert len(pages) == 1
    assert pages[0]["text"] == repaired_text
    assert pages[0]["ocr_confidence"] == 0.93
    assert pages[0]["pdf_text_layer_repaired"] is True


def test_clean_nepali_pdf_text_layer_does_not_use_ocr(monkeypatch, tmp_path: Path):
    pdf_path = tmp_path / "clean-nepali.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 fake")
    clean_text = "यो ऐन तुरुन्त प्रारम्भ हुनेछ। विषय वा प्रसङ्गले अर्को अर्थ नलागेमा।"

    class FakePage:
        def extract_text(self):
            return clean_text

        def extract_tables(self):
            return []

    class FakePdf:
        pages = [FakePage()]

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    def fail_ocr(*_args, **_kwargs):
        raise AssertionError("clean Nepali text layer should not be OCRed")

    monkeypatch.setitem(
        __import__("sys").modules,
        "pdfplumber",
        SimpleNamespace(open=lambda _path: FakePdf()),
    )
    monkeypatch.setattr(ingestion_service, "convert_pdf_pages_to_images", fail_ocr)

    pages = extract_pages(str(pdf_path), "pdf")

    assert len(pages) == 1
    assert pages[0]["text"] == clean_text
    assert pages[0]["ocr_confidence"] is None
    assert "pdf_text_layer_repaired" not in pages[0]


def test_degraded_nepali_pdf_repair_keeps_direct_line_when_ocr_adds_latin_noise(monkeypatch, tmp_path: Path):
    pdf_path = tmp_path / "noisy-nepali.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 fake")

    corrupt_text = "भउू पयोग ऐन , २०७६\n२०७६/०५/०६\n(२) यो ऐन िरुु न्ि प्रारम्भ हनु ेछ।"
    ocr_text = "भूउपयोग UT, ROWE\n२०७६/०%५/०६\n(२) यो ऐन तुरुन्त प्रारम्भ हुनेछ।"

    class FakePage:
        def extract_text(self):
            return corrupt_text

        def extract_tables(self):
            return []

    class FakePdf:
        pages = [FakePage()]

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    class FakeImage:
        def close(self):
            pass

    monkeypatch.setitem(
        __import__("sys").modules,
        "pdfplumber",
        SimpleNamespace(open=lambda _path: FakePdf()),
    )
    monkeypatch.setattr(
        ingestion_service,
        "convert_pdf_pages_to_images",
        lambda path, *, first_page, last_page: [FakeImage()],
    )
    monkeypatch.setattr(
        ingestion_service,
        "ocr_pil_image_to_text",
        lambda _image: ingestion_service.OcrResult(text=ocr_text, confidence=0.92),
    )

    pages = extract_pages(str(pdf_path), "pdf")

    assert pages[0]["text"] == "भउू पयोग ऐन , २०७६\n२०७६/०५/०६\n(२) यो ऐन तुरुन्त प्रारम्भ हुनेछ।"
