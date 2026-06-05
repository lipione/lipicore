# Policy Citation Fidelity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make LipiCore cite policy answers by document title, document heading, clause number, PDF page number, printed page number when available, and source status, while blocking final policy answers when required citation fields are missing.

**Status:** Completed on 2026-06-03. The checklist below is the original implementation recipe retained for auditability.

**Architecture:** Extract citation metadata during ingestion, persist it on `DocumentChunk`, copy it into Qdrant payloads, return it through RAG sources, and render it in chat/evaluation UI. Keep `page_number` as the existing PDF page field for backward compatibility and add explicit `pdf_page_number` aliases in source payloads.

**Tech Stack:** FastAPI, SQLModel, Alembic, Qdrant payload metadata, pytest, React/Vite, existing LipiCore RAG and source trust components.

---

## Requirements

- Policy answers must cite document title, document heading, clause number, PDF page number, printed page number when available, effective dates, and source status.
- `DocumentChunk.page_number` remains the stored PDF page number.
- New chunk fields: `printed_page_number`, `document_heading`, `clause_number`, `citation_confidence`, `citation_incomplete_reasons_json`.
- RAG source payloads must expose both `page_number` and `pdf_page_number`.
- If a policy, circular, directive, procedure, SOP, law, act, or compliance answer lacks heading, clause, or PDF page, LipiCore returns a citation-incomplete review response instead of a final answer.
- Printed page number is optional; when present, it must appear beside the PDF page number.
- Existing non-policy Q&A behavior must remain compatible with old `page_number` and `section_label` fields.

## File Structure

- Create `backend/app/services/policy_citation_metadata.py`: focused extraction helpers for printed page, heading, clause, and completeness checks.
- Create `backend/tests/test_policy_citation_metadata.py`: unit tests for citation metadata extraction and completeness.
- Modify `backend/app/models/document.py`: add citation metadata columns to `DocumentChunk`.
- Create `backend/alembic/versions/022_policy_citation_metadata.py`: migration for new chunk columns.
- Modify `backend/app/services/ingestion_service.py`: enrich indexable chunks, database chunk records, and Qdrant payloads with citation metadata.
- Modify `backend/app/services/rag_service.py`: propagate metadata through vector, keyword, FTS, source formatting, context prompts, and policy citation gating.
- Modify `backend/app/schemas/rag_evaluation.py` and `backend/app/services/rag_evaluation_service.py`: evaluate clause, heading, and printed page recall.
- Modify `backend/app/api/documents.py`: expose citation metadata in source passage viewer responses and add a backfill endpoint for approved documents.
- Create `backend/app/services/policy_citation_backfill_service.py`: re-extract citation metadata for existing chunks and update Qdrant payloads.
- Modify `frontend/src/components/trust/SourceMetadataStrip.jsx`: render PDF page, printed page, heading, clause, effective dates, source status, and citation completeness.
- Modify `frontend/src/components/chat/SourceEvidencePanel.jsx`: improve source location strings and source viewer metadata.
- Modify `frontend/src/components/chat/SourceCards.jsx`: include concise clause/page citation labels.
- Modify `frontend/src/pages/EvaluationCenter.jsx`: surface new citation metadata in evaluation source cards.

---

### Task 1: Citation Metadata Extractor

**Files:**
- Create: `backend/app/services/policy_citation_metadata.py`
- Create: `backend/tests/test_policy_citation_metadata.py`

- [ ] **Step 1: Write failing extraction tests**

Create `backend/tests/test_policy_citation_metadata.py`:

```python
from app.services.policy_citation_metadata import (
    build_citation_metadata,
    citation_is_complete_for_policy,
    extract_clause_number,
    extract_document_heading,
    extract_printed_page_number,
)


def test_extracts_policy_heading_clause_and_printed_page_number():
    text = """
    Credit Policy 2024
    Chapter 5: SME Lending
    Clause 5.1(a) Secured SME DSR Limit
    For secured SME loans, debt service ratio must not exceed 60%.

    Page 38
    """

    assert extract_document_heading(text) == "Chapter 5: SME Lending"
    assert extract_clause_number(text) == "Clause 5.1(a)"
    assert extract_printed_page_number(text) == "38"


def test_build_citation_metadata_marks_complete_policy_citation():
    metadata = build_citation_metadata(
        page={"page_number": 42, "text": "Chapter 5: SME Lending\nClause 5.1(a) DSR limit\nPage 38"},
        chunk_text="Clause 5.1(a) DSR limit for secured SME loans is 60%.",
        document_type="policy",
    )

    assert metadata["pdf_page_number"] == 42
    assert metadata["printed_page_number"] == "38"
    assert metadata["document_heading"] == "Chapter 5: SME Lending"
    assert metadata["clause_number"] == "Clause 5.1(a)"
    assert metadata["citation_confidence"] >= 0.9
    assert metadata["citation_incomplete_reasons"] == []
    assert citation_is_complete_for_policy(metadata)


def test_missing_clause_is_incomplete_for_policy_documents():
    metadata = build_citation_metadata(
        page={"page_number": 7, "text": "Chapter 2: Customer Service\nComplaints must be escalated."},
        chunk_text="Complaints must be escalated.",
        document_type="policy",
    )

    assert metadata["pdf_page_number"] == 7
    assert metadata["document_heading"] == "Chapter 2: Customer Service"
    assert metadata["clause_number"] is None
    assert "missing_clause_number" in metadata["citation_incomplete_reasons"]
    assert not citation_is_complete_for_policy(metadata)


def test_nepali_printed_page_and_clause_are_extracted():
    text = "परिच्छेद ३: कर्जा नीति\nदफा ३.२ कर्जा नवीकरण\nपृष्ठ १२"

    assert extract_document_heading(text) == "परिच्छेद ३: कर्जा नीति"
    assert extract_clause_number(text) == "दफा ३.२"
    assert extract_printed_page_number(text) == "१२"
```

- [ ] **Step 2: Run extractor tests to verify failure**

Run:

```bash
PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests/test_policy_citation_metadata.py -q
```

Expected: FAIL because `app.services.policy_citation_metadata` does not exist.

- [ ] **Step 3: Implement extraction helper**

Create `backend/app/services/policy_citation_metadata.py`:

```python
import re
from typing import Any


POLICY_DOCUMENT_TYPES = {
    "policy",
    "procedure",
    "manual",
    "compliance",
    "circular",
    "directive",
    "law",
    "act",
    "sop",
}

HEADING_RE = re.compile(
    r"^\s*((?:Chapter|Section|Part|Article)\s+[0-9]+(?:\.[0-9]+)*\s*[:\-–]?\s*[^\n]{0,120})\s*$|"
    r"^\s*((?:परिच्छेद|खण्ड)\s*[०-९0-9]+(?:[.\-][०-९0-9]+)*\s*[:\-–]?\s*[^\n]{0,120})\s*$",
    re.IGNORECASE | re.MULTILINE,
)
CLAUSE_RE = re.compile(
    r"\b((?:Clause|Section|Article|Rule)\s+[0-9]+(?:\.[0-9]+)*(?:\([a-zA-Z0-9]+\))?)\b|"
    r"\b((?:दफा|बुँदा)\s*[०-९0-9]+(?:[.\-][०-९0-9]+)*(?:\([^)]+\))?)",
    re.IGNORECASE,
)
PRINTED_PAGE_RE = re.compile(
    r"(?:^|\b)(?:page|pg\.?|p\.|printed\s+page)\s*[:#\-]?\s*([०-९0-9ivxlcdmIVXLCDM]+)\b|"
    r"(?:पृष्ठ|पेज)\s*[:#\-]?\s*([०-९0-9]+)",
    re.IGNORECASE,
)


def _first_group(match: re.Match[str] | None) -> str | None:
    if not match:
        return None
    for group in match.groups():
        if group:
            return " ".join(group.strip().split())[:160]
    return None


def _edge_text(text: str, line_count: int = 8) -> str:
    lines = [line.strip() for line in (text or "").splitlines() if line.strip()]
    if len(lines) <= line_count * 2:
        return "\n".join(lines)
    return "\n".join([*lines[:line_count], *lines[-line_count:]])


def extract_document_heading(text: str | None) -> str | None:
    return _first_group(HEADING_RE.search(text or ""))


def extract_clause_number(text: str | None) -> str | None:
    return _first_group(CLAUSE_RE.search((text or "")[:1600]))


def extract_printed_page_number(text: str | None) -> str | None:
    return _first_group(PRINTED_PAGE_RE.search(_edge_text(text or "")))


def is_policy_document_type(document_type: str | None) -> bool:
    return (document_type or "").strip().lower() in POLICY_DOCUMENT_TYPES


def citation_is_complete_for_policy(metadata: dict[str, Any]) -> bool:
    return not metadata.get("citation_incomplete_reasons")


def build_citation_metadata(*, page: dict[str, Any], chunk_text: str, document_type: str | None) -> dict[str, Any]:
    combined_text = "\n".join(
        value for value in (page.get("section_label"), chunk_text, page.get("text")) if value
    )
    pdf_page_number = page.get("page_number")
    document_heading = page.get("document_heading") or extract_document_heading(combined_text)
    clause_number = page.get("clause_number") or extract_clause_number(combined_text)
    printed_page_number = page.get("printed_page_number") or extract_printed_page_number(page.get("text") or chunk_text)

    reasons: list[str] = []
    if is_policy_document_type(document_type):
        if pdf_page_number is None:
            reasons.append("missing_pdf_page_number")
        if not document_heading:
            reasons.append("missing_document_heading")
        if not clause_number:
            reasons.append("missing_clause_number")

    present = sum(1 for value in (pdf_page_number, document_heading, clause_number, printed_page_number) if value)
    confidence = min(1.0, 0.25 + (present * 0.2) + (0.15 if not reasons else 0.0))

    return {
        "pdf_page_number": pdf_page_number,
        "printed_page_number": printed_page_number,
        "document_heading": document_heading,
        "clause_number": clause_number,
        "citation_confidence": round(confidence, 2),
        "citation_incomplete_reasons": reasons,
    }
```

- [ ] **Step 4: Run extractor tests to verify pass**

Run:

```bash
PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests/test_policy_citation_metadata.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/policy_citation_metadata.py backend/tests/test_policy_citation_metadata.py
git commit -m "feat: extract policy citation metadata"
```

---

### Task 2: Persist Citation Metadata During Ingestion

**Files:**
- Modify: `backend/app/models/document.py`
- Create: `backend/alembic/versions/022_policy_citation_metadata.py`
- Modify: `backend/app/services/ingestion_service.py`
- Modify: `backend/tests/test_ingestion_structure.py`

- [ ] **Step 1: Write failing ingestion metadata test**

Append to `backend/tests/test_ingestion_structure.py`:

```python
def test_build_indexable_chunks_adds_policy_citation_metadata():
    chunks = build_indexable_chunks(
        [
            {
                "page_number": 42,
                "text": "Chapter 5: SME Lending\nClause 5.1(a) DSR limit\nFor secured loans DSR is 60%.\nPage 38",
            }
        ],
        document_type="policy",
    )

    assert chunks[0]["page_number"] == 42
    assert chunks[0]["pdf_page_number"] == 42
    assert chunks[0]["printed_page_number"] == "38"
    assert chunks[0]["document_heading"] == "Chapter 5: SME Lending"
    assert chunks[0]["clause_number"] == "Clause 5.1(a)"
    assert chunks[0]["citation_incomplete_reasons"] == []
```

- [ ] **Step 2: Run ingestion test to verify failure**

Run:

```bash
PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests/test_ingestion_structure.py::test_build_indexable_chunks_adds_policy_citation_metadata -q
```

Expected: FAIL because `pdf_page_number`, `printed_page_number`, `document_heading`, and `clause_number` are not returned.

- [ ] **Step 3: Add citation fields to `DocumentChunk`**

Modify `backend/app/models/document.py` inside `DocumentChunk` after `page_number`:

```python
    printed_page_number: Optional[str] = None
    document_heading: Optional[str] = None
    clause_number: Optional[str] = None
    citation_confidence: Optional[float] = None
    citation_incomplete_reasons_json: str = "[]"
```

- [ ] **Step 4: Add Alembic migration**

Create `backend/alembic/versions/022_policy_citation_metadata.py`:

```python
"""add policy citation metadata to document chunks

Revision ID: 022
Revises: 021
Create Date: 2026-06-03
"""

from alembic import op
import sqlalchemy as sa


revision = "022"
down_revision = "021"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("documentchunk", sa.Column("printed_page_number", sa.String(), nullable=True))
    op.add_column("documentchunk", sa.Column("document_heading", sa.String(), nullable=True))
    op.add_column("documentchunk", sa.Column("clause_number", sa.String(), nullable=True))
    op.add_column("documentchunk", sa.Column("citation_confidence", sa.Float(), nullable=True))
    op.add_column(
        "documentchunk",
        sa.Column("citation_incomplete_reasons_json", sa.String(), nullable=False, server_default="[]"),
    )


def downgrade():
    op.drop_column("documentchunk", "citation_incomplete_reasons_json")
    op.drop_column("documentchunk", "citation_confidence")
    op.drop_column("documentchunk", "clause_number")
    op.drop_column("documentchunk", "document_heading")
    op.drop_column("documentchunk", "printed_page_number")
```

- [ ] **Step 5: Enrich chunks and Qdrant payloads**

Modify `backend/app/services/ingestion_service.py`.

Add import:

```python
from .policy_citation_metadata import build_citation_metadata
```

Inside `build_indexable_chunks`, before `indexable_chunks.append`, add:

```python
            citation = build_citation_metadata(
                page=page,
                chunk_text=chunk_text,
                document_type=document_type,
            )
```

Extend the chunk dict:

```python
                "pdf_page_number": citation["pdf_page_number"],
                "printed_page_number": citation["printed_page_number"],
                "document_heading": citation["document_heading"],
                "clause_number": citation["clause_number"],
                "citation_confidence": citation["citation_confidence"],
                "citation_incomplete_reasons": citation["citation_incomplete_reasons"],
```

Extend `DocumentChunk(...)` in `process_document`:

```python
                    printed_page_number=chunk.get("printed_page_number"),
                    document_heading=chunk.get("document_heading"),
                    clause_number=chunk.get("clause_number"),
                    citation_confidence=chunk.get("citation_confidence"),
                    citation_incomplete_reasons_json=json.dumps(chunk.get("citation_incomplete_reasons", [])),
```

Extend the Qdrant payload:

```python
                        "pdf_page_number": chunk["page_number"],
                        "printed_page_number": chunk.get("printed_page_number"),
                        "document_heading": chunk.get("document_heading"),
                        "clause_number": chunk.get("clause_number"),
                        "citation_confidence": chunk.get("citation_confidence"),
                        "citation_incomplete_reasons": chunk.get("citation_incomplete_reasons", []),
```

- [ ] **Step 6: Run ingestion tests**

Run:

```bash
PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests/test_ingestion_structure.py backend/tests/test_policy_citation_metadata.py -q
```

Expected: PASS.

- [ ] **Step 7: Verify migration head**

Run:

```bash
cd backend && PYTHONPATH=. .venv/bin/python -m alembic -c alembic.ini heads
```

Expected: `022 (head)`.

- [ ] **Step 8: Commit**

```bash
git add backend/app/models/document.py backend/alembic/versions/022_policy_citation_metadata.py backend/app/services/ingestion_service.py backend/tests/test_ingestion_structure.py
git commit -m "feat: persist policy citation metadata"
```

---

### Task 3: Propagate Citation Metadata Through Retrieval

**Files:**
- Modify: `backend/app/services/rag_service.py`
- Modify: `backend/tests/test_session_documents.py`

- [ ] **Step 1: Write failing RAG source metadata test**

Append to `backend/tests/test_session_documents.py`:

```python
def test_global_rag_returns_clause_heading_and_both_page_numbers(monkeypatch):
    def fake_embeddings(_texts):
        return [[0.1, 0.2, 0.3]]

    def fake_search_points(_query_vector, bank_id, limit=5, document_ids=None, session_id=None, document_scope=None, **_kwargs):
        return [
            SimpleNamespace(
                payload={
                    "document_id": 3,
                    "text": "Clause 5.1(a) says secured SME DSR must not exceed 60%.",
                    "page_number": 42,
                    "pdf_page_number": 42,
                    "printed_page_number": "38",
                    "document_heading": "Chapter 5: SME Lending",
                    "clause_number": "Clause 5.1(a)",
                    "section_label": "Clause 5.1(a)",
                    "chunk_index": 7,
                    "citation_confidence": 0.95,
                    "citation_incomplete_reasons": [],
                },
                score=0.95,
            )
        ]

    def fake_call_llm(prompt):
        assert "Heading: Chapter 5: SME Lending" in prompt
        assert "Clause: Clause 5.1(a)" in prompt
        assert "PDF page: 42" in prompt
        assert "Printed page: 38" in prompt
        return "Secured SME DSR must not exceed 60%."

    monkeypatch.setattr(rag_service, "generate_embeddings", fake_embeddings)
    monkeypatch.setattr(rag_service, "search_points", fake_search_points)
    monkeypatch.setattr(rag_service, "call_llm", fake_call_llm)

    with Session(engine) as session:
        bank = Bank(name="Citation Bank", code="CITE01")
        session.add(bank)
        session.commit()
        session.refresh(bank)
        user = User(email="citation@test.local", password_hash="x", name="Citation User", role="staff_user", bank_id=bank.id)
        session.add(user)
        session.commit()
        doc = Document(
            id=3,
            bank_id=bank.id,
            uploaded_by=user.id,
            title="Credit Policy 2024",
            file_name="credit-policy.pdf",
            file_type="pdf",
            file_path="credit-policy.pdf",
            document_type="policy",
            status="approved",
            version_state="approved",
            document_scope="global_knowledge",
        )
        session.add(doc)
        session.commit()

        answer, sources = rag_service.generate_rag_response(
            "What is the secured SME DSR limit?",
            bank.id,
            "staff_user",
            session,
        )

    assert "60%" in answer
    assert sources[0]["document_heading"] == "Chapter 5: SME Lending"
    assert sources[0]["clause_number"] == "Clause 5.1(a)"
    assert sources[0]["page_number"] == 42
    assert sources[0]["pdf_page_number"] == 42
    assert sources[0]["printed_page_number"] == "38"
    assert sources[0]["document_status"] == "approved"
    assert sources[0]["version_state"] == "approved"
    assert sources[0]["source_status"] == "approved/approved"
    assert sources[0]["citation_complete"] is True
```

- [ ] **Step 2: Run RAG metadata test to verify failure**

Run:

```bash
PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests/test_session_documents.py::test_global_rag_returns_clause_heading_and_both_page_numbers -q
```

Expected: FAIL because `_source_prefix` and `_build_source` do not include full citation metadata.

- [ ] **Step 3: Add payload extraction helpers to `rag_service.py`**

Modify `backend/app/services/rag_service.py`.

Add import:

```python
from .policy_citation_metadata import is_policy_document_type
```

Add helper:

```python
def _citation_reasons(payload: dict) -> list[str]:
    reasons = payload.get("citation_incomplete_reasons")
    if isinstance(reasons, list):
        return reasons
    if isinstance(reasons, str):
        try:
            parsed = json.loads(reasons or "[]")
        except json.JSONDecodeError:
            return []
        return parsed if isinstance(parsed, list) else []
    return []
```

- [ ] **Step 4: Extend source payloads**

In `_build_source`, add:

```python
    citation_reasons = _citation_reasons(payload)
```

Add fields to the returned dict:

```python
        "pdf_page_number": payload.get("pdf_page_number") or payload.get("page_number"),
        "printed_page_number": payload.get("printed_page_number"),
        "document_heading": payload.get("document_heading"),
        "clause_number": payload.get("clause_number"),
        "citation_confidence": payload.get("citation_confidence"),
        "citation_incomplete_reasons": citation_reasons,
        "citation_complete": not citation_reasons,
        "document_status": payload.get("document_status") or doc.status,
        "version_state": payload.get("version_state") or doc.version_state,
        "source_status": f"{payload.get('document_status') or doc.status}/{payload.get('version_state') or doc.version_state}",
```

- [ ] **Step 5: Include citation fields in keyword and FTS payloads**

In `_python_keyword_search`, add to payload:

```python
                "pdf_page_number": chunk.page_number,
                "printed_page_number": chunk.printed_page_number,
                "document_heading": chunk.document_heading,
                "clause_number": chunk.clause_number,
                "citation_confidence": chunk.citation_confidence,
                "citation_incomplete_reasons": _source_risk_flags_from_json(chunk.citation_incomplete_reasons_json),
```

In `_postgres_keyword_search`, select these columns:

```sql
            c.printed_page_number,
            c.document_heading,
            c.clause_number,
            c.citation_confidence,
            c.citation_incomplete_reasons_json,
```

Add to row payload:

```python
                "pdf_page_number": row["page_number"],
                "printed_page_number": row.get("printed_page_number"),
                "document_heading": row.get("document_heading"),
                "clause_number": row.get("clause_number"),
                "citation_confidence": row.get("citation_confidence"),
                "citation_incomplete_reasons": _source_risk_flags_from_json(row.get("citation_incomplete_reasons_json")),
```

- [ ] **Step 6: Upgrade source prefix**

Replace `_source_prefix` body with:

```python
def _source_prefix(doc: Document | None, payload: dict) -> str:
    title = (doc.title or doc.file_name) if doc else "Document"
    parts = [f"Document: {title}"]
    heading = payload.get("document_heading") or payload.get("section_label") or payload.get("section_number")
    if heading:
        parts.append(f"Heading: {heading}")
    clause = payload.get("clause_number")
    if clause:
        parts.append(f"Clause: {clause}")
    pdf_page = payload.get("pdf_page_number") or payload.get("page_number")
    if pdf_page is not None:
        parts.append(f"PDF page: {pdf_page}")
    printed_page = payload.get("printed_page_number")
    if printed_page:
        parts.append(f"Printed page: {printed_page}")
    if doc:
        parts.append(f"Status: {doc.status}/{doc.version_state}")
        if doc.effective_from:
            parts.append(f"Effective from: {doc.effective_from.isoformat()}")
        if doc.effective_to:
            parts.append(f"Effective until: {doc.effective_to.isoformat()}")
    chunk_index = payload.get("chunk_index")
    if chunk_index is not None:
        parts.append(f"Chunk: {chunk_index}")
    return "[" + "; ".join(parts) + "]"
```

- [ ] **Step 7: Strengthen policy prompt**

In `RAG_PROMPT_TEMPLATE`, replace the policy citation sentence with:

```python
When the answer comes from a policy, directive, circular, procedure, SOP, law, act, or compliance document, every key policy claim must cite: document title, heading, clause number, PDF page, printed page when available, effective dates when available, and source status.
```

- [ ] **Step 8: Run RAG metadata tests**

Run:

```bash
PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests/test_session_documents.py::test_global_rag_returns_clause_heading_and_both_page_numbers backend/tests/test_session_documents.py::test_global_rag_returns_cited_sources -q
```

Expected: PASS.

- [ ] **Step 9: Commit**

```bash
git add backend/app/services/rag_service.py backend/tests/test_session_documents.py
git commit -m "feat: return full policy citation metadata"
```

---

### Task 4: Block Final Policy Answers With Incomplete Citations

**Files:**
- Modify: `backend/app/services/rag_service.py`
- Modify: `backend/tests/test_session_documents.py`

- [ ] **Step 1: Write failing citation-gate test**

Append to `backend/tests/test_session_documents.py`:

```python
def test_policy_rag_blocks_answer_when_required_citation_fields_are_missing(monkeypatch):
    def fake_embeddings(_texts):
        return [[0.1, 0.2, 0.3]]

    def fake_search_points(_query_vector, bank_id, limit=5, document_ids=None, session_id=None, document_scope=None, **_kwargs):
        return [
            SimpleNamespace(
                payload={
                    "document_id": 12,
                    "text": "DSR must not exceed 60% for secured SME loans.",
                    "page_number": 42,
                    "chunk_index": 1,
                    "citation_incomplete_reasons": ["missing_document_heading", "missing_clause_number"],
                },
                score=0.95,
            )
        ]

    monkeypatch.setattr(rag_service, "generate_embeddings", fake_embeddings)
    monkeypatch.setattr(rag_service, "search_points", fake_search_points)
    monkeypatch.setattr(rag_service, "call_llm", lambda _prompt: "DSR must not exceed 60%.")

    with Session(engine) as session:
        bank = Bank(name="Incomplete Citation Bank", code="ICIT01")
        session.add(bank)
        session.commit()
        session.refresh(bank)
        user = User(email="incomplete@test.local", password_hash="x", name="Incomplete User", role="staff_user", bank_id=bank.id)
        session.add(user)
        session.commit()
        doc = Document(
            id=12,
            bank_id=bank.id,
            uploaded_by=user.id,
            title="Credit Policy",
            file_name="credit-policy.pdf",
            file_type="pdf",
            file_path="credit-policy.pdf",
            document_type="policy",
            status="approved",
            version_state="approved",
            document_scope="global_knowledge",
        )
        session.add(doc)
        session.commit()

        answer, sources = rag_service.generate_rag_response(
            "What is the SME DSR policy?",
            bank.id,
            "staff_user",
            session,
        )

    assert answer == rag_service.POLICY_CITATION_INCOMPLETE_RESPONSE
    assert sources == []
```

- [ ] **Step 2: Run gate test to verify failure**

Run:

```bash
PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests/test_session_documents.py::test_policy_rag_blocks_answer_when_required_citation_fields_are_missing -q
```

Expected: FAIL because incomplete policy citations are not blocked.

- [ ] **Step 3: Add incomplete-citation response and policy query detector**

Modify `backend/app/services/rag_service.py` near `NOT_FOUND_RESPONSE`:

```python
POLICY_CITATION_INCOMPLETE_RESPONSE = (
    "I found policy-like material, but the source citation is incomplete. "
    "Please send this to compliance review before relying on it."
)
POLICY_QUERY_TERMS = (
    "policy",
    "procedure",
    "sop",
    "circular",
    "directive",
    "rule",
    "clause",
    "section",
    "compliance",
    "nrb",
    "approve",
    "approval",
    "limit",
    "required",
    "must",
)
```

Add helpers:

```python
def _looks_like_policy_question(question: str | None) -> bool:
    normalized = (question or "").lower()
    return any(term in normalized for term in POLICY_QUERY_TERMS)


def _source_has_complete_policy_citation(source: dict) -> bool:
    return bool(
        source.get("document_heading")
        and source.get("clause_number")
        and (source.get("pdf_page_number") is not None or source.get("page_number") is not None)
        and not source.get("citation_incomplete_reasons")
    )


def _policy_sources_need_complete_citations(question: str, sources: list[dict]) -> bool:
    if not _looks_like_policy_question(question):
        return False
    return any(is_policy_document_type(source.get("document_type")) for source in sources)
```

- [ ] **Step 4: Apply citation gate in sync and async RAG**

In `generate_rag_response`, after `sources = _build_sources(high_confidence, db)` and before `answer = call_llm(prompt)`, add:

```python
    if _policy_sources_need_complete_citations(question, sources) and not any(
        _source_has_complete_policy_citation(source) for source in sources
    ):
        return POLICY_CITATION_INCOMPLETE_RESPONSE, []
```

In `async_generate_rag_response`, add the same block before `answer = await async_call_llm(...)`.

- [ ] **Step 5: Run citation-gate tests**

Run:

```bash
PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests/test_session_documents.py::test_policy_rag_blocks_answer_when_required_citation_fields_are_missing backend/tests/test_session_documents.py::test_global_rag_returns_clause_heading_and_both_page_numbers -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/rag_service.py backend/tests/test_session_documents.py
git commit -m "feat: gate policy answers on complete citations"
```

---

### Task 5: Backfill Existing Chunk Citation Metadata

**Files:**
- Create: `backend/app/services/policy_citation_backfill_service.py`
- Modify: `backend/app/api/documents.py`
- Create: `backend/tests/test_policy_citation_backfill.py`

- [ ] **Step 1: Write failing backfill test**

Create `backend/tests/test_policy_citation_backfill.py`:

```python
from sqlmodel import Session, SQLModel, select

from app.models.bank import Bank
from app.models.document import Document, DocumentChunk
from app.models.user import User
from app.services.policy_citation_backfill_service import backfill_document_citation_metadata
from test_main import engine


def test_backfill_updates_existing_policy_chunks_and_qdrant_payload(monkeypatch):
    updates = []

    def fake_update_points(document_id, bank_id, payload):
        updates.append({"document_id": document_id, "bank_id": bank_id, "payload": payload})

    monkeypatch.setattr(
        "app.services.policy_citation_backfill_service.update_points_by_document_payload",
        fake_update_points,
    )

    SQLModel.metadata.create_all(engine)
    try:
        with Session(engine) as session:
            bank = Bank(name="Backfill Bank", code="BACK01")
            session.add(bank)
            session.commit()
            session.refresh(bank)
            user = User(email="backfill@test.local", password_hash="x", name="Backfill User", role="bank_admin", bank_id=bank.id)
            session.add(user)
            session.commit()
            document = Document(
                bank_id=bank.id,
                uploaded_by=user.id,
                title="Credit Policy",
                file_name="credit.pdf",
                file_type="pdf",
                file_path="credit.pdf",
                document_type="policy",
                status="approved",
                version_state="approved",
            )
            session.add(document)
            session.commit()
            session.refresh(document)
            chunk = DocumentChunk(
                bank_id=bank.id,
                document_id=document.id,
                chunk_index=0,
                chunk_text="Chapter 5: SME Lending\nClause 5.1(a) DSR limit\nPage 38",
                page_number=42,
                qdrant_point_id="point-1",
            )
            session.add(chunk)
            session.commit()

            result = backfill_document_citation_metadata(session, document_id=document.id, bank_id=bank.id)
            refreshed = session.exec(select(DocumentChunk).where(DocumentChunk.document_id == document.id)).first()

        assert result["updated_chunks"] == 1
        assert refreshed.document_heading == "Chapter 5: SME Lending"
        assert refreshed.clause_number == "Clause 5.1(a)"
        assert refreshed.printed_page_number == "38"
        assert updates[0]["payload"]["citation_metadata_backfilled"] is True
    finally:
        SQLModel.metadata.drop_all(engine)
```

- [ ] **Step 2: Run backfill test to verify failure**

Run:

```bash
PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests/test_policy_citation_backfill.py -q
```

Expected: FAIL because the backfill service does not exist.

- [ ] **Step 3: Implement backfill service**

Create `backend/app/services/policy_citation_backfill_service.py`:

```python
import json

from sqlmodel import Session, select

from ..models.document import Document, DocumentChunk
from .policy_citation_metadata import build_citation_metadata
from .qdrant_service import update_points_by_document_payload


def backfill_document_citation_metadata(db: Session, *, document_id: int, bank_id: int) -> dict:
    document = db.get(Document, document_id)
    if not document or document.bank_id != bank_id:
        return {"document_id": document_id, "updated_chunks": 0}

    chunks = db.exec(
        select(DocumentChunk).where(
            DocumentChunk.document_id == document_id,
            DocumentChunk.bank_id == bank_id,
        )
    ).all()

    updated = 0
    for chunk in chunks:
        citation = build_citation_metadata(
            page={"page_number": chunk.page_number, "text": chunk.chunk_text},
            chunk_text=chunk.chunk_text,
            document_type=document.document_type,
        )
        chunk.printed_page_number = citation["printed_page_number"]
        chunk.document_heading = citation["document_heading"]
        chunk.clause_number = citation["clause_number"]
        chunk.citation_confidence = citation["citation_confidence"]
        chunk.citation_incomplete_reasons_json = json.dumps(citation["citation_incomplete_reasons"])
        db.add(chunk)
        updated += 1

    db.commit()
    update_points_by_document_payload(document_id, bank_id, {"citation_metadata_backfilled": True})
    return {"document_id": document_id, "updated_chunks": updated}
```

- [ ] **Step 4: Add admin endpoint**

In `backend/app/api/documents.py`, import:

```python
from ..services.policy_citation_backfill_service import backfill_document_citation_metadata
```

Add endpoint:

```python
@router.post("/{document_id}/citation-backfill")
def backfill_document_citations(
    document_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ("bank_admin", "super_admin", "compliance_officer", "document_reviewer"):
        raise HTTPException(status_code=403, detail="Not authorized to backfill citation metadata")
    document = db.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    if current_user.role != "super_admin" and document.bank_id != current_user.bank_id:
        raise HTTPException(status_code=403, detail="Document is outside your bank")
    return backfill_document_citation_metadata(db, document_id=document_id, bank_id=document.bank_id)
```

- [ ] **Step 5: Expose citation metadata in source viewer API**

In `backend/app/api/documents.py`, extend each chunk dict in `read_document_source`:

```python
                "pdf_page_number": chunk.page_number,
                "printed_page_number": chunk.printed_page_number,
                "document_heading": chunk.document_heading,
                "clause_number": chunk.clause_number,
                "citation_confidence": chunk.citation_confidence,
                "citation_incomplete_reasons_json": chunk.citation_incomplete_reasons_json,
```

- [ ] **Step 6: Run backfill tests**

Run:

```bash
PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests/test_policy_citation_backfill.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add backend/app/services/policy_citation_backfill_service.py backend/app/api/documents.py backend/tests/test_policy_citation_backfill.py
git commit -m "feat: backfill policy citation metadata"
```

---

### Task 6: Update Evaluation Gates for Clause, Heading, and Printed Page

**Files:**
- Modify: `backend/app/schemas/rag_evaluation.py`
- Modify: `backend/app/services/rag_evaluation_service.py`
- Modify: `backend/tests/test_rag_evaluation.py`
- Modify: `docs/evaluations/bank-ready-rag-gate.json`

- [ ] **Step 1: Write failing evaluation test**

Append to `backend/tests/test_rag_evaluation.py`:

```python
def test_rag_evaluation_scores_clause_heading_and_printed_page_locations():
    sources = [
        {
            "document_title": "Credit Policy 2024",
            "document_heading": "Chapter 5: SME Lending",
            "clause_number": "Clause 5.1(a)",
            "page_number": 42,
            "pdf_page_number": 42,
            "printed_page_number": "38",
        }
    ]

    score = rag_evaluation_service._score_location_recall(
        sources=sources,
        expected_section_labels=[],
        expected_page_numbers=[42],
        expected_chunk_indexes=[],
        expected_document_headings=["Chapter 5: SME Lending"],
        expected_clause_numbers=["Clause 5.1(a)"],
        expected_printed_page_numbers=["38"],
    )

    assert score == 1.0
```

- [ ] **Step 2: Run evaluation test to verify failure**

Run:

```bash
PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests/test_rag_evaluation.py::test_rag_evaluation_scores_clause_heading_and_printed_page_locations -q
```

Expected: FAIL because `_score_location_recall` does not accept the new expectation fields.

- [ ] **Step 3: Extend evaluation schema**

In `backend/app/schemas/rag_evaluation.py`, add fields to `RagEvaluationCase`:

```python
    expected_document_headings: list[str] = Field(default_factory=list)
    expected_clause_numbers: list[str] = Field(default_factory=list)
    expected_printed_page_numbers: list[str] = Field(default_factory=list)
```

- [ ] **Step 4: Extend evaluation scoring**

In `backend/app/services/rag_evaluation_service.py`, change `_score_location_recall` signature:

```python
def _score_location_recall(
    *,
    sources: list[dict[str, Any]],
    expected_section_labels: list[str],
    expected_page_numbers: list[int],
    expected_chunk_indexes: list[int],
    expected_document_headings: list[str] | None = None,
    expected_clause_numbers: list[str] | None = None,
    expected_printed_page_numbers: list[str] | None = None,
) -> float:
```

Add expected values:

```python
    expected.extend(("heading", _normalize_location(label)) for label in expected_document_headings or [])
    expected.extend(("clause", _normalize_location(number)) for number in expected_clause_numbers or [])
    expected.extend(("printed_page", _normalize_location(number)) for number in expected_printed_page_numbers or [])
```

Add observed values inside the source loop:

```python
        if source.get("document_heading"):
            observed.add(("heading", _normalize_location(source.get("document_heading"))))
        if source.get("clause_number"):
            observed.add(("clause", _normalize_location(source.get("clause_number"))))
        if source.get("printed_page_number"):
            observed.add(("printed_page", _normalize_location(source.get("printed_page_number"))))
```

In `evaluate_rag_cases`, read fields:

```python
        expected_document_headings = list(_value(case, "expected_document_headings", []) or [])
        expected_clause_numbers = list(_value(case, "expected_clause_numbers", []) or [])
        expected_printed_page_numbers = list(_value(case, "expected_printed_page_numbers", []) or [])
```

Pass them into `_score_location_recall`.

- [ ] **Step 5: Add one gate case to evaluation JSON**

Modify `docs/evaluations/bank-ready-rag-gate.json` by adding this case object to the cases array:

```json
{
  "id": "policy-clause-page-citation",
  "question": "What is the current secured SME DSR limit?",
  "expected_source_titles": ["Credit Policy 2024"],
  "expected_document_headings": ["Chapter 5: SME Lending"],
  "expected_clause_numbers": ["Clause 5.1(a)"],
  "expected_page_numbers": [42],
  "expected_printed_page_numbers": ["38"],
  "required_citation_terms": ["Credit Policy 2024", "Chapter 5: SME Lending", "Clause 5.1(a)", "page 42"],
  "source_required": true,
  "citation_required": true,
  "no_general_policy_advice": true
}
```

- [ ] **Step 6: Run evaluation tests**

Run:

```bash
PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests/test_rag_evaluation.py backend/tests/test_bank_ready_rag_gate_payload.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add backend/app/schemas/rag_evaluation.py backend/app/services/rag_evaluation_service.py backend/tests/test_rag_evaluation.py docs/evaluations/bank-ready-rag-gate.json
git commit -m "feat: evaluate policy citation locations"
```

---

### Task 7: Render Full Citations in the UI

**Files:**
- Modify: `frontend/src/components/trust/SourceMetadataStrip.jsx`
- Modify: `frontend/src/components/chat/SourceEvidencePanel.jsx`
- Modify: `frontend/src/components/chat/SourceCards.jsx`
- Modify: `frontend/src/pages/EvaluationCenter.jsx`

- [ ] **Step 1: Update metadata strip**

Replace the `items` array in `frontend/src/components/trust/SourceMetadataStrip.jsx` with:

```jsx
  const items = [
    source?.document_heading ? `Heading: ${source.document_heading}` : null,
    source?.clause_number ? `Clause: ${source.clause_number}` : null,
    source?.pdf_page_number || source?.page_number ? `PDF p.${source.pdf_page_number || source.page_number}` : null,
    source?.printed_page_number ? `Printed p.${source.printed_page_number}` : null,
    source?.source_status ? `Status ${source.source_status}` : null,
    source?.effective_from ? `Effective from ${source.effective_from.slice(0, 10)}` : null,
    source?.effective_to ? `Effective until ${source.effective_to.slice(0, 10)}` : null,
    source?.citation_complete === false ? 'Citation incomplete' : null,
    source?.citation_incomplete_reasons?.length ? source.citation_incomplete_reasons.join(', ') : null,
    confidenceLabel(source?.citation_confidence) ? `Citation ${confidenceLabel(source.citation_confidence)}` : null,
    confidenceLabel(source?.ocr_confidence) ? `OCR ${confidenceLabel(source.ocr_confidence)}` : null,
    confidenceLabel(source?.table_confidence) ? `Table ${confidenceLabel(source.table_confidence)}` : null,
    source?.citation_verification ? `Answer ${source.citation_verification}` : null,
  ].filter(Boolean);
```

- [ ] **Step 2: Update source location string**

In `frontend/src/components/chat/SourceEvidencePanel.jsx`, replace `sourceLocation` with:

```jsx
function sourceLocation(source) {
  const parts = [];
  if (source.document_heading) parts.push(source.document_heading);
  if (source.clause_number) parts.push(source.clause_number);
  if (!source.document_heading && (source.section_label || source.section_number)) {
    parts.push(source.section_label || source.section_number);
  }
  if (source.pdf_page_number || source.page_number) parts.push(`PDF p.${source.pdf_page_number || source.page_number}`);
  if (source.printed_page_number) parts.push(`printed p.${source.printed_page_number}`);
  if (!parts.length && Number.isInteger(source.chunk_index)) parts.push(`chunk ${source.chunk_index + 1}`);
  return parts.join(' · ');
}
```

In the modal chunk header, replace `{chunk.page_number && <span>Page {chunk.page_number}</span>}` with:

```jsx
                {chunk.pdf_page_number || chunk.page_number ? <span>PDF page {chunk.pdf_page_number || chunk.page_number}</span> : null}
                {chunk.printed_page_number ? <span>Printed page {chunk.printed_page_number}</span> : null}
                {chunk.document_heading ? <span>{chunk.document_heading}</span> : null}
                {chunk.clause_number ? <span>{chunk.clause_number}</span> : null}
                {chunk.document_status && chunk.version_state ? <span>Status {chunk.document_status}/{chunk.version_state}</span> : null}
```

- [ ] **Step 3: Update compact source cards**

In `frontend/src/components/chat/SourceCards.jsx`, replace the label body after source title with:

```jsx
            {src.clause_number && <span className="text-slate-400 ml-0.5">[{src.clause_number}]</span>}
            {(src.pdf_page_number || src.page_number) && <span className="text-slate-400 ml-0.5">[PDF p.{src.pdf_page_number || src.page_number}]</span>}
            {src.printed_page_number && <span className="text-slate-400 ml-0.5">[printed p.{src.printed_page_number}]</span>}
```

- [ ] **Step 4: Update evaluation source card heading**

In `frontend/src/pages/EvaluationCenter.jsx`, replace source location text:

```jsx
                  {source.document_heading || source.section_label || source.section_number || 'Heading unknown'}
                  {source.clause_number ? ` · ${source.clause_number}` : ''}
                  {source.pdf_page_number || source.page_number ? ` · PDF p.${source.pdf_page_number || source.page_number}` : ''}
                  {source.printed_page_number ? ` · printed p.${source.printed_page_number}` : ''}
```

- [ ] **Step 5: Run frontend verification**

Run:

```bash
cd frontend && npm run lint
cd frontend && npm run build
```

Expected: lint exits with 0 errors and build exits 0. Existing E2E `no-console` warnings may remain.

- [ ] **Step 6: Browser smoke check**

With the dev server running, open:

```text
http://localhost:5173/login
```

Expected: login screen loads and browser console has 0 runtime errors from the modified source components.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/components/trust/SourceMetadataStrip.jsx frontend/src/components/chat/SourceEvidencePanel.jsx frontend/src/components/chat/SourceCards.jsx frontend/src/pages/EvaluationCenter.jsx
git commit -m "feat: show full policy citations in UI"
```

---

### Task 8: Final Verification

**Files:**
- Verify all modified backend, frontend, and evaluation files.

- [ ] **Step 1: Run focused backend tests**

Run:

```bash
PYTHONPATH=backend backend/.venv/bin/python -m pytest \
  backend/tests/test_policy_citation_metadata.py \
  backend/tests/test_ingestion_structure.py \
  backend/tests/test_session_documents.py \
  backend/tests/test_policy_citation_backfill.py \
  backend/tests/test_rag_evaluation.py \
  backend/tests/test_bank_ready_rag_gate_payload.py \
  -q
```

Expected: PASS.

- [ ] **Step 2: Run broader RAG/trust tests**

Run:

```bash
PYTHONPATH=backend backend/.venv/bin/python -m pytest \
  backend/tests/test_citation_verifier.py \
  backend/tests/test_chat_modes.py \
  backend/tests/test_document_governance_phase1.py \
  backend/tests/test_rag_evaluation.py \
  backend/tests/test_session_documents.py \
  -q
```

Expected: PASS.

- [ ] **Step 3: Run frontend checks**

Run:

```bash
cd frontend && npm run lint
cd frontend && npm run build
```

Expected: lint exits with 0 errors and build exits 0.

- [ ] **Step 4: Run migration check**

Run:

```bash
cd backend && PYTHONPATH=. .venv/bin/python -m alembic -c alembic.ini heads
```

Expected: `022 (head)`.

- [ ] **Step 5: Run whitespace check**

Run:

```bash
git diff --check -- backend frontend docs/evaluations
```

Expected: no output and exit code 0.

- [ ] **Step 6: Commit final verification note if execution changed docs**

If execution updates only implementation files and tests, no extra commit is needed. If execution updates evaluation docs after Task 6, commit them with:

```bash
git add docs/evaluations/bank-ready-rag-gate.json
git commit -m "test: require full policy citation gate"
```

---

## Self-Review

- Spec coverage: The plan covers clause number, document heading, PDF page, printed page, effective/status metadata propagation, incomplete citation gating, UI display, evaluation gates, and backfill.
- Placeholder scan: The plan contains no placeholder implementation steps; every code-changing task includes concrete snippets and verification commands.
- Type consistency: New backend names are consistent across extraction, `DocumentChunk`, Qdrant payloads, RAG source payloads, evaluation fields, and frontend source rendering.
