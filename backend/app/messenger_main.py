from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from .models.bank import Bank  # noqa: F401
from .models.chat import ChatMessage, ChatSession  # noqa: F401
from .models.document import Document, DocumentChunk  # noqa: F401
from .models.token import RevokedToken  # noqa: F401
from .models.user import User  # noqa: F401
from .api import messenger
from .core.config import settings
from .core.context import request_ip
from .db.messenger_session import get_messenger_session
from .db.session import get_session


app = FastAPI(
    title=f"{settings.PROJECT_NAME} Secure Messenger",
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/messenger/openapi.json",
)

app.dependency_overrides[get_session] = get_messenger_session

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def capture_request_ip(request: Request, call_next):
    forwarded = request.headers.get("X-Forwarded-For")
    ip = forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else "")
    token = request_ip.set(ip)
    try:
        response = await call_next(request)
    finally:
        request_ip.reset(token)
    return response


@app.get("/health")
def health_check():
    return {"status": "ok", "project": "secure-messenger", "version": settings.VERSION}


app.include_router(
    messenger.router,
    prefix=f"{settings.API_V1_STR}/messenger",
    tags=["messenger"],
)
