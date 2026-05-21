import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_bank_evaluation_seed_packs_are_valid_gate_payloads():
    seed_paths = sorted((REPO_ROOT / "docs" / "evaluations").glob("*-rag-seed.json"))

    assert {path.name for path in seed_paths} >= {
        "customer-care-rag-seed.json",
        "branch-operations-rag-seed.json",
        "compliance-circular-rag-seed.json",
        "product-faq-rag-seed.json",
        "lending-policy-rag-seed.json",
    }

    for path in seed_paths:
        payload = json.loads(path.read_text())
        assert payload["name"]
        assert 0 <= payload["pass_threshold"] <= 1
        assert payload["user_role"]
        assert payload["cases"]
        for case in payload["cases"]:
            assert case["id"]
            assert case["question"]
            assert any(
                case.get(key)
                for key in (
                    "source_required",
                    "citation_required",
                    "not_found_required",
                    "expect_not_found",
                    "no_general_policy_advice",
                    "required_answer_terms",
                    "required_citation_terms",
                )
            )
