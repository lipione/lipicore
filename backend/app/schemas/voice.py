from pydantic import BaseModel


class VoiceLanguageResponse(BaseModel):
    code: str
    label: str


class VoiceCapabilitiesResponse(BaseModel):
    enabled: bool
    provider: str
    languages: list[VoiceLanguageResponse]
    max_upload_mb: int
    browser_fallback_enabled: bool


class VoiceTranscriptionResponse(BaseModel):
    text: str
    language: str
    requested_language: str
    duration_seconds: float | None = None
    confidence: float | None = None
    provider: str
