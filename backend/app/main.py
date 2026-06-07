from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from .core.config import settings
from .core.limiter import limiter
from .core.context import request_ip
from .db.session import init_db
from .api import (
    analytics,
    audit,
    audit_evidence,
    auth,
    banks,
    branch_responses,
    ceo_messages,
    chat,
    checklist_workspace,
    circular_impact,
    compliance_reviews,
    configuration,
    complaint_workspace,
    document_review,
    documents,
    employee_directory,
    evaluations,
    export,
    feature_flags,
    knowledge_gaps,
    kyc_case_prep,
    loan_support,
    long_document_analysis,
    market_utilities,
    model_lab,
    notifications,
    ocr,
    policy_changes,
    staff_work_items,
    support_cases,
    tasks,
    users,
    voice,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    from .services.qdrant_service import init_qdrant
    init_qdrant()
    from .db.init_data import create_super_admin
    create_super_admin()
    from .services.embedding_service import generate_embeddings
    generate_embeddings(["warmup"])
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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
    return {"status": "ok", "project": settings.PROJECT_NAME, "version": settings.VERSION}


# Include routers
app.include_router(auth.router,      prefix=f"{settings.API_V1_STR}/auth",      tags=["auth"])
app.include_router(banks.router,     prefix=f"{settings.API_V1_STR}/banks",     tags=["banks"])
app.include_router(users.router,     prefix=f"{settings.API_V1_STR}/users",     tags=["users"])
app.include_router(documents.router, prefix=f"{settings.API_V1_STR}/documents", tags=["documents"])
app.include_router(chat.router,      prefix=f"{settings.API_V1_STR}/chat",      tags=["chat"])
app.include_router(audit.router,     prefix=f"{settings.API_V1_STR}/audit",     tags=["audit"])
app.include_router(analytics.router, prefix=f"{settings.API_V1_STR}/analytics", tags=["analytics"])
app.include_router(tasks.router,    prefix=f"{settings.API_V1_STR}/tasks",    tags=["tasks"])
app.include_router(export.router,   prefix=f"{settings.API_V1_STR}/export",   tags=["export"])
app.include_router(configuration.router, prefix=f"{settings.API_V1_STR}/config", tags=["config"])
app.include_router(feature_flags.router, prefix=f"{settings.API_V1_STR}/feature-flags", tags=["feature-flags"])
app.include_router(employee_directory.router, prefix=f"{settings.API_V1_STR}/employee-directory", tags=["employee-directory"])
app.include_router(evaluations.router, prefix=f"{settings.API_V1_STR}/evaluations", tags=["evaluations"])
app.include_router(ceo_messages.router, prefix=f"{settings.API_V1_STR}/ceo-messages", tags=["ceo-messages"])
app.include_router(knowledge_gaps.router, prefix=f"{settings.API_V1_STR}/knowledge-gaps", tags=["knowledge-gaps"])
app.include_router(policy_changes.router, prefix=f"{settings.API_V1_STR}/policy-changes", tags=["policy-changes"])
app.include_router(complaint_workspace.router, prefix=f"{settings.API_V1_STR}/complaint-workspace", tags=["complaint-workspace"])
app.include_router(circular_impact.router, prefix=f"{settings.API_V1_STR}/circular-impact", tags=["circular-impact"])
app.include_router(branch_responses.router, prefix=f"{settings.API_V1_STR}/branch-responses", tags=["branch-responses"])
app.include_router(kyc_case_prep.router, prefix=f"{settings.API_V1_STR}/kyc-case-prep", tags=["kyc-case-prep"])
app.include_router(checklist_workspace.router, prefix=f"{settings.API_V1_STR}/checklist-workspace", tags=["checklist-workspace"])
app.include_router(audit_evidence.router, prefix=f"{settings.API_V1_STR}/audit-evidence", tags=["audit-evidence"])
app.include_router(support_cases.router, prefix=f"{settings.API_V1_STR}/support-cases", tags=["support-cases"])
app.include_router(compliance_reviews.router, prefix=f"{settings.API_V1_STR}/compliance-reviews", tags=["compliance-reviews"])
app.include_router(loan_support.router, prefix=f"{settings.API_V1_STR}/loan-support", tags=["loan-support"])
app.include_router(long_document_analysis.router, prefix=f"{settings.API_V1_STR}/long-document-analysis", tags=["long-document-analysis"])
app.include_router(market_utilities.router, prefix=f"{settings.API_V1_STR}/market-utilities", tags=["market-utilities"])
app.include_router(model_lab.router, prefix=f"{settings.API_V1_STR}/model-lab", tags=["model-lab"])
app.include_router(notifications.router, prefix=f"{settings.API_V1_STR}/notifications", tags=["notifications"])
app.include_router(staff_work_items.router, prefix=f"{settings.API_V1_STR}/staff-work-items", tags=["staff-work-items"])
app.include_router(document_review.router, prefix=f"{settings.API_V1_STR}/document-review", tags=["document-review"])
app.include_router(ocr.router, prefix=f"{settings.API_V1_STR}/ocr", tags=["ocr"])
app.include_router(voice.router, prefix=f"{settings.API_V1_STR}/voice", tags=["voice"])
