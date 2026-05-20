import pytest
from pydantic import ValidationError

from app.api.chat import (
    derive_answer_metadata,
    general_fallback_system_identity,
    mode_instruction,
    should_show_document_search_status,
)
from app.schemas.chat import ChatRequest


def test_chat_request_defaults_to_bank_knowledge_mode():
    request = ChatRequest(message="What is the loan policy?")

    assert request.mode == "ask_knowledge"


def test_chat_request_rejects_unknown_mode():
    with pytest.raises(ValidationError):
        ChatRequest(message="Draft a memo", mode="department_bot")


def test_mode_instruction_marks_drafts_as_non_policy_output():
    instruction = mode_instruction("draft")

    assert "draft" in instruction.lower()
    assert "not official bank policy" in instruction.lower()


def test_answer_metadata_marks_ask_knowledge_with_sources_as_official():
    metadata = derive_answer_metadata(
        mode="ask_knowledge",
        sources=[{"document_id": 1, "document_title": "Credit SOP"}],
        active_document_ids=[],
        answer="The policy says borrowers must submit documents.",
    )

    assert metadata["mode"] == "ask_knowledge"
    assert metadata["answer_type"] == "official_source_backed"
    assert metadata["source_count"] == 1
    assert metadata["requires_sources"] is False


def test_answer_metadata_marks_uploaded_file_answers():
    metadata = derive_answer_metadata(
        mode="analyze_file",
        sources=[{"document_id": 10, "document_title": "Uploaded Statement"}],
        active_document_ids=[10],
        answer="The statement shows three transactions.",
    )

    assert metadata["answer_type"] == "uploaded_file_answer"
    assert metadata["source_count"] == 1


def test_answer_metadata_marks_ask_knowledge_without_sources_as_general():
    metadata = derive_answer_metadata(
        mode="ask_knowledge",
        sources=[],
        active_document_ids=[],
        answer="Property insurance protects property against covered loss. Verify internal policy with a supervisor.",
    )

    assert metadata["answer_type"] == "general_answer"
    assert metadata["source_count"] == 0


def test_answer_metadata_marks_draft_without_sources_as_general():
    metadata = derive_answer_metadata(
        mode="draft",
        sources=[],
        active_document_ids=[],
        answer="Dear customer care team...",
    )

    assert metadata["answer_type"] == "general_answer"
    assert metadata["requires_sources"] is False


def test_answer_metadata_marks_hard_source_required_mode_without_sources_as_not_found():
    metadata = derive_answer_metadata(
        mode="compare",
        sources=[],
        active_document_ids=[],
        answer="I do not have enough approved information to answer.",
    )

    assert metadata["answer_type"] == "not_found"
    assert metadata["requires_sources"] is True


def test_general_fallback_warns_not_official_policy():
    instruction = general_fallback_system_identity("en", "ask_knowledge")

    assert "general knowledge only" in instruction
    assert "official bank policy" in instruction


def test_document_search_status_only_shows_when_document_search_is_expected():
    assert should_show_document_search_status(active_document_ids=[10], mode="draft", has_image=False) is True
    assert should_show_document_search_status(active_document_ids=[], mode="ask_knowledge", has_image=False) is True
    assert should_show_document_search_status(active_document_ids=[], mode="draft", has_image=False) is False
    assert should_show_document_search_status(active_document_ids=[10], mode="analyze_file", has_image=True) is False
