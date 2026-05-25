import os
import tempfile
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

# Fail fast on missing required secrets — never start with insecure defaults
_jwt_secret = os.getenv("JWT_SECRET")
if not _jwt_secret:
    raise RuntimeError("JWT_SECRET environment variable must be set")

_super_admin_password = os.getenv("SUPER_ADMIN_PASSWORD")
if not _super_admin_password:
    raise RuntimeError("SUPER_ADMIN_PASSWORD environment variable must be set")


def _parse_origins(raw: str) -> list[str]:
    return [o.strip() for o in raw.split(",") if o.strip()]


class Settings(BaseSettings):
    PROJECT_NAME: str = "Bank's Own LLM"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api"

    JWT_SECRET: str = _jwt_secret
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))

    ALLOWED_ORIGINS_RAW: str = os.getenv(
        "ALLOWED_ORIGINS",
        "https://ai.silverlining.com.np,https://202.51.2.50,http://202.51.2.50,http://localhost:3000,http://localhost:80,http://localhost",
    )
    COOKIE_SECURE: bool = os.getenv("COOKIE_SECURE", "false").lower() == "true"

    @property
    def ALLOWED_ORIGINS(self) -> list[str]:
        return _parse_origins(self.ALLOWED_ORIGINS_RAW)

    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/lipicore")
    MESSENGER_DATABASE_URL: str = os.getenv("MESSENGER_DATABASE_URL") or os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/lipicore")

    QDRANT_HOST: str = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", "6333"))

    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "admin")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "password")
    MINIO_BUCKET: str = os.getenv("MINIO_BUCKET", "bank-documents")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    INGESTION_QUEUE_NAME: str = os.getenv("INGESTION_QUEUE_NAME", "document-ingestion")
    INGESTION_JOB_TIMEOUT_SECONDS: int = int(os.getenv("INGESTION_JOB_TIMEOUT_SECONDS", "1800"))
    INGESTION_JOB_RESULT_TTL_SECONDS: int = int(os.getenv("INGESTION_JOB_RESULT_TTL_SECONDS", "86400"))
    INGESTION_JOB_FAILURE_TTL_SECONDS: int = int(os.getenv("INGESTION_JOB_FAILURE_TTL_SECONDS", "604800"))
    INGESTION_MAX_RETRIES: int = int(os.getenv("INGESTION_MAX_RETRIES", "2"))
    INGESTION_WORKER_CONCURRENCY: int = int(os.getenv("INGESTION_WORKER_CONCURRENCY", "1"))
    OCR_ENGINE: str = os.getenv("OCR_ENGINE", "tesseract")
    OCR_LANGUAGES: str = os.getenv("OCR_LANGUAGES", "eng+nep")
    OCR_TESSERACT_CONFIG: str = os.getenv("OCR_TESSERACT_CONFIG", "--psm 6")
    OCR_IMAGE_DPI: int = int(os.getenv("OCR_IMAGE_DPI", "300"))
    OCR_MAX_PAGES: int = int(os.getenv("OCR_MAX_PAGES", "200"))

    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", os.path.join(tempfile.gettempdir(), "lipicore_uploads"))
    CHAT_UPLOAD_DIR: str = os.getenv("CHAT_UPLOAD_DIR", os.path.join(tempfile.gettempdir(), "lipicore_chat_uploads"))
    MESSENGER_UPLOAD_DIR: str = os.getenv("MESSENGER_UPLOAD_DIR", os.path.join(tempfile.gettempdir(), "lipicore_messenger_uploads"))

    # vLLM backends — each backend can serve one or more models
    # LLM_A (vllm-b): LipiLLM fast inference
    LLM_A_API_BASE: str = os.getenv("LLM_A_API_BASE", "http://localhost:8001")
    LLM_A_MODEL: str = os.getenv("LLM_A_MODEL", "model-a")
    LLM_A_API_KEY: str = os.getenv("LLM_A_API_KEY", "no-key")

    # LLM_B (vllm-b): LipiLLM (same as A for now)
    LLM_B_API_BASE: str = os.getenv("LLM_B_API_BASE", "http://localhost:8002")
    LLM_B_MODEL: str = os.getenv("LLM_B_MODEL", "model-b")
    LLM_B_API_KEY: str = os.getenv("LLM_B_API_KEY", "no-key")

    # LLM_C (vllm-c): Gemma-4 26B for deeper analysis
    LLM_C_API_BASE: str = os.getenv("LLM_C_API_BASE", "http://localhost:8003")
    LLM_C_MODEL: str = os.getenv("LLM_C_MODEL", "gemma-4-26b-4bit")
    LLM_C_API_KEY: str = os.getenv("LLM_C_API_KEY", "no-key")

    # Vision model endpoint for scanned PDFs, document images, and OCR fallback
    LLM_VISION_API_BASE: str = os.getenv("LLM_VISION_API_BASE", "http://localhost:8007")
    LLM_VISION_MODEL: str = os.getenv("LLM_VISION_MODEL", "Qwen/Qwen3-VL-8B-Instruct")
    LLM_VISION_API_KEY: str = os.getenv("LLM_VISION_API_KEY", "no-key")

    LLM_A_MAX_CONCURRENCY: int = int(os.getenv("LLM_A_MAX_CONCURRENCY", "12"))
    LLM_C_MAX_CONCURRENCY: int = int(os.getenv("LLM_C_MAX_CONCURRENCY", "4"))
    LLM_VISION_MAX_CONCURRENCY: int = int(os.getenv("LLM_VISION_MAX_CONCURRENCY", "2"))
    LLM_USER_MAX_CONCURRENCY: int = int(os.getenv("LLM_USER_MAX_CONCURRENCY", "1"))
    LLM_ADMIN_MAX_CONCURRENCY: int = int(os.getenv("LLM_ADMIN_MAX_CONCURRENCY", "2"))
    LLM_QUEUE_TIMEOUT_SECONDS: float = float(os.getenv("LLM_QUEUE_TIMEOUT_SECONDS", "120"))
    LLM_QUEUE_STALE_SECONDS: float = float(os.getenv("LLM_QUEUE_STALE_SECONDS", "10"))
    LLM_FAST_MAX_TOKENS: int = int(os.getenv("LLM_FAST_MAX_TOKENS", "512"))
    LLM_DEEP_MAX_TOKENS: int = int(os.getenv("LLM_DEEP_MAX_TOKENS", "768"))
    LLM_VISION_MAX_TOKENS: int = int(os.getenv("LLM_VISION_MAX_TOKENS", "768"))
    LLM_CONTEXT_WINDOW_TOKENS: int = int(os.getenv("LLM_CONTEXT_WINDOW_TOKENS", "8192"))
    LLM_FAST_CONTEXT_WINDOW_TOKENS: int = int(os.getenv("LLM_FAST_CONTEXT_WINDOW_TOKENS", os.getenv("LLM_CONTEXT_WINDOW_TOKENS", "8192")))
    LLM_DEEP_CONTEXT_WINDOW_TOKENS: int = int(os.getenv("LLM_DEEP_CONTEXT_WINDOW_TOKENS", os.getenv("LLM_CONTEXT_WINDOW_TOKENS", "8192")))
    LLM_VISION_CONTEXT_WINDOW_TOKENS: int = int(os.getenv("LLM_VISION_CONTEXT_WINDOW_TOKENS", os.getenv("LLM_CONTEXT_WINDOW_TOKENS", "8192")))

    # LLM_D (vllm-d): Qwen3.6 27B for report generation
    LLM_D_API_BASE: str = os.getenv("LLM_D_API_BASE", "http://localhost:8004")
    LLM_D_MODEL: str = os.getenv("LLM_D_MODEL", "qwen3.6-27b-4bit")
    LLM_D_API_KEY: str = os.getenv("LLM_D_API_KEY", "no-key")

    # Legacy single-LLM fields kept for backward compat (points to A by default)
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "vllm")
    LLM_MODEL: str = os.getenv("LLM_MODEL") or os.getenv("LLM_A_MODEL", "model-a")
    LLM_API_BASE: str = os.getenv("LLM_API_BASE") or os.getenv("LLM_A_API_BASE", "http://localhost:8001")
    LLM_API_KEY: str = os.getenv("LLM_API_KEY") or os.getenv("LLM_A_API_KEY", "no-key")

    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    EMBEDDING_DIMENSION: int = int(os.getenv("EMBEDDING_DIMENSION", "384"))

    SUPER_ADMIN_EMAIL: str = os.getenv("SUPER_ADMIN_EMAIL", "admin@lipicore.io")
    SUPER_ADMIN_PASSWORD: str = _super_admin_password


settings = Settings()
