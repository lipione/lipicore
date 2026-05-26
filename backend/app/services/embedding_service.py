from sentence_transformers import SentenceTransformer
from ..core.config import settings
from threading import Lock, local

# Load one model per worker thread. SentenceTransformer/PyTorch inference can
# hang when a model initialized on the app thread is reused by background tasks.
_thread_state = local()
_model_lock = Lock()

def get_embedding_model():
    model = getattr(_thread_state, "model", None)
    if model is None:
        with _model_lock:
            model = SentenceTransformer(
                settings.EMBEDDING_MODEL,
                cache_folder=settings.EMBEDDING_CACHE_DIR,
            )
        _thread_state.model = model
    return model

def generate_embeddings(texts: list[str]) -> list[list[float]]:
    model = get_embedding_model()
    embeddings = model.encode(texts, normalize_embeddings=settings.EMBEDDING_NORMALIZE)
    return embeddings.tolist()
