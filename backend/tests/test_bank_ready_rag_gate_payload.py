import json
from pathlib import Path

from app.schemas.rag_evaluation import RagEvaluationRequest


REPO_ROOT = Path(__file__).resolve().parents[2]
GATE_PATH = REPO_ROOT / "docs" / "evaluations" / "bank-ready-rag-gate.json"


def test_bank_ready_rag_gate_payload_has_required_cases():
    payload = json.loads(GATE_PATH.read_text())
    case_ids = {case["id"] for case in payload["cases"]}

    assert {
        "customer-care-complaint-escalation",
        "compliance-quarterly-reporting",
        "loan-exception-expired-kyc",
        "policy-clause-page-citation",
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
        assert any(
            case.get(key)
            for key in (
                "expected_section_labels",
                "expected_page_numbers",
                "expected_document_headings",
                "expected_clause_numbers",
                "expected_printed_page_numbers",
            )
        )


def test_bank_ready_rag_gate_payload_matches_api_schema():
    payload = json.loads(GATE_PATH.read_text())
    request = RagEvaluationRequest(**payload)
    clause_case = next(
        (case for case in request.cases if case.id == "policy-clause-page-citation"),
        None,
    )

    assert len(request.cases) == 6
    assert request.cases[0].expected_section_labels == ["Section 2.1"]
    assert clause_case is not None
    assert clause_case.expected_clause_numbers == ["Clause 5.1(a)"]
