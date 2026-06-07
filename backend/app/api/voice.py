import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlmodel import Session

from ..api.deps import get_current_user
from ..core.config import settings
from ..db.session import get_session
from ..models.user import User
from ..schemas.voice import VoiceCapabilitiesResponse, VoiceLanguageResponse, VoiceTranscriptionResponse
from ..services.audit_service import log_audit_event
from ..services.stt_service import (
    PUBLIC_STT_LANGUAGES,
    SttServiceError,
    audio_extension,
    normalize_stt_language,
    transcribe_prompt_audio,
)

router = APIRouter()

ALLOWED_AUDIO_EXTENSIONS = {".webm", ".wav", ".mp3", ".m4a", ".mp4", ".ogg", ".oga"}


def _voice_upload_dir() -> str:
    upload_dir = os.path.join(settings.UPLOAD_DIR, "voice_prompts")
    os.makedirs(upload_dir, exist_ok=True)
    return upload_dir


@router.get("/capabilities", response_model=VoiceCapabilitiesResponse)
def get_voice_capabilities(current_user: User = Depends(get_current_user)):
    return VoiceCapabilitiesResponse(
        enabled=settings.STT_PROVIDER.strip().lower() != "disabled",
        provider=settings.STT_PROVIDER,
        languages=[
            VoiceLanguageResponse(code=language.code, label=language.label)
            for language in PUBLIC_STT_LANGUAGES
        ],
        max_upload_mb=max(1, settings.STT_MAX_UPLOAD_BYTES // (1024 * 1024)),
        browser_fallback_enabled=settings.STT_BROWSER_FALLBACK_ENABLED,
    )


@router.post("/transcribe", response_model=VoiceTranscriptionResponse)
async def transcribe_voice_prompt(
    file: UploadFile = File(...),
    language: str = Form("en"),
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        normalize_stt_language(language)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    file_name = file.filename or "prompt.webm"
    ext = audio_extension(file_name) or ".webm"
    if ext not in ALLOWED_AUDIO_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Supported audio formats: WEBM, WAV, MP3, M4A, MP4, OGG")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Audio file is empty")
    if len(content) > settings.STT_MAX_UPLOAD_BYTES:
        max_mb = max(1, settings.STT_MAX_UPLOAD_BYTES // (1024 * 1024))
        raise HTTPException(status_code=400, detail=f"Audio file exceeds {max_mb} MB limit")

    temp_path = os.path.join(_voice_upload_dir(), f"{current_user.bank_id}_{uuid.uuid4().hex}{ext}")
    try:
        Path(temp_path).write_bytes(content)
        try:
            result = await transcribe_prompt_audio(
                file_path=temp_path,
                file_name=file_name,
                content_type=file.content_type,
                language=language,
            )
        except SttServiceError as exc:
            log_audit_event(
                db=db,
                action="voice_transcribe_failed",
                resource_type="voice_prompt",
                resource_id=file_name,
                bank_id=current_user.bank_id,
                user_id=current_user.id,
                metadata={
                    "file_name": file_name,
                    "file_size": len(content),
                    "language": language,
                    "provider": settings.STT_PROVIDER,
                    "detail": exc.detail,
                },
            )
            raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

        log_audit_event(
            db=db,
            action="voice_transcribe",
            resource_type="voice_prompt",
            resource_id=file_name,
            bank_id=current_user.bank_id,
            user_id=current_user.id,
            metadata={
                "file_name": file_name,
                "file_size": len(content),
                "language": result.language,
                "provider": result.provider,
                "duration_seconds": result.duration_seconds,
                "confidence": result.confidence,
                "character_count": len(result.text),
            },
        )
        return VoiceTranscriptionResponse(
            text=result.text,
            language=result.language,
            requested_language=result.requested_language,
            duration_seconds=result.duration_seconds,
            confidence=result.confidence,
            provider=result.provider,
        )
    finally:
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except OSError:
            pass
