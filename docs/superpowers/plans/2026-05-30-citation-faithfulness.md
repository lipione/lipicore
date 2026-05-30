# Citation Faithfulness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make LipiCore answer badges reflect whether generated claims are actually supported by retrieved source passages.

**Architecture:** Keep the existing lexical citation verifier as the first pass and add deterministic sentence-level support metadata that downstream chat metadata, audit logs, and UI badges can consume. Do not add an external API dependency; advanced NLI can remain an optional offline/local model later.

**Tech Stack:** Python citation verifier, RAG/chat metadata, pytest, React trust badges.

---

## File Structure

- Modify: `backend/app/services/citation_verifier.py` to return sentence-level support details and a stable trust label.
- Modify: `backend/app/api/chat.py` to use trust labels in `derive_answer_metadata`.
- Modify: `backend/app/services/rag_evaluation_service.py` to score unsupported answers as failed citation cases.
- Modify: `frontend/src/pages/ChatAssistant.jsx` to render supported/partial/unsupported states.
- Test: `backend/tests/test_citation_verifier.py`
- Test: `backend/tests/test_chat_modes.py`
- Test: `backend/tests/test_rag_evaluation.py`

## Task 1: Stabilize Citation Verification Labels

**Files:**
- Modify: `backend/app/services/citation_verifier.py`
- Test: `backend/tests/test_citation_verifier.py`

- [ ] **Step 1: Add failing tests**

Add to `backend/tests/test_citation_verifier.py`:

```python
def test_verifier_marks_supported_when_all_claims_overlap_sources():
    from app.services.citation_verifier import verify_answer_against_sources

    answer = "Complaints must be escalated within one business day."
    sources = [{"passage": "Customer complaints must be escalated within one business day to the branch supervisor."}]

    result = verify_answer_against_sources(answer=answer, sources=sources)

    assert result["status"] == "supported"
    assert result["trust_label"] == "source_supported"
    assert result["unsupported_sentence_count"] == 0


def test_verifier_marks_unsupported_when_answer_adds_unsourced_claim():
    from app.services.citation_verifier import verify_answer_against_sources

    answer = "Complaints must be escalated within one business day. The customer must receive NPR 500 compensation."
    sources = [{"passage": "Customer complaints must be escalated within one business day to the branch supervisor."}]

    result = verify_answer_against_sources(answer=answer, sources=sources, min_overlap=0.35)

    assert result["status"] in {"partially_supported", "unsupported"}
    assert result["trust_label"] in {"partially_source_supported", "not_source_supported"}
    assert "NPR 500 compensation" in " ".join(result["unsupported_sentences"])
```

- [ ] **Step 2: Run tests to verify failure or current gap**

Run:

```bash
PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests/test_citation_verifier.py -q
```

Expected: new tests fail until `trust_label` and stricter status behavior exist.

- [ ] **Step 3: Add trust labels**

In `verify_answer_against_sources`, set:

```python
if not sources:
    trust_label = "no_sources"
elif unsupported_sentence_count == 0:
    trust_label = "source_supported"
elif supported_sentence_count > 0:
    trust_label = "partially_source_supported"
else:
    trust_label = "not_source_supported"
```

Add `trust_label` to the returned dict.

- [ ] **Step 4: Run verifier tests**

Run:

```bash
PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests/test_citation_verifier.py -q
```

Expected: pass.

## Task 2: Use Faithfulness In Chat Answer Metadata

**Files:**
- Modify: `backend/app/api/chat.py`
- Test: `backend/tests/test_chat_modes.py`

- [ ] **Step 1: Add failing metadata test**

Add to `backend/tests/test_chat_modes.py`:

```python
def test_answer_metadata_uses_citation_trust_label_for_unsupported_source():
    from app.api.chat import derive_answer_metadata

    metadata = derive_answer_metadata(
        mode="approved_knowledge",
        sources=[{"document_title": "Policy"}],
        active_document_ids=[],
        answer="Unsupported claim",
        citation_verification={"status": "partially_supported", "trust_label": "partially_source_supported"},
    )

    assert metadata["answer_type"] == "unsupported_source"
    assert metadata["trust_label"] == "partially_source_supported"
```

- [ ] **Step 2: Run metadata test to verify failure**

Run:

```bash
PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests/test_chat_modes.py::test_answer_metadata_uses_citation_trust_label_for_unsupported_source -q
```

Expected: fail because `trust_label` is not copied.

- [ ] **Step 3: Add trust label to metadata**

In `derive_answer_metadata`, add:

```python
trust_label = (citation_verification or {}).get("trust_label", "no_sources" if source_count == 0 else "source_unverified")
```

Return it:

```python
"trust_label": trust_label,
```

Keep existing `unsupported_source` answer type when status is `partially_supported` or trust label is not fully supported.

- [ ] **Step 4: Run chat mode tests**

Run:

```bash
PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests/test_chat_modes.py -q
```

Expected: pass.

## Task 3: Fail Evaluation Cases On Unsupported Source Claims

**Files:**
- Modify: `backend/app/services/rag_evaluation_service.py`
- Test: `backend/tests/test_rag_evaluation.py`

- [ ] **Step 1: Add failing evaluation test**

Add to `backend/tests/test_rag_evaluation.py`:

```python
def test_rag_evaluation_marks_partially_supported_answer_as_failed_when_citation_required():
    from app.services.rag_evaluation_service import _case_passed

    case = {
        "citation_required": True,
        "source_required": True,
    }
    result = {
        "source_recall": 1.0,
        "citation_term_recall": 1.0,
        "answer_term_recall": 1.0,
        "citation_verification": {"trust_label": "partially_source_supported"},
    }

    assert _case_passed(case, result) is False
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests/test_rag_evaluation.py::test_rag_evaluation_marks_partially_supported_answer_as_failed_when_citation_required -q
```

Expected: fail until helper exists or logic is updated.

- [ ] **Step 3: Implement pass/fail helper**

In `backend/app/services/rag_evaluation_service.py`, add or update:

```python
def _case_passed(case: dict, result: dict) -> bool:
    if case.get("expected_not_found"):
        return bool(result.get("expected_not_found_passed"))
    if case.get("source_required") and result.get("source_recall", 0) <= 0:
        return False
    if case.get("citation_required") and result.get("citation_term_recall", 0) <= 0:
        return False
    trust_label = (result.get("citation_verification") or {}).get("trust_label")
    if case.get("citation_required") and trust_label not in (None, "source_supported"):
        return False
    if case.get("no_general_policy_advice") and not result.get("no_general_policy_advice_passed", True):
        return False
    return True
```

Use `_case_passed` when setting each evaluation result's pass/fail field.

- [ ] **Step 4: Run evaluation tests**

Run:

```bash
PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests/test_rag_evaluation.py -q
```

Expected: pass.

## Task 4: Render Trust Labels In Chat UI

**Files:**
- Modify: `frontend/src/pages/ChatAssistant.jsx`

- [ ] **Step 1: Locate answer metadata rendering**

Run:

```bash
rg -n "answer_metadata|answer_type|citation_verification|trust" frontend/src/pages frontend/src/components
```

Expected: identify the chat answer metadata block.

- [ ] **Step 2: Add trust label copy**

Add a mapping near the component:

```jsx
const trustLabelCopy = {
  source_supported: 'Source supported',
  partially_source_supported: 'Partially source supported',
  not_source_supported: 'Not source supported',
  no_sources: 'No sources',
  source_unverified: 'Source unverified',
};
```

Render:

```jsx
{metadata?.trust_label && (
  <span className={`inline-flex items-center rounded px-2 py-0.5 text-xs font-semibold ${
    metadata.trust_label === 'source_supported'
      ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
      : 'bg-amber-50 text-amber-800 border border-amber-200'
  }`}>
    {trustLabelCopy[metadata.trust_label] || metadata.trust_label}
  </span>
)}
```

- [ ] **Step 3: Run frontend build**

Run:

```bash
cd frontend && npm run build
```

Expected: build exits `0`.

## Final Verification

- [ ] Run backend tests:

```bash
PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests/test_citation_verifier.py backend/tests/test_chat_modes.py backend/tests/test_rag_evaluation.py -q
```

- [ ] Run frontend build:

```bash
cd frontend && npm run build
```

- [ ] Run diff check:

```bash
git diff --check
```

