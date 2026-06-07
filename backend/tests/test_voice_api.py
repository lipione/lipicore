from types import SimpleNamespace

from sqlmodel import Session, SQLModel

from app.core.security import get_password_hash
from app.models.bank import Bank
from app.models.user import User
from test_main import client, engine, get_token


def setup_function():
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        bank = Bank(name="Voice Bank", code="VOICE01")
        session.add(bank)
        session.commit()
        session.refresh(bank)

        user = User(
            email="voice-staff@test.local",
            password_hash=get_password_hash("password"),
            name="Voice Staff",
            role="staff_user",
            bank_id=bank.id,
            is_active=True,
        )
        session.add(user)
        session.commit()


def teardown_function():
    SQLModel.metadata.drop_all(engine)


def test_voice_capabilities_include_private_nepali_and_english_stt():
    token = get_token("voice-staff@test.local")

    response = client.get(
        "/api/voice/capabilities",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["enabled"] is True
    assert payload["browser_fallback_enabled"] is False
    assert payload["max_upload_mb"] >= 1
    assert [language["code"] for language in payload["languages"]] == ["en", "ne-NP"]


def test_voice_transcribe_rejects_np_language_code():
    token = get_token("voice-staff@test.local")

    response = client.post(
        "/api/voice/transcribe",
        headers={"Authorization": f"Bearer {token}"},
        data={"language": "np"},
        files={"file": ("prompt.webm", b"audio-bytes", "audio/webm")},
    )

    assert response.status_code == 400
    assert "ne-NP" in response.json()["detail"]


def test_voice_transcribe_rejects_empty_audio_file():
    token = get_token("voice-staff@test.local")

    response = client.post(
        "/api/voice/transcribe",
        headers={"Authorization": f"Bearer {token}"},
        data={"language": "ne-NP"},
        files={"file": ("prompt.webm", b"", "audio/webm")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Audio file is empty"


def test_voice_transcribe_returns_private_stt_transcript(monkeypatch):
    token = get_token("voice-staff@test.local")

    async def fake_transcribe_prompt_audio(*, file_path, file_name, content_type, language):
        assert file_path.endswith(".webm")
        assert file_name == "prompt.webm"
        assert content_type == "audio/webm"
        assert language == "ne-NP"
        return SimpleNamespace(
            text="नमस्ते, मेरो खाताको जानकारी चाहियो",
            language="ne-NP",
            requested_language="ne-NP",
            duration_seconds=1.4,
            confidence=0.92,
            provider="test-private-stt",
        )

    monkeypatch.setattr("app.api.voice.transcribe_prompt_audio", fake_transcribe_prompt_audio)

    response = client.post(
        "/api/voice/transcribe",
        headers={"Authorization": f"Bearer {token}"},
        data={"language": "ne-NP"},
        files={"file": ("prompt.webm", b"audio-bytes", "audio/webm")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["text"] == "नमस्ते, मेरो खाताको जानकारी चाहियो"
    assert payload["language"] == "ne-NP"
    assert payload["requested_language"] == "ne-NP"
    assert payload["duration_seconds"] == 1.4
    assert payload["confidence"] == 0.92
    assert payload["provider"] == "test-private-stt"
