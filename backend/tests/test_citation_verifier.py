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


def test_verifier_uses_semantic_matching_for_english_answer_against_nepali_sources():
    answer = "Customer complaints must be escalated within one business day."
    sources = [
        {
            "passage": "ग्राहकको गुनासो एक कार्यदिनभित्र सुपरवाइजरमा पठाउनुपर्छ।"
        }
    ]

    def fake_semantic_scorer(sentences: list[str], source_segments: list[str]) -> list[float]:
        assert source_segments
        return [0.82 for _ in sentences]

    result = verify_answer_against_sources(
        answer=answer,
        sources=sources,
        min_overlap=0.95,
        nli_enabled=False,
        semantic_enabled=True,
        semantic_threshold=0.8,
        semantic_scorer=fake_semantic_scorer,
        semantic_only_cross_lang=True,
    )

    assert result["status"] == "supported"
    assert result["verification_stage"] == "lexical+semantic"
    assert result["semantic_checked_sentence_count"] == 1
    assert result["semantic_supported_sentence_count"] == 1
    assert result["semantic_top_score"] == 0.82
    assert result["trust_label"] == "source_supported"


def test_verifier_falls_back_to_semantic_when_nli_does_not_support():
    answer = "Customer complaints must be escalated within one business day."
    sources = [
        {
            "passage": "ग्राहकको गुनासो एक कार्यदिनभित्र सुपरवाइजरमा पठाउनुपर्छ।"
        }
    ]

    def fake_nli(_premise, _hypothesis):
        return {"label": "contradiction", "score": 0.95}

    def fake_semantic_scorer(sentences: list[str], source_segments: list[str]) -> list[float]:
        return [0.83 for _ in sentences]

    result = verify_answer_against_sources(
        answer=answer,
        sources=sources,
        min_overlap=0.95,
        nli_enabled=True,
        nli_predictor=fake_nli,
        semantic_enabled=True,
        semantic_threshold=0.9,
        semantic_scorer=fake_semantic_scorer,
        semantic_only_cross_lang=True,
    )

    assert result["status"] == "unsupported"
    assert result["verification_stage"] == "hybrid"
    assert result["nli_checked_sentence_count"] == 1
    assert result["semantic_checked_sentence_count"] == 1
    assert result["semantic_supported_sentence_count"] == 0
    assert result["trust_label"] == "not_source_supported"
