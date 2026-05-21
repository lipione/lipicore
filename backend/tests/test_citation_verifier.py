from app.services.citation_verifier import verify_answer_against_sources


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
    assert result["status"] == "partially_supported"
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
