from app.services.citation_verifier import verify_answer_against_sources


def test_verifier_marks_supported_when_all_claims_overlap_sources():
    answer = "Complaints must be escalated within one business day."
    sources = [
        {
            "passage": "Customer complaints must be escalated within one business day to the branch supervisor."
        }
    ]

    result = verify_answer_against_sources(answer=answer, sources=sources)

    assert result["status"] == "supported"
    assert result["trust_label"] == "source_supported"
    assert result["unsupported_sentence_count"] == 0


def test_verifier_marks_unsupported_when_answer_adds_unsourced_claim():
    answer = "Complaints must be escalated within one business day. The customer must receive NPR 500 compensation."
    sources = [
        {
            "passage": "Customer complaints must be escalated within one business day to the branch supervisor."
        }
    ]

    result = verify_answer_against_sources(answer=answer, sources=sources, min_overlap=0.35)

    assert result["status"] in {"partially_supported", "unsupported"}
    assert result["trust_label"] in {"partially_source_supported", "not_source_supported"}
    assert "NPR 500 compensation" in " ".join(result["unsupported_sentences"])


def test_citation_verifier_can_use_nli_stage_to_reject_contradiction():
    calls = []

    def fake_nli(premise, hypothesis):
        calls.append({"premise": premise, "hypothesis": hypothesis})
        return {"label": "contradiction", "score": 0.94}

    result = verify_answer_against_sources(
        answer="Staff must escalate expired-source answers to the document owner.",
        sources=[
            {
                "passage": "Staff must escalate expired-source answers to the supervisor, not the document owner."
            }
        ],
        min_overlap=0.2,
        nli_enabled=True,
        nli_predictor=fake_nli,
    )

    assert calls
    assert result["status"] == "unsupported"
    assert result["trust_label"] == "not_source_supported"
    assert result["verification_stage"] == "lexical+nli"
    assert result["nli_checked_sentence_count"] == 1
    assert result["unsupported_sentence_count"] == 1


def test_citation_verifier_keeps_lexical_stage_when_nli_disabled():
    def fake_nli(_premise, _hypothesis):
        raise AssertionError("NLI should not run when disabled")

    result = verify_answer_against_sources(
        answer="Staff must escalate expired-source answers to the supervisor.",
        sources=[
            {
                "passage": "Staff must escalate expired-source answers to the supervisor."
            }
        ],
        min_overlap=0.2,
        nli_enabled=False,
        nli_predictor=fake_nli,
    )

    assert result["status"] == "supported"
    assert result["verification_stage"] == "lexical"
    assert result["nli_checked_sentence_count"] == 0
