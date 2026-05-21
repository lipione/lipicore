from app.services.large_document_context_service import build_large_file_prompt, select_relevant_file_chunks


def test_select_relevant_file_chunks_keeps_late_matching_evidence():
    pages = [
        {
            "page_number": 1,
            "text": "General introduction. " + ("opening account details " * 300),
        },
        {
            "page_number": 48,
            "text": "Section 9.3 Dormant account reactivation requires branch manager approval and KYC refresh.",
        },
    ]

    chunks = select_relevant_file_chunks(
        pages=pages,
        question="What approval is needed for dormant account reactivation?",
        max_chars=1600,
    )

    combined = "\n".join(chunk["text"] for chunk in chunks)
    assert "Dormant account reactivation" in combined
    assert chunks[0]["page_number"] == 48


def test_build_large_file_prompt_reports_shortening_and_stays_under_budget():
    pages = [
        {"page_number": 1, "text": "Noise " * 2000},
        {"page_number": 12, "text": "Loan exception approval must be reviewed by Credit Risk."},
    ]

    prompt, metadata = build_large_file_prompt(
        file_name="large-policy.pdf",
        user_request="Who reviews loan exception approval?",
        pages=pages,
        context_window_tokens=1200,
        output_tokens=256,
    )

    assert "large-policy.pdf" in prompt
    assert "Loan exception approval must be reviewed by Credit Risk" in prompt
    assert "Content was shortened" in prompt
    assert metadata["shortened"] is True
    assert metadata["selected_chunks"] >= 1
    assert len(prompt) <= metadata["input_budget_chars"] + 1200
