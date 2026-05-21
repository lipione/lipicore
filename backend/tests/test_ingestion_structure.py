from pathlib import Path

from openpyxl import Workbook
from openpyxl.worksheet.table import Table

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
