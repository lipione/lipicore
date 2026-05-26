from types import SimpleNamespace

from app.api import chat as chat_api


def test_greeting_does_not_trigger_document_retrieval_status():
    assert chat_api._should_skip_document_retrieval("helo")
    assert not chat_api._should_attempt_document_retrieval(
        message="helo",
        mode="ask_knowledge",
        active_document_ids=[],
        has_image=False,
    )
    assert not chat_api.should_show_document_search_status(
        active_document_ids=[],
        mode="ask_knowledge",
        has_image=False,
        message="helo",
    )


def test_stream_context_uses_bounded_top_results():
    results = [
        SimpleNamespace(score=1.0 - (index / 100), payload={"document_id": index})
        for index in range(chat_api.MAX_CONTEXT_RESULTS + 5)
    ]

    bounded = chat_api._document_context_results(results)

    assert bounded == results[:chat_api.MAX_CONTEXT_RESULTS]
