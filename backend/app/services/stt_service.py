import asyncio
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx

from ..core.config import settings


@dataclass(frozen=True)
class SttLanguage:
    code: str
    label: str
    whisper_language: str


@dataclass(frozen=True)
class TranscriptionResult:
    text: str
    language: str
    requested_language: str
    duration_seconds: float | None
    confidence: float | None
    provider: str


class SttServiceError(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


SUPPORTED_STT_LANGUAGES: dict[str, SttLanguage] = {
    "en": SttLanguage(code="en", label="English", whisper_language="en"),
    "ne": SttLanguage(code="ne-NP", label="Nepali", whisper_language="ne"),
    "ne-NP": SttLanguage(code="ne-NP", label="Nepali", whisper_language="ne"),
}

PUBLIC_STT_LANGUAGES: list[SttLanguage] = [
    SUPPORTED_STT_LANGUAGES["en"],
    SUPPORTED_STT_LANGUAGES["ne-NP"],
]

_local_model: Any | None = None
_local_model_lock = threading.Lock()


def normalize_stt_language(language: str | None) -> SttLanguage:
    requested = (language or "en").strip()
    if requested == "np":
        raise ValueError("Unsupported language code 'np'. Use 'ne' or 'ne-NP' for Nepali.")
    try:
        return SUPPORTED_STT_LANGUAGES[requested]
    except KeyError as exc:
        raise ValueError("Supported voice languages are 'en' and 'ne-NP'.") from exc


def _get_local_whisper_model():
    global _local_model
    if _local_model is not None:
        return _local_model

    with _local_model_lock:
        if _local_model is not None:
            return _local_model
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise SttServiceError(
                503,
                "Local Whisper STT is not installed. Install faster-whisper or configure STT_PROVIDER=openai_compatible.",
            ) from exc

        download_root = settings.STT_MODEL_CACHE_DIR or None
        _local_model = WhisperModel(
            settings.STT_MODEL,
            device=settings.STT_DEVICE,
            compute_type=settings.STT_COMPUTE_TYPE,
            download_root=download_root,
        )
        return _local_model


def _transcribe_with_local_whisper(file_path: str, language: SttLanguage) -> TranscriptionResult:
    model = _get_local_whisper_model()
    segments, info = model.transcribe(
        file_path,
        language=language.whisper_language,
        vad_filter=True,
        beam_size=1,
    )
    text = " ".join(segment.text.strip() for segment in segments if segment.text and segment.text.strip()).strip()
    return TranscriptionResult(
        text=text,
        language=language.code,
        requested_language=language.code,
        duration_seconds=getattr(info, "duration", None),
        confidence=getattr(info, "language_probability", None),
        provider="local_whisper",
    )


async def _transcribe_with_openai_compatible(
    *,
    file_path: str,
    file_name: str,
    content_type: str | None,
    language: SttLanguage,
) -> TranscriptionResult:
    api_base = settings.STT_API_BASE.rstrip("/")
    headers = {"Authorization": f"Bearer {settings.STT_API_KEY}"}
    mime_type = content_type or "application/octet-stream"
    data = {
        "model": settings.STT_MODEL,
        "language": language.whisper_language,
        "response_format": "json",
    }
    with open(file_path, "rb") as audio_file:
        files = {"file": (file_name, audio_file, mime_type)}
        async with httpx.AsyncClient(timeout=settings.STT_TIMEOUT_SECONDS) as client:
            response = await client.post(
                f"{api_base}/v1/audio/transcriptions",
                headers=headers,
                data=data,
                files=files,
            )
    if response.status_code >= 400:
        raise SttServiceError(response.status_code, f"STT provider failed: {response.text[:300]}")

    payload = response.json()
    return TranscriptionResult(
        text=(payload.get("text") or "").strip(),
        language=language.code,
        requested_language=language.code,
        duration_seconds=payload.get("duration") or payload.get("duration_seconds"),
        confidence=payload.get("confidence") or payload.get("language_probability"),
        provider="openai_compatible",
    )


async def transcribe_prompt_audio(
    *,
    file_path: str,
    file_name: str,
    content_type: str | None,
    language: str | None,
) -> TranscriptionResult:
    normalized_language = normalize_stt_language(language)
    provider = settings.STT_PROVIDER.strip().lower()

    if provider == "disabled":
        raise SttServiceError(503, "Prompt voice transcription is disabled.")
    if provider == "local_whisper":
        return await asyncio.to_thread(_transcribe_with_local_whisper, file_path, normalized_language)
    if provider == "openai_compatible":
        return await _transcribe_with_openai_compatible(
            file_path=file_path,
            file_name=file_name,
            content_type=content_type,
            language=normalized_language,
        )

    raise SttServiceError(503, f"Unsupported STT_PROVIDER '{settings.STT_PROVIDER}'.")


def audio_extension(file_name: str) -> str:
    return Path(file_name or "").suffix.lower()
