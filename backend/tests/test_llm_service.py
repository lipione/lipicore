import pytest

from app.services import llm_service


@pytest.mark.asyncio
async def test_async_llm_falls_back_to_streaming_when_non_streaming_response_is_empty(monkeypatch):
    class FakeLease:
        profile = type(
            "Profile",
            (),
            {
                "api_base": "http://fake-llm.local",
                "api_key": "test",
                "model": "fake-model",
                "max_tokens": 256,
                "timeout_seconds": 1,
            },
        )()

    class FakeReservation:
        async def __aenter__(self):
            return FakeLease()

        async def __aexit__(self, *_args):
            return False

    class FakePostResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"choices": [{"message": {"content": ""}}]}

    class FakeStreamResponse:
        status_code = 200

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return False

        async def aiter_lines(self):
            yield 'data: {"choices":[{"delta":{"content":"Recovered "}}]}'
            yield 'data: {"choices":[{"delta":{"content":"answer."}}]}'
            yield "data: [DONE]"

    class FakeAsyncClient:
        def __init__(self, *_args, **_kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return False

        async def post(self, *_args, **_kwargs):
            return FakePostResponse()

        def stream(self, *_args, **_kwargs):
            return FakeStreamResponse()

    monkeypatch.setattr(llm_service, "reserve_model", lambda **_kwargs: FakeReservation())
    monkeypatch.setattr(llm_service, "model_fallback_keys", lambda _model_name: ["fast"])
    monkeypatch.setattr(llm_service.httpx, "AsyncClient", FakeAsyncClient)

    answer = await llm_service.async_call_llm_a("Say hello", user_id=1, role="staff_user", model_name="fast")

    assert answer == "Recovered answer."
