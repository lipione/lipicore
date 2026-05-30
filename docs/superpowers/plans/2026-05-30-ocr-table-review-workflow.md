# OCR And Table Review Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make OCR/table extraction quality visible and reviewable before low-confidence content becomes approved bank knowledge.

**Architecture:** Use existing page-level extraction records and confidence fields. Add deterministic quality buckets, store review flags consistently, expose low-confidence pages through the existing document review/OCR surfaces, and add table-focused regression tests for Excel and PDF extraction metadata.

**Tech Stack:** FastAPI, SQLModel, existing `DocumentExtractionPage`, ingestion service, OCR service, pytest, React OCR/review UI.

---

## File Structure

- Create: `backend/app/services/extraction_quality_service.py`
- Create: `backend/tests/test_extraction_quality_service.py`
- Modify: `backend/app/services/ingestion_service.py`
- Modify: `backend/app/services/document_intelligence_service.py`
- Modify: `backend/app/api/document_review.py`
- Modify: `frontend/src/pages/OcrExtraction.jsx`
- Test: `backend/tests/test_ingestion_structure.py`
- Test: `backend/tests/test_document_intelligence_service.py`

## Task 1: Add Extraction Quality Buckets

**Files:**
- Create: `backend/app/services/extraction_quality_service.py`
- Create: `backend/tests/test_extraction_quality_service.py`

- [ ] **Step 1: Write failing quality tests**

Create `backend/tests/test_extraction_quality_service.py`:

```python
from app.services.extraction_quality_service import build_extraction_quality


def test_quality_marks_low_ocr_confidence_for_review():
    result = build_extraction_quality(
        extraction_confidence=0.82,
        ocr_confidence=0.41,
        table_confidence=None,
        text="Visible but noisy OCR text",
    )

    assert result["quality_bucket"] == "review_required"
    assert "low_ocr_confidence" in result["flags"]


def test_quality_marks_table_review_when_table_confidence_is_low():
    result = build_extraction_quality(
        extraction_confidence=0.95,
        ocr_confidence=None,
        table_confidence=0.52,
        text="Row 1: Customer | Limit",
    )

    assert result["quality_bucket"] == "review_required"
    assert "low_table_confidence" in result["flags"]


def test_quality_marks_clean_direct_text_as_reliable():
    result = build_extraction_quality(
        extraction_confidence=0.97,
        ocr_confidence=None,
        table_confidence=None,
        text="Section 1 Staff must verify identity.",
    )

    assert result["quality_bucket"] == "reliable"
    assert result["flags"] == []
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests/test_extraction_quality_service.py -q
```

Expected: fail because service does not exist.

- [ ] **Step 3: Implement service**

Create `backend/app/services/extraction_quality_service.py`:

```python
def build_extraction_quality(
    *,
    extraction_confidence: float | None,
    ocr_confidence: float | None,
    table_confidence: float | None,
    text: str | None,
) -> dict:
    flags = []
    if not (text or "").strip():
        flags.append("empty_text")
    if extraction_confidence is not None and extraction_confidence < 0.75:
        flags.append("low_extraction_confidence")
    if ocr_confidence is not None and ocr_confidence < 0.70:
        flags.append("low_ocr_confidence")
    if table_confidence is not None and table_confidence < 0.75:
        flags.append("low_table_confidence")

    if "empty_text" in flags or "low_ocr_confidence" in flags or "low_table_confidence" in flags:
        quality_bucket = "review_required"
    elif flags:
        quality_bucket = "caution"
    else:
        quality_bucket = "reliable"

    return {"quality_bucket": quality_bucket, "flags": flags}
```

- [ ] **Step 4: Run quality tests**

Run:

```bash
PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests/test_extraction_quality_service.py -q
```

Expected: `3 passed`.

## Task 2: Store Quality Flags In Review Records

**Files:**
- Modify: `backend/app/services/ingestion_service.py`
- Test: `backend/tests/test_ingestion_structure.py`

- [ ] **Step 1: Add failing review-record test**

Add to `backend/tests/test_ingestion_structure.py`:

```python
def test_create_extraction_review_records_marks_low_ocr_review_required(session):
    from app.models.bank import Bank
    from app.models.document_intelligence import DocumentExtractionPage
    from app.services.ingestion_service import create_extraction_review_records
    from sqlmodel import select

    bank = Bank(name="Quality Bank", code="QB01")
    session.add(bank)
    session.commit()
    session.refresh(bank)

    create_extraction_review_records(
        session,
        bank_id=bank.id,
        document_id=999,
        pages=[{"page_number": 1, "text": "Noisy OCR", "extraction_confidence": 0.82, "ocr_confidence": 0.45}],
    )

    record = session.exec(select(DocumentExtractionPage).where(DocumentExtractionPage.document_id == 999)).first()
    assert record.review_status == "pending"
    assert "low_ocr_confidence" in record.flags_json
```

If this project does not expose a shared `session` fixture in this file, create the setup following existing SQLModel test fixtures in `backend/tests/test_document_intelligence_service.py`.

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests/test_ingestion_structure.py::test_create_extraction_review_records_marks_low_ocr_review_required -q
```

Expected: fail because quality flags are not added.

- [ ] **Step 3: Add quality flags to review records**

In `create_extraction_review_records`, import:

```python
from .extraction_quality_service import build_extraction_quality
```

Before creating each `DocumentExtractionPage`, compute:

```python
quality = build_extraction_quality(
    extraction_confidence=page.get("extraction_confidence"),
    ocr_confidence=page.get("ocr_confidence"),
    table_confidence=page.get("table_confidence"),
    text=page.get("text"),
)
```

Set:

```python
flags_json=json.dumps(quality["flags"]),
review_status="pending" if quality["quality_bucket"] == "review_required" else "verified",
```

- [ ] **Step 4: Run ingestion review test**

Run:

```bash
PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests/test_ingestion_structure.py::test_create_extraction_review_records_marks_low_ocr_review_required -q
```

Expected: pass.

## Task 3: Preserve Table Structure Metadata

**Files:**
- Modify: `backend/app/services/ingestion_service.py`
- Test: `backend/tests/test_ingestion_structure.py`

- [ ] **Step 1: Add failing Excel metadata test**

Extend `test_extract_xlsx_preserves_sheet_tables_merges_and_formulas`:

```python
assert pages[0]["table_metadata"]["sheet_name"] == "Loan Pipeline"
assert pages[0]["table_metadata"]["merged_ranges"] == ["A1:C1"]
assert pages[0]["table_metadata"]["tables"] == [{"name": "LoanTable", "ref": "A2:C3"}]
assert "C3" in pages[0]["table_metadata"]["formula_cells"]
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests/test_ingestion_structure.py::test_extract_xlsx_preserves_sheet_tables_merges_and_formulas -q
```

Expected: fail because `table_metadata` is absent.

- [ ] **Step 3: Add table metadata to page payload**

Add `table_metadata: dict | None = None` to `_page_payload` and include `"table_metadata": table_metadata`.

Inside `_extract_xlsx_pages`, build:

```python
merged_ranges = [str(cell_range) for cell_range in sheet.merged_cells.ranges]
tables_metadata = []
for name, table in sheet.tables.items():
    ref = getattr(table, "ref", table)
    tables_metadata.append({"name": name, "ref": str(ref)})
formula_cells = {}
```

When a formula is found:

```python
formula_cells[cell.coordinate] = {"formula": cell.value, "cached": value}
```

Pass:

```python
table_metadata={
    "sheet_name": sheet.title,
    "dimension": sheet.calculate_dimension(),
    "merged_ranges": merged_ranges,
    "tables": tables_metadata,
    "formula_cells": formula_cells,
}
```

- [ ] **Step 4: Run Excel metadata test**

Run:

```bash
PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests/test_ingestion_structure.py::test_extract_xlsx_preserves_sheet_tables_merges_and_formulas -q
```

Expected: pass.

## Task 4: Show Quality In OCR UI

**Files:**
- Modify: `frontend/src/pages/OcrExtraction.jsx`

- [ ] **Step 1: Locate OCR result rendering**

Run:

```bash
rg -n "ocr_confidence|table_confidence|extraction_confidence|pages" frontend/src/pages/OcrExtraction.jsx
```

Expected: find the result card or page list.

- [ ] **Step 2: Render confidence badges**

Add badge rendering near each page result:

```jsx
const confidenceBadge = (label, value) => {
  if (value === null || value === undefined) return null;
  const tone = value >= 0.75 ? 'emerald' : 'amber';
  return (
    <span className={`rounded border px-2 py-0.5 text-xs font-semibold ${
      tone === 'emerald'
        ? 'border-emerald-200 bg-emerald-50 text-emerald-700'
        : 'border-amber-200 bg-amber-50 text-amber-800'
    }`}>
      {label}: {Math.round(value * 100)}%
    </span>
  );
};
```

Use it for extraction, OCR, and table confidence values returned by the API.

- [ ] **Step 3: Run frontend build**

Run:

```bash
cd frontend && npm run build
```

Expected: build exits `0`.

## Final Verification

- [ ] Run backend tests:

```bash
PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests/test_extraction_quality_service.py backend/tests/test_ingestion_structure.py backend/tests/test_document_intelligence_service.py -q
```

- [ ] Run frontend build:

```bash
cd frontend && npm run build
```

- [ ] Run diff check:

```bash
git diff --check
```

