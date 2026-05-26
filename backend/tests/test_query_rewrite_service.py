from app.models.chat import ChatMessage
from app.services import query_rewrite_service


def _message(role: str, content: str) -> ChatMessage:
    return ChatMessage(
        bank_id=1,
        session_id=1,
        user_id=1,
        role=role,
        content=content,
    )


def test_source_lookup_follow_up_is_rewritten_with_previous_subject(monkeypatch):
    history = [
        _message("user", "tell me about banking offence"),
        _message("assistant", "Banking offences include unauthorized banking activity."),
    ]

    def fake_call_llm(prompt: str) -> str:
        assert "tell me about banking offence" in prompt
        assert "quote me exact policy" in prompt
        return '{"query":"quote me exact policy about banking offence"}'

    monkeypatch.setattr(query_rewrite_service, "call_llm", fake_call_llm)

    rewritten = query_rewrite_service.rewrite_query_for_retrieval(
        "quote me exact policy",
        history,
    )

    assert rewritten == "quote me exact policy about banking offence"


def test_source_lookup_follow_up_falls_back_to_last_user_subject(monkeypatch):
    history = [
        _message("user", "tell me about banking offence"),
        _message("assistant", "Banking offences include unauthorized banking activity."),
    ]

    def fail_call_llm(_prompt: str) -> str:
        raise RuntimeError("model unavailable")

    monkeypatch.setattr(query_rewrite_service, "call_llm", fail_call_llm)

    rewritten = query_rewrite_service.rewrite_query_for_retrieval(
        "quote me exait policy",
        history,
    )

    assert rewritten == "quote me exait policy about banking offence"
