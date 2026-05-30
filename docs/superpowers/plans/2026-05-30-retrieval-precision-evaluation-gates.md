# Retrieval Precision And Evaluation Gates Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make LipiCore retrieval quality measurable before bank demos, pilots, embedding changes, chunking changes, prompt changes, or model route changes.

**Architecture:** Extend the existing RAG Evaluation Center instead of building a parallel evaluator. Add synthetic fixture documents, richer case fields, strict release-gate scoring, and CLI/API workflows that use the existing `evaluate_rag_cases` service and `/api/evaluations/rag` endpoint.

**Tech Stack:** FastAPI, SQLModel/PostgreSQL, pytest, existing RAG Evaluation Center, Qdrant search path, JSON seed packs.

---

## File Structure

- Create: `docs/evaluations/fixtures/customer-care-policy.md` synthetic policy fixture.
- Create: `docs/evaluations/fixtures/compliance-circular.md` synthetic circular fixture.
- Create: `docs/evaluations/fixtures/spreadsheet-policy-summary.md` synthetic table/spreadsheet fixture.
- Create: `docs/evaluations/bank-ready-rag-gate.json` release-gate evaluation payload.
- Create: `backend/tests/test_bank_ready_rag_gate_payload.py` static validation for gate payload shape.
- Modify: `backend/app/schemas/rag_evaluation.py` to add optional page/section/sheet expectations.
- Modify: `backend/app/services/rag_evaluation_service.py` to compute citation location recall.
- Modify: `frontend/src/pages/EvaluationCenter.jsx` to show release-gate fields and pass/fail state.
- Modify: `docs/evaluations/README.md` to document when the gate must be run.

## Task 1: Add Bank-Ready Evaluation Fixtures

**Files:**
- Create: `docs/evaluations/fixtures/customer-care-policy.md`
- Create: `docs/evaluations/fixtures/compliance-circular.md`
- Create: `docs/evaluations/fixtures/spreadsheet-policy-summary.md`

- [ ] **Step 1: Create customer care fixture**

Create `docs/evaluations/fixtures/customer-care-policy.md`:

```markdown
# Customer Care SOP

Section 2.1 Complaint Escalation
Customer complaints about failed ATM withdrawals must be escalated to the branch operations supervisor within one business day.

Section 2.2 Identity Verification
Staff must verify the customer's account number, registered mobile number, and one additional identity factor before discussing account-specific support.

Section 2.3 Unsupported Products
If a question concerns a product that the bank does not offer, staff must say the answer is not found in approved documents and escalate to the supervisor.
```

- [ ] **Step 2: Create compliance circular fixture**

Create `docs/evaluations/fixtures/compliance-circular.md`:

```markdown
# Compliance Circular 2026-01

Section 4 Regulatory Reporting
The Compliance Department must submit the quarterly suspicious transaction summary by the seventh calendar day after quarter end.

Section 5 Department Responsibility
Branch Operations must maintain supporting documents for all escalated suspicious transaction reports for seven years.

Section 6 Human Approval
AI-generated compliance notes are draft assistance only. A compliance officer must review and approve final regulatory interpretations.
```

- [ ] **Step 3: Create spreadsheet/table fixture**

Create `docs/evaluations/fixtures/spreadsheet-policy-summary.md`:

```markdown
# Sheet: Loan Exceptions

Workbook: Credit Controls.xlsx
Dimension: A1:D4
Table: LoanExceptionTable=A1:D4

Row 1: Department | Exception Type | Reviewer | Time Limit
Row 2: Credit Administration | Missing income document | Credit Risk | 2 business days
Row 3: Branch Operations | Expired KYC document | Compliance | 1 business day
Row 4: Recovery | Collateral valuation mismatch | Credit Committee | 5 business days
```

- [ ] **Step 4: Verify files are present**

Run:

```bash
test -f docs/evaluations/fixtures/customer-care-policy.md
test -f docs/evaluations/fixtures/compliance-circular.md
test -f docs/evaluations/fixtures/spreadsheet-policy-summary.md
```

Expected: exit code `0`.

## Task 2: Add Gate Payload And Static Validation

**Files:**
- Create: `docs/evaluations/bank-ready-rag-gate.json`
- Create: `backend/tests/test_bank_ready_rag_gate_payload.py`

- [ ] **Step 1: Create gate payload**

Create `docs/evaluations/bank-ready-rag-gate.json`:

```json
{
  "cases": [
    {
      "id": "customer-care-complaint-escalation",
      "question": "When should a failed ATM withdrawal complaint be escalated?",
      "expected_source_titles": ["Customer Care SOP"],
      "required_citation_terms": ["Section 2.1", "one business day", "branch operations supervisor"],
      "required_answer_terms": ["one business day", "supervisor"],
      "expected_section_labels": ["Section 2.1"],
      "source_required": true,
      "citation_required": true
    },
    {
      "id": "compliance-quarterly-reporting",
      "question": "Who submits the quarterly suspicious transaction summary and when?",
      "expected_source_titles": ["Compliance Circular 2026-01"],
      "required_citation_terms": ["Section 4", "Compliance Department", "seventh calendar day"],
      "required_answer_terms": ["Compliance Department", "seventh calendar day"],
      "expected_section_labels": ["Section 4"],
      "source_required": true,
      "citation_required": true
    },
    {
      "id": "loan-exception-expired-kyc",
      "question": "In the loan exception sheet, who reviews expired KYC document exceptions?",
      "expected_source_titles": ["Credit Controls.xlsx", "Loan Exceptions"],
      "required_citation_terms": ["Expired KYC document", "Compliance", "1 business day"],
      "required_answer_terms": ["Compliance", "1 business day"],
      "expected_section_labels": ["Sheet: Loan Exceptions"],
      "source_required": true,
      "citation_required": true
    },
    {
      "id": "unsupported-product-refusal",
      "question": "What is the customer care policy for crypto wallet chargebacks?",
      "expected_not_found": true,
      "source_required": false,
      "citation_required": false,
      "no_general_policy_advice": true
    }
  ]
}
```

- [ ] **Step 2: Write failing static validation test**

Create `backend/tests/test_bank_ready_rag_gate_payload.py`:

```python
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
GATE_PATH = REPO_ROOT / "docs" / "evaluations" / "bank-ready-rag-gate.json"


def test_bank_ready_rag_gate_payload_has_required_cases():
    payload = json.loads(GATE_PATH.read_text())
    case_ids = {case["id"] for case in payload["cases"]}

    assert {
        "customer-care-complaint-escalation",
        "compliance-quarterly-reporting",
        "loan-exception-expired-kyc",
        "unsupported-product-refusal",
    } <= case_ids


def test_bank_ready_rag_gate_source_cases_have_location_expectations():
    payload = json.loads(GATE_PATH.read_text())
    source_cases = [case for case in payload["cases"] if case.get("source_required")]

    assert source_cases
    for case in source_cases:
        assert case["expected_source_titles"]
        assert case["required_citation_terms"]
        assert case["required_answer_terms"]
        assert case["expected_section_labels"]
```

- [ ] **Step 3: Run static validation**

Run:

```bash
PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests/test_bank_ready_rag_gate_payload.py -q
```

Expected before creating the JSON file: fail with `FileNotFoundError`. Expected after creating the JSON file: pass.

## Task 3: Extend Evaluation Schema For Location Expectations

**Files:**
- Modify: `backend/app/schemas/rag_evaluation.py`
- Test: `backend/tests/test_bank_ready_rag_gate_payload.py`

- [ ] **Step 1: Add schema fields**

In `backend/app/schemas/rag_evaluation.py`, add these optional fields to the case model:

```python
expected_page_numbers: list[int] = []
expected_section_labels: list[str] = []
expected_chunk_indexes: list[int] = []
```

- [ ] **Step 2: Verify schema accepts the gate payload**

Extend `backend/tests/test_bank_ready_rag_gate_payload.py`:

```python
from app.schemas.rag_evaluation import RagEvaluationRequest


def test_bank_ready_rag_gate_payload_matches_api_schema():
    payload = json.loads(GATE_PATH.read_text())
    request = RagEvaluationRequest(**payload)

    assert len(request.cases) == 4
    assert request.cases[0].expected_section_labels == ["Section 2.1"]
```

- [ ] **Step 3: Run schema validation test**

Run:

```bash
PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests/test_bank_ready_rag_gate_payload.py::test_bank_ready_rag_gate_payload_matches_api_schema -q
```

Expected before schema change: fail because `expected_section_labels` is not preserved. Expected after schema change: pass.

## Task 4: Compute Citation Location Recall

**Files:**
- Modify: `backend/app/services/rag_evaluation_service.py`
- Modify: `backend/app/schemas/rag_evaluation.py`
- Test: `backend/tests/test_rag_evaluation.py`

- [ ] **Step 1: Write failing service test**

Add to `backend/tests/test_rag_evaluation.py`:

```python
def test_rag_evaluation_scores_expected_section_labels():
    from app.services.rag_evaluation_service import _score_location_recall

    sources = [
        {"document_title": "Customer Care SOP", "section_label": "Section 2.1", "page_number": 4},
        {"document_title": "Other", "section_label": "Section 9", "page_number": 20},
    ]

    assert _score_location_recall(
        sources=sources,
        expected_section_labels=["Section 2.1"],
        expected_page_numbers=[4],
        expected_chunk_indexes=[],
    ) == 1.0
```

- [ ] **Step 2: Implement scorer**

Add to `backend/app/services/rag_evaluation_service.py`:

```python
def _normalize_location(value) -> str:
    return " ".join(str(value or "").lower().split())


def _score_location_recall(
    *,
    sources: list[dict],
    expected_section_labels: list[str],
    expected_page_numbers: list[int],
    expected_chunk_indexes: list[int],
) -> float:
    expected = []
    expected.extend(("section", _normalize_location(label)) for label in expected_section_labels)
    expected.extend(("page", str(number)) for number in expected_page_numbers)
    expected.extend(("chunk", str(index)) for index in expected_chunk_indexes)
    if not expected:
        return 1.0

    observed = set()
    for source in sources or []:
        if source.get("section_label") or source.get("section_number"):
            observed.add(("section", _normalize_location(source.get("section_label") or source.get("section_number"))))
        if source.get("page_number") is not None:
            observed.add(("page", str(source.get("page_number"))))
        if source.get("chunk_index") is not None:
            observed.add(("chunk", str(source.get("chunk_index"))))

    matches = sum(1 for item in expected if item in observed)
    return matches / len(expected)
```

- [ ] **Step 3: Add result field**

In `backend/app/schemas/rag_evaluation.py`, add `location_recall: float = 1.0` to each result object and `location_recall_avg: float = 1.0` to summary.

- [ ] **Step 4: Wire service output**

In `evaluate_rag_cases`, compute `location_recall` for each case from returned sources and expected location fields. Include the per-case score and average in the response.

- [ ] **Step 5: Run evaluation tests**

Run:

```bash
PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests/test_rag_evaluation.py backend/tests/test_bank_ready_rag_gate_payload.py -q
```

Expected: all tests pass.

## Task 5: Add Frontend Gate Display

**Files:**
- Modify: `frontend/src/pages/EvaluationCenter.jsx`

- [ ] **Step 1: Add location recall score card**

In `EvaluationCenter.jsx`, add a score card next to existing source/citation/answer cards:

```jsx
<ScoreCard label="Location recall" value={summary ? pct(summary.location_recall_avg) : '—'} icon="pin_drop" tone="slate" />
```

- [ ] **Step 2: Show expected section/page fields in helper text**

Update the evaluation editor helper text:

```jsx
Use expected sources, section/page expectations, citation terms, and gate flags such as source_required, citation_required, and no_general_policy_advice.
```

- [ ] **Step 3: Run frontend build**

Run:

```bash
cd frontend && npm run build
```

Expected: Vite build exits `0`.

## Task 6: Document Release Gate

**Files:**
- Modify: `docs/evaluations/README.md`

- [ ] **Step 1: Add release gate section**

Add:

```markdown
## Bank-Ready Release Gate

Run `bank-ready-rag-gate.json` before demos, pilots, embedding changes, chunk-profile changes, prompt changes, model route changes, reranker changes, or major document-ingestion changes.

Minimum pass rules:

- Source recall average >= 0.85.
- Citation term recall average >= 0.80.
- Location recall average >= 0.75.
- Not-found cases must pass.
- No case may return general bank-policy advice when `no_general_policy_advice` is true.

Failures are product issues. Do not explain them away as demo variance.
```

- [ ] **Step 2: Verify docs contain gate**

Run:

```bash
rg -n "Bank-Ready Release Gate|Location recall|bank-ready-rag-gate" docs/evaluations/README.md
```

Expected: all three terms are found.

## Final Verification

- [ ] Run backend evaluation tests:

```bash
PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests/test_bank_ready_rag_gate_payload.py backend/tests/test_rag_evaluation.py backend/tests/test_evaluation_seed_packs.py -q
```

- [ ] Run frontend build:

```bash
cd frontend && npm run build
```

- [ ] Run whitespace check:

```bash
git diff --check
```

