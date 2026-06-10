from typing import Any, List, Optional
from pathlib import Path
import os
import uuid
import logging
import asyncio
import re
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select
import json
import httpx
from ..core.limiter import limiter

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.txt', '.jpg', '.jpeg', '.png', '.xlsx', '.xls', '.pptx', '.ppt'}
MAX_UPLOAD_BYTES = 50 * 1024 * 1024  # 50 MB


def _safe_filename(session_id: int, original: str) -> str:
    ext = Path(original).suffix.lower()
    return f"{session_id}_{uuid.uuid4().hex}{ext}"

from ..db.session import get_session
from ..models.user import User
from ..models.chat import ChatSession, ChatMessage
from ..schemas.chat import ChatSessionCreate, ChatSessionResponse, ChatRequest, ChatMessageResponse
from .deps import get_current_analytics_user, get_current_user
from ..services.rag_service import (
    NOT_FOUND_RESPONSE,
    POLICY_CITATION_INCOMPLETE_RESPONSE,
    _build_context,
    _build_sources,
    _filter_results,
    _high_confidence_results,
    _policy_citation_blocking_sources,
    _policy_citation_gate_blocks,
    _search,
    generate_rag_response,
    async_generate_rag_response,
    get_system_identity,
    MAX_CONTEXT_RESULTS,
    RAG_PROMPT_TEMPLATE,
    UNTRUSTED_EVIDENCE_WARNING,
)
from ..services.audit_service import log_audit_event
from ..services.guardrail_service import detect_prompt_injection, detect_and_mask_pii
from ..services.query_rewrite_service import rewrite_query_for_retrieval
from ..services.llm_service import async_call_llm
from ..services.embedding_service import generate_embeddings
from ..services.llm_gateway import model_status, reserve_model, resolve_model_profile, select_model_key_for_workflow
from ..services.ingestion_queue import enqueue_document_ingestion
from ..services.ingestion_service import extract_pages
from ..services.citation_verifier import attach_source_verification, verify_answer_against_sources
from ..services.feature_flag_service import is_feature_enabled
from ..core.config import settings


def _resolve_model_endpoint(model_name: Optional[str]) -> tuple[str, str, str]:
    """
    Map model name to (API_BASE, MODEL, API_KEY).
    Returns default (LLM_A) if model_name is None or unknown.
    """
    model_map = {
        'LipiFast': (settings.LLM_A_API_BASE, settings.LLM_A_MODEL, settings.LLM_A_API_KEY),
        'LipiCore': (settings.LLM_C_API_BASE, settings.LLM_C_MODEL, settings.LLM_C_API_KEY),
    }
    if model_name in model_map:
        return model_map[model_name]
    # Default to LLM_A if not found
    return (settings.LLM_A_API_BASE, settings.LLM_A_MODEL, settings.LLM_A_API_KEY)


def _model_supports_vision(model_name: Optional[str]) -> bool:
    requested = (model_name or "").strip().lower()
    if not requested:
        return False
    return requested in {"vision", "lipicore", "lipi core", "lipi-core", "ocr", "document_image", "image_ocr"}

router = APIRouter()

CHAT_UPLOAD_DIR = settings.CHAT_UPLOAD_DIR

KNOWLEDGE_SEARCH_MODES = {"ask_knowledge", "approved_knowledge", "analyze_file", "compare"}
SOURCE_REQUIRED_MODES = {"approved_knowledge", "analyze_file", "compare"}
SOURCE_BACKED_QUERY_RE = re.compile(
    r"\b("
    r"according to|as per|approved|policy|policies|source|sources|cite|citation|"
    r"document|documents|circular|circulars|directive|directives|sop|manual|"
    r"rule|rules|regulation|regulations|regulatory|nrb|act|law|laws|"
    r"section|sections|clause|clauses|article|articles|quote|quoted|exact"
    r")\b"
    r"|\bunder\s+(?:the\s+)?(?:act|law|policy|rule|regulation|directive|circular|section|clause|nrb)\b"
    r"|\bwhat\s+does\b.{0,60}\bsay\b",
    flags=re.IGNORECASE,
)
SOURCE_BACKED_NEPALI_TERMS = {
    "नीति",
    "स्रोत",
    "दफा",
    "ऐन",
    "नियम",
    "परिपत्र",
    "निर्देशन",
}
LOW_INTENT_TERMS = {
    "hello",
    "helo",
    "hi",
    "hey",
    "namaste",
    "namaskar",
    "thanks",
    "thank",
    "thankyou",
    "okay",
    "ok",
    "yes",
    "no",
    "नमस्ते",
    "धन्यवाद",
}
MODEL_CONTEXT_LIMIT_TOKENS = settings.LLM_CONTEXT_WINDOW_TOKENS
MODEL_TOKEN_HEADROOM = 96
MIN_GENERATION_TOKENS = 128
APPROX_CHARS_PER_TOKEN = 3

MODE_INSTRUCTIONS = {
    "ask_knowledge": (
        "Mode: Ask BankAi. Use approved bank knowledge with citations when relevant sources are available. "
        "If no approved source matches, answer as general knowledge and clearly avoid presenting it as approved bank policy."
    ),
    "approved_knowledge": (
        "Mode: Ask Approved Knowledge. Answer only when approved bank documents support the response. "
        "If approved sources do not support the answer, say that the answer was not found in approved documents."
    ),
    "analyze_file": (
        "Mode: Analyze Uploaded File. Focus on the user's selected session files. "
        "Cite uploaded file evidence when making claims."
    ),
    "summarize": (
        "Mode: Summarize. Produce a concise staff-ready summary. "
        "Use cited document evidence when sources are available."
    ),
    "draft": (
        "Mode: Draft. Produce a draft for staff review. Clearly treat the output as a draft "
        "and not official bank policy unless source-backed evidence is cited."
    ),
    "translate": (
        "Mode: Translate. Translate faithfully between English and Nepali while preserving banking terms. "
        "Do not add unsupported policy advice."
    ),
    "compare": (
        "Mode: Compare Documents. Compare selected documents or policies and cite evidence for differences. "
        "If enough source evidence is not available, say what is missing."
    ),
}


def mode_instruction(mode: str) -> str:
    return MODE_INSTRUCTIONS.get(mode, MODE_INSTRUCTIONS["ask_knowledge"])


def general_fallback_system_identity(language: str, mode: str) -> str:
    return (
        f"{get_system_identity(language)}\n\n{mode_instruction(mode)}\n\n"
        "No approved document source matched this question. Answer using general knowledge only. "
        "Give one direct staff-ready answer. Do not provide multiple alternative answers unless the user explicitly asks for alternatives. "
        "Do not claim this is official bank policy, an approved circular, or a bank-specific rule. "
        "For internal bank policy, tell the user to verify against approved documents or a supervisor."
    )


def _estimate_message_tokens(content: str) -> int:
    return max(1, (len(content or "") + APPROX_CHARS_PER_TOKEN - 1) // APPROX_CHARS_PER_TOKEN)


def _vllm_message(role: str, content: str) -> dict:
    return {"role": role, "content": content}


def _message_cost(message: dict) -> int:
    return _estimate_message_tokens(message.get("content", "")) + 6


def _should_skip_document_retrieval(message: str) -> bool:
    normalized = " ".join((message or "").strip().lower().split())
    if not normalized:
        return True
    tokens = re.findall(r"[\w\u0900-\u097F]+", normalized, flags=re.UNICODE)
    if not tokens:
        return True
    return len(tokens) <= 3 and all(token in LOW_INTENT_TERMS for token in tokens)


def _should_attempt_document_retrieval(
    *,
    message: str | None,
    mode: str,
    active_document_ids: list[int] | None,
    has_image: bool,
) -> bool:
    if has_image:
        return False
    if message is not None and _should_skip_document_retrieval(message):
        return False
    return bool(active_document_ids) or mode in KNOWLEDGE_SEARCH_MODES


def _requires_source_backed_answer(
    *,
    mode: str,
    message: str | None,
    retrieval_query: str | None = None,
) -> bool:
    if mode in SOURCE_REQUIRED_MODES:
        return True

    combined = " ".join(part for part in [message, retrieval_query] if part).strip().lower()
    if not combined:
        return False
    if SOURCE_BACKED_QUERY_RE.search(combined):
        return True
    return any(term in combined for term in SOURCE_BACKED_NEPALI_TERMS)


def _document_context_prompt(*, context: str, retrieval_query: str, safe_message: str) -> str:
    interpreted_query = ""
    if retrieval_query and retrieval_query.strip().lower() != (safe_message or "").strip().lower():
        interpreted_query = (
            "The latest user request was normalized for document retrieval as: "
            f"\"{retrieval_query.strip()}\". Treat this as the user's intended document question.\n\n"
        )
    return (
        f"\n\n--- DOCUMENT CONTEXT ---\n"
        f"{interpreted_query}"
        f"Use the following context from approved documents to answer the user's question.\n"
        f"{UNTRUSTED_EVIDENCE_WARNING}\n\n"
        f"{context}\n--- END DOCUMENT CONTEXT ---"
    )


def _document_context_results(results):
    return list(results[:MAX_CONTEXT_RESULTS])


def prepare_vllm_payload_messages(
    *,
    system: str,
    history,
    desired_max_tokens: int,
    context_limit: int = MODEL_CONTEXT_LIMIT_TOKENS,
) -> tuple[list[dict], int, bool]:
    system_message = _vllm_message("system", system)
    history_messages = [
        _vllm_message("assistant" if msg.role == "assistant" else "user", msg.content)
        for msg in history
    ]
    max_tokens = min(desired_max_tokens, max(MIN_GENERATION_TOKENS, context_limit // 8))
    input_budget = max(MIN_GENERATION_TOKENS, context_limit - max_tokens - MODEL_TOKEN_HEADROOM)
    selected_reversed: list[dict] = []
    used_tokens = _message_cost(system_message)
    was_trimmed = False

    for message in reversed(history_messages):
        cost = _message_cost(message)
        if selected_reversed and used_tokens + cost > input_budget:
            was_trimmed = True
            continue
        if not selected_reversed and used_tokens + cost > input_budget:
            selected_reversed.append(message)
            was_trimmed = True
            continue
        selected_reversed.append(message)
        used_tokens += cost

    selected = list(reversed(selected_reversed))
    estimated_input_tokens = _message_cost(system_message) + sum(_message_cost(message) for message in selected)
    available_output_tokens = context_limit - estimated_input_tokens - MODEL_TOKEN_HEADROOM
    if available_output_tokens < max_tokens:
        max_tokens = max(MIN_GENERATION_TOKENS, available_output_tokens)

    return [system_message, *selected], max_tokens, was_trimmed


def should_show_document_search_status(
    *,
    active_document_ids: list[int] | None,
    mode: str,
    has_image: bool,
    message: str | None = None,
) -> bool:
    return _should_attempt_document_retrieval(
        message=message,
        mode=mode,
        active_document_ids=active_document_ids,
        has_image=has_image,
    )


def derive_answer_metadata(
    *,
    mode: str,
    sources: list[dict] | None,
    active_document_ids: list[int] | None,
    answer: str | None,
    citation_verification: dict | None = None,
) -> dict:
    source_count = len(sources or [])
    requires_sources = mode in SOURCE_REQUIRED_MODES
    trust_label = (citation_verification or {}).get(
        "trust_label",
        "no_sources" if source_count == 0 else "source_unverified",
    )
    source_values = sources or []
    has_complete_cited_source = any(source.get("citation_complete") is True for source in source_values)
    has_incomplete_cited_source = any(source.get("citation_complete") is False for source in source_values)
    citation_incomplete = (
        answer == POLICY_CITATION_INCOMPLETE_RESPONSE
        or trust_label == "citation_incomplete"
        or (has_incomplete_cited_source and not has_complete_cited_source)
    )

    if citation_incomplete:
        answer_type = "citation_incomplete"
        trust_label = "citation_incomplete"
    elif source_count > 0:
        answer_type = "uploaded_file_answer" if mode == "analyze_file" or active_document_ids else "official_source_backed"
    elif requires_sources:
        answer_type = "not_found"
    else:
        answer_type = "general_answer"

    if source_count > 0 and citation_verification and (
        citation_verification.get("status") in {"partially_supported", "unsupported"}
        or trust_label in {"partially_source_supported", "not_source_supported"}
    ):
        answer_type = "unsupported_source"

    if answer and requires_sources and source_count == 0:
        if any(term in answer.lower() for term in ("escalate", "supervisor", "compliance team")):
            answer_type = "escalate"

    return {
        "mode": mode,
        "answer_type": answer_type,
        "source_count": source_count,
        "requires_sources": requires_sources,
        "trust_label": trust_label,
        "citation_verification": citation_verification or {},
    }


def _citation_verification_with_feature_flags(
    *,
    answer: str | None,
    sources: list[dict] | None,
    db: Session,
    bank_id: int | None,
) -> dict:
    if not bank_id:
        return verify_answer_against_sources(answer=answer, sources=sources)
    return verify_answer_against_sources(
        answer=answer,
        sources=sources,
        nli_enabled=is_feature_enabled(db, bank_id, "citation_nli_verification"),
        semantic_enabled=is_feature_enabled(db, bank_id, "citation_semantic_verification"),
    )


def ensure_chat_upload_dir() -> None:
    import os
    os.makedirs(CHAT_UPLOAD_DIR, exist_ok=True)


@router.get("/models/status")
async def read_model_status(current_user: User = Depends(get_current_analytics_user)) -> dict:
    return await model_status()


def _session_active_document_ids(session: ChatSession, requested_ids: Optional[List[int]] = None) -> list[int]:
    try:
        stored_ids = json.loads(session.active_document_ids_json or "[]")
    except Exception:
        stored_ids = []

    merged: list[int] = []
    for doc_id in [*stored_ids, *(requested_ids or [])]:
        try:
            doc_id = int(doc_id)
        except (TypeError, ValueError):
            continue
        if doc_id not in merged:
            merged.append(doc_id)
    return merged


def _track_session_document(session: ChatSession, document_id: int, db: Session) -> None:
    active_docs = _session_active_document_ids(session)
    if document_id not in active_docs:
        active_docs.append(document_id)
        session.active_document_ids_json = json.dumps(active_docs)
        db.add(session)
        db.commit()


def _maybe_update_session_title(session: ChatSession, message: str, db: Session) -> None:
    if session.title and session.title not in ("New Conversation", "New Analysis"):
        return
    title = " ".join(message.strip().split())[:60]
    if len(message.strip()) > 60:
        title = title.rstrip() + "..."
    if title:
        session.title = title
        db.add(session)
        db.commit()


def _update_session_summary(session: ChatSession, user_message: str, assistant_message: str, db: Session) -> None:
    summary = f"User asked: {user_message[:220]}"
    if assistant_message:
        summary += f"\nBankAi answered: {assistant_message[:320]}"
    session.session_summary = summary
    db.add(session)
    db.commit()

EXTRACT_TEXT_INTENT_RE = re.compile(
    r"\b(?:extract|show|display|give|copy|read)\s+(?:me\s+)?(?:the\s+)?(?:raw\s+|full\s+|all\s+)?text\b|"
    r"\b(?:ocr|text extraction|extracted text|raw text|full text)\b|"
    r"(?:टेक्स्ट|पाठ|अक्षर)\s*(?:निकाल|देखा|देऊ)",
    re.IGNORECASE,
)
CHAT_EXTRACT_TEXT_MAX_CHARS = 24000


def _is_extract_text_request(message: str | None) -> bool:
    return bool(EXTRACT_TEXT_INTENT_RE.search(message or ""))


def _selected_session_uploads(
    *,
    db: Session,
    session_id: int,
    current_user: User,
    active_document_ids: list[int] | None,
):
    if not active_document_ids:
        return []
    from ..models.document import Document

    docs = []
    seen: set[int] = set()
    for doc_id in active_document_ids:
        if doc_id in seen:
            continue
        seen.add(doc_id)
        doc = db.get(Document, doc_id)
        if (
            doc
            and doc.bank_id == current_user.bank_id
            and doc.uploaded_by == current_user.id
            and doc.session_id == session_id
            and doc.document_scope == "session_upload"
            and doc.status not in ("disabled", "failed")
        ):
            docs.append(doc)
    return docs


def _review_pages_for_document(db: Session, document_id: int) -> list[dict]:
    from ..models.document_intelligence import DocumentExtractionPage

    records = db.exec(
        select(DocumentExtractionPage)
        .where(DocumentExtractionPage.document_id == document_id)
        .order_by(DocumentExtractionPage.page_number)
    ).all()
    pages = []
    for record in records:
        text = (record.corrected_text or record.extracted_text or "").strip()
        if not text:
            continue
        pages.append({
            "page_number": record.page_number,
            "text": text,
            "ocr_confidence": record.ocr_confidence,
            "table_confidence": record.table_confidence,
            "page_bbox_json": record.bbox_json,
        })
    return pages


def _label_extracted_page(page: dict, index: int) -> str:
    if page.get("sheet_name"):
        return f"Sheet: {page.get('sheet_name')}"
    if page.get("slide_number"):
        return f"Slide {page.get('slide_number')}"
    if page.get("page_number"):
        return f"Page {page.get('page_number')}"
    return f"Part {index}"


def _build_uploaded_file_text_response(
    *,
    db: Session,
    session_id: int,
    current_user: User,
    active_document_ids: list[int] | None,
    max_chars: int = CHAT_EXTRACT_TEXT_MAX_CHARS,
) -> tuple[str, list[dict]]:
    docs = _selected_session_uploads(
        db=db,
        session_id=session_id,
        current_user=current_user,
        active_document_ids=active_document_ids,
    )
    if not docs:
        return "", []

    blocks = []
    sources = []
    for doc in docs:
        pages = _review_pages_for_document(db, doc.id) or extract_pages(doc.file_path, doc.file_type)
        page_blocks = []
        for index, page in enumerate(pages, start=1):
            text = (page.get("text") or "").strip()
            if not text:
                continue
            page_blocks.append(f"### {_label_extracted_page(page, index)}\n{text}")
        doc_text = "\n\n".join(page_blocks).strip()
        if not doc_text:
            continue
        blocks.append(f"## Extracted text from {doc.file_name}\n\n{doc_text}")
        sources.append({
            "document_id": doc.id,
            "document_title": doc.title or doc.file_name,
            "title": doc.title or doc.file_name,
            "file_name": doc.file_name,
            "file_type": doc.file_type,
            "source_file_url": f"/api/documents/{doc.id}/file",
            "document_type": doc.document_type,
            "department": doc.department,
            "page_number": None,
            "pdf_page_number": None,
            "printed_page_number": None,
            "document_heading": None,
            "clause_number": None,
            "citation_complete": True,
            "section_label": None,
            "section_number": None,
            "chunk_index": None,
            "snippet": doc_text[:180],
            "passage": doc_text[:1000],
            "relevance_score": 1.0,
            "source_warnings": [],
        })

    response = "\n\n---\n\n".join(blocks).strip()
    if not response:
        return "", sources
    if len(response) > max_chars:
        response = (
            response[:max_chars].rstrip()
            + "\n\n[Text truncated in chat. Open OCR Extraction for the full export.]"
        )
    return response, sources


def _direct_extract_verification(sources: list[dict] | None) -> dict:
    source_count = len(sources or [])
    return {
        "status": "supported" if source_count else "no_sources",
        "trust_label": "source_supported" if source_count else "no_sources",
        "verification_stage": "direct_extract",
        "supported_sentence_count": 0,
        "unsupported_sentence_count": 0,
        "unsupported_sentences": [],
        "nli_checked_sentence_count": 0,
    }


def _citation_incomplete_verification(sources: list[dict] | None) -> dict:
    incomplete_reasons = []
    for source in sources or []:
        for reason in source.get("citation_incomplete_reasons") or []:
            if reason not in incomplete_reasons:
                incomplete_reasons.append(reason)
    return {
        "status": "citation_incomplete",
        "trust_label": "citation_incomplete",
        "verification_stage": "citation_metadata",
        "supported_sentence_count": 0,
        "unsupported_sentence_count": 0,
        "unsupported_sentences": [],
        "nli_checked_sentence_count": 0,
        "incomplete_source_count": len(sources or []),
        "citation_incomplete_reasons": incomplete_reasons,
    }


@router.post("/sessions", response_model=ChatSessionResponse)
def create_chat_session(
    *,
    db: Session = Depends(get_session),
    session_in: ChatSessionCreate,
    current_user: User = Depends(get_current_user),
) -> Any:
    if current_user.bank_id is None:
        from ..models.bank import Bank
        default_bank = db.exec(select(Bank).where(Bank.code == "DEFAULT")).first()
        if default_bank:
            current_user.bank_id = default_bank.id
        else:
            raise HTTPException(status_code=500, detail="User has no bank assigned and no default bank exists")
            
    session = ChatSession(
        bank_id=current_user.bank_id,
        user_id=current_user.id,
        title=session_in.title
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

@router.get("/sessions", response_model=List[ChatSessionResponse])
def read_chat_sessions(
    db: Session = Depends(get_session),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Retrieve chat sessions for current user.
    """
    sessions = db.exec(
        select(ChatSession)
        .where(ChatSession.user_id == current_user.id)
        .order_by(ChatSession.created_at.desc())
        .offset(skip).limit(limit)
    ).all()
    return sessions

@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
def read_chat_session(
    *,
    db: Session = Depends(get_session),
    session_id: int,
    current_user: User = Depends(get_current_user),
) -> Any:
    session = db.get(ChatSession, session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessageResponse])
def read_chat_messages(
    *,
    db: Session = Depends(get_session),
    session_id: int,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Retrieve all messages for a chat session.
    """
    session = db.get(ChatSession, session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found")
    
    messages = db.exec(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
    ).all()
    return messages

@router.post("/sessions/{session_id}/messages")
@limiter.limit("30/minute")
async def create_chat_message(
    request: Request,
    *,
    db: Session = Depends(get_session),
    session_id: int,
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_user),
) -> Any:
    session = db.get(ChatSession, session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found")

    # 1. Guardrail checks
    if detect_prompt_injection(chat_request.message, db, current_user.id, current_user.bank_id):
        raise HTTPException(status_code=400, detail="Query rejected due to security policy.")

    safe_message = detect_and_mask_pii(chat_request.message)

    # 2. Save user message
    user_msg = ChatMessage(
        bank_id=current_user.bank_id,
        session_id=session_id,
        user_id=current_user.id,
        role="user",
        content=safe_message
    )
    db.add(user_msg)
    db.commit()
    _maybe_update_session_title(session, safe_message, db)

    from sqlalchemy import asc
    history = db.exec(
        select(ChatMessage).where(ChatMessage.session_id == session_id)
        .order_by(asc(ChatMessage.created_at)).limit(20)
    ).all()
    retrieval_query = rewrite_query_for_retrieval(safe_message, history[:-1])

    # 3. Build prompt and call LLM async
    mode = chat_request.mode
    active_doc_ids = _session_active_document_ids(session, chat_request.active_document_ids)
    direct_text_extract = False
    sys_identity = f"{get_system_identity(chat_request.language)}\n\n{mode_instruction(mode)}"
    if chat_request.image:
        from ..services.llm_service import async_call_vision_llm
        answer = await async_call_vision_llm(f"{sys_identity}\n\n{chat_request.message}", chat_request.image)
        sources = []
    elif active_doc_ids and _is_extract_text_request(safe_message):
        answer, sources = _build_uploaded_file_text_response(
            db=db,
            session_id=session_id,
            current_user=current_user,
            active_document_ids=active_doc_ids,
        )
        if not answer:
            answer = "No extractable text was found in the selected uploaded file."
            sources = []
        direct_text_extract = True
    else:
        answer, sources = await async_generate_rag_response(
            retrieval_query,
            current_user.bank_id,
            current_user.role,
            db,
            chat_request.language,
            active_document_ids=active_doc_ids,
            session_id=session_id,
            user_id=current_user.id,
            user_department=current_user.department,
            model_name=chat_request.model_override or select_model_key_for_workflow(mode),
        )
        if answer == POLICY_CITATION_INCOMPLETE_RESPONSE and not _requires_source_backed_answer(
            mode=mode,
            message=safe_message,
            retrieval_query=retrieval_query,
        ):
            answer = await async_call_llm(
                safe_message,
                system=general_fallback_system_identity(chat_request.language, mode),
                user_id=current_user.id,
                role=current_user.role,
            )
            sources = []
        elif answer == NOT_FOUND_RESPONSE and mode not in SOURCE_REQUIRED_MODES:
            answer = await async_call_llm(
                safe_message,
                system=general_fallback_system_identity(chat_request.language, mode),
                user_id=current_user.id,
                role=current_user.role,
            )
            sources = []

    if direct_text_extract:
        citation_verification = _direct_extract_verification(sources)
    elif answer == POLICY_CITATION_INCOMPLETE_RESPONSE:
        citation_verification = _citation_incomplete_verification(sources)
    else:
        citation_verification = _citation_verification_with_feature_flags(
            answer=answer,
            sources=sources,
            db=db,
            bank_id=current_user.bank_id,
        )
    sources = attach_source_verification(sources, citation_verification)
    
    # 4. Save AI message
    ai_msg = ChatMessage(
        bank_id=current_user.bank_id,
        session_id=session_id,
        user_id=current_user.id,
        role="assistant",
        content=answer,
        sources_json=json.dumps(sources)
    )
    db.add(ai_msg)
    db.commit()
    db.refresh(ai_msg)
    _update_session_summary(session, safe_message, answer, db)
    answer_metadata = derive_answer_metadata(
        mode=mode,
        sources=sources,
        active_document_ids=active_doc_ids if not chat_request.image else [],
        answer=answer,
        citation_verification=citation_verification,
    )
    
    log_audit_event(
        db=db,
        action="chat_query",
        resource_type="chat",
        resource_id=str(session_id),
        bank_id=current_user.bank_id,
        user_id=current_user.id,
        metadata={
            "query": safe_message,
            "pii_detected": safe_message != chat_request.message,
            "masking_mode": "redact",
            "llm_received_masked_input": not direct_text_extract and answer != POLICY_CITATION_INCOMPLETE_RESPONSE,
            "sources_count": len(sources),
            "answer_type": answer_metadata["answer_type"],
            "trust_label": answer_metadata.get("trust_label"),
            "mode": mode,
            "citation_verification": citation_verification,
            "rewritten_query": retrieval_query if retrieval_query != safe_message else None,
            "direct_text_extract": direct_text_extract or None,
            "citation_gate_blocked": answer == POLICY_CITATION_INCOMPLETE_RESPONSE or None,
        }
    )
    
    return ai_msg

@router.post("/sessions/{session_id}/stream")
@limiter.limit("30/minute")
async def stream_chat_message(
    request: Request,
    *,
    db: Session = Depends(get_session),
    session_id: int,
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Stream a chat response using Server-Sent Events.
    """
    logger.info(f"[STREAM] Route handler called for session {session_id}")
    session = db.get(ChatSession, session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found")

    if detect_prompt_injection(chat_request.message, db, current_user.id, current_user.bank_id):
        raise HTTPException(status_code=400, detail="Query rejected due to security policy.")

    safe_message = detect_and_mask_pii(chat_request.message)

    # Save user message
    user_msg = ChatMessage(
        bank_id=current_user.bank_id,
        session_id=session_id,
        user_id=current_user.id,
        role="user",
        content=safe_message
    )
    db.add(user_msg)
    db.commit()
    _maybe_update_session_title(session, safe_message, db)

    from sqlalchemy import asc
    history = db.exec(
        select(ChatMessage).where(ChatMessage.session_id == session_id)
        .order_by(asc(ChatMessage.created_at)).limit(20)
    ).all()
    retrieval_query = rewrite_query_for_retrieval(safe_message, history[:-1])

    active_doc_ids = _session_active_document_ids(session, chat_request.active_document_ids)
    mode = chat_request.mode
    has_image = bool(chat_request.image)

    async def event_stream():
        logger.info("[STREAM] Starting event_stream")

        # Check if user selected a model and uploaded an image
        selected_model = chat_request.model_override
        if has_image and selected_model and not _model_supports_vision(selected_model):
            yield f"data: {json.dumps({'type': 'status', 'message': '⚠️ Warning: The selected model does not support image analysis. Using text-based analysis instead.'})}\n\n"

        direct_text_extract_requested = not has_image and bool(active_doc_ids) and _is_extract_text_request(safe_message)
        if (
            not direct_text_extract_requested
            and should_show_document_search_status(
                active_document_ids=active_doc_ids,
                mode=mode,
                has_image=has_image,
                message=safe_message,
            )
        ):
            status_message = "Searching selected documents..." if active_doc_ids else "Searching approved knowledge..."
            yield f"data: {json.dumps({'type': 'status', 'message': status_message})}\n\n"

        sources_list = []
        sys_identity = f"{get_system_identity(chat_request.language)}\n\n{mode_instruction(mode)}"
        logger.info("[STREAM] Got system identity")
        should_search_documents = _should_attempt_document_retrieval(
            message=safe_message,
            mode=mode,
            active_document_ids=active_doc_ids,
            has_image=has_image,
        )

        if direct_text_extract_requested:
            yield f"data: {json.dumps({'type': 'status', 'message': 'Extracting text from selected upload...'})}\n\n"
            full_response, sources_list = _build_uploaded_file_text_response(
                db=db,
                session_id=session_id,
                current_user=current_user,
                active_document_ids=active_doc_ids,
            )
            if not full_response:
                full_response = "No extractable text was found in the selected uploaded file."
                sources_list = []
            yield f"data: {json.dumps({'token': full_response})}\n\n"
            suggestions = []
            citation_verification = _direct_extract_verification(sources_list)
            sources_list = attach_source_verification(sources_list, citation_verification)
            answer_metadata = derive_answer_metadata(
                mode=mode,
                sources=sources_list,
                active_document_ids=active_doc_ids,
                answer=full_response,
                citation_verification=citation_verification,
            )
            try:
                ai_msg = ChatMessage(
                    bank_id=current_user.bank_id,
                    session_id=session_id,
                    user_id=current_user.id,
                    role="assistant",
                    content=full_response,
                    sources_json=json.dumps(sources_list),
                    suggestions_json=json.dumps(suggestions),
                )
                db.add(ai_msg)
                db.commit()
                _update_session_summary(session, safe_message, full_response, db)
                log_audit_event(
                    db=db,
                    action="chat_query",
                    resource_type="chat",
                    resource_id=str(session_id),
                    bank_id=current_user.bank_id,
                    user_id=current_user.id,
                    metadata={
                        "query": safe_message,
                        "pii_detected": safe_message != chat_request.message,
                        "masking_mode": "redact",
                        "llm_received_masked_input": False,
                        "sources_count": len(sources_list),
                        "answer_type": answer_metadata["answer_type"],
                        "trust_label": answer_metadata.get("trust_label"),
                        "mode": mode,
                        "citation_verification": citation_verification,
                        "rewritten_query": retrieval_query if retrieval_query != safe_message else None,
                        "streamed": True,
                        "direct_text_extract": True,
                    },
                )
            except Exception as e:
                logger.error(f"[STREAM] Error saving direct text extraction message: {e}")
            yield f"data: {json.dumps({'done': True, 'sources': sources_list, 'suggestions': suggestions, 'answer_metadata': answer_metadata})}\n\n"
            return

        if should_search_documents:
            try:
                logger.info("[STREAM] Starting RAG search")

                logger.info(f"[STREAM] Generating embeddings for query: {retrieval_query[:50]}")
                embeddings = await asyncio.to_thread(generate_embeddings, [retrieval_query])
                query_vector = embeddings[0]
                logger.info("[STREAM] Embeddings generated")

                results = _search(query_vector, current_user.bank_id, active_doc_ids, session_id, retrieval_query, db)
                if results:
                    filtered = _filter_results(results, db, session_id, current_user.role, current_user.department)
                    high_confidence = _high_confidence_results(filtered)
                    if high_confidence:
                        context = _build_context(high_confidence, db)
                        sys_identity += _document_context_prompt(
                            context=context,
                            retrieval_query=retrieval_query,
                            safe_message=safe_message,
                        )
                        sources_list = _build_sources(high_confidence, db)
            except Exception as e:
                logger.error(f"RAG failed in stream: {e}")

        logger.info("[STREAM] About to yield prepare status")
        yield f"data: {json.dumps({'type': 'status', 'message': 'Generating response...'})}\n\n"

        if not has_image and _policy_citation_gate_blocks(retrieval_query, sources_list):
            if not _requires_source_backed_answer(
                mode=mode,
                message=safe_message,
                retrieval_query=retrieval_query,
            ):
                sources_list = []
                sys_identity = general_fallback_system_identity(chat_request.language, mode)
            else:
                sources_list = _policy_citation_blocking_sources(sources_list)
                full_response = POLICY_CITATION_INCOMPLETE_RESPONSE
                yield f"data: {json.dumps({'token': full_response})}\n\n"
                suggestions = []
                citation_verification = _citation_incomplete_verification(sources_list)
                sources_list = attach_source_verification(sources_list, citation_verification)
                answer_metadata = derive_answer_metadata(
                    mode=mode,
                    sources=sources_list,
                    active_document_ids=active_doc_ids,
                    answer=full_response,
                    citation_verification=citation_verification,
                )
                try:
                    ai_msg = ChatMessage(
                        bank_id=current_user.bank_id,
                        session_id=session_id,
                        user_id=current_user.id,
                        role="assistant",
                        content=full_response,
                        sources_json=json.dumps(sources_list),
                        suggestions_json=json.dumps(suggestions),
                    )
                    db.add(ai_msg)
                    db.commit()
                    _update_session_summary(session, safe_message, full_response, db)
                    log_audit_event(
                        db=db,
                        action="chat_query",
                        resource_type="chat",
                        resource_id=str(session_id),
                        bank_id=current_user.bank_id,
                        user_id=current_user.id,
                        metadata={
                            "query": safe_message,
                            "pii_detected": safe_message != chat_request.message,
                            "masking_mode": "redact",
                            "llm_received_masked_input": False,
                            "sources_count": len(sources_list),
                            "answer_type": answer_metadata["answer_type"],
                            "trust_label": answer_metadata.get("trust_label"),
                            "mode": mode,
                            "citation_verification": citation_verification,
                            "rewritten_query": retrieval_query if retrieval_query != safe_message else None,
                            "streamed": True,
                            "citation_gate_blocked": True,
                        },
                    )
                except Exception as e:
                    logger.error(f"[STREAM] Error saving citation-incomplete message: {e}")
                yield f"data: {json.dumps({'done': True, 'sources': sources_list, 'suggestions': suggestions, 'answer_metadata': answer_metadata})}\n\n"
                return

        if not has_image and mode in SOURCE_REQUIRED_MODES and not sources_list:
            full_response = NOT_FOUND_RESPONSE
            yield f"data: {json.dumps({'token': full_response})}\n\n"
            suggestions = []
            citation_verification = _citation_verification_with_feature_flags(
                answer=full_response,
                sources=sources_list,
                db=db,
                bank_id=current_user.bank_id,
            )
            answer_metadata = derive_answer_metadata(
                mode=mode,
                sources=sources_list,
                active_document_ids=active_doc_ids,
                answer=full_response,
                citation_verification=citation_verification,
            )
            try:
                ai_msg = ChatMessage(
                    bank_id=current_user.bank_id,
                    session_id=session_id,
                    user_id=current_user.id,
                    role="assistant",
                    content=full_response,
                    sources_json=json.dumps(sources_list),
                    suggestions_json=json.dumps(suggestions),
                )
                db.add(ai_msg)
                db.commit()
                _update_session_summary(session, safe_message, full_response, db)
                log_audit_event(
                    db=db,
                    action="chat_query",
                    resource_type="chat",
                    resource_id=str(session_id),
                    bank_id=current_user.bank_id,
                    user_id=current_user.id,
                    metadata={
                        "query": safe_message,
                        "pii_detected": safe_message != chat_request.message,
                        "masking_mode": "redact",
                        "llm_received_masked_input": False,
                        "sources_count": 0,
                        "answer_type": answer_metadata["answer_type"],
                        "trust_label": answer_metadata.get("trust_label"),
                        "mode": mode,
                        "rewritten_query": retrieval_query if retrieval_query != safe_message else None,
                        "streamed": True,
                        "not_found_reason": "no_source_above_threshold",
                    },
                )
            except Exception as e:
                logger.error(f"[STREAM] Error saving not-found message: {e}")
            yield f"data: {json.dumps({'done': True, 'sources': sources_list, 'suggestions': suggestions, 'answer_metadata': answer_metadata})}\n\n"
            return

        if not has_image and not sources_list and mode not in SOURCE_REQUIRED_MODES:
            sys_identity = general_fallback_system_identity(chat_request.language, mode)

        selected_model = chat_request.model_override or select_model_key_for_workflow(mode)
        selected_profile = resolve_model_profile(selected_model)
        vllm_messages, response_max_tokens, trimmed_history = prepare_vllm_payload_messages(
            system=sys_identity,
            history=history[-10:],
            desired_max_tokens=selected_profile.max_tokens,
            context_limit=selected_profile.context_window_tokens,
        )
        if trimmed_history:
            yield f"data: {json.dumps({'type': 'status', 'message': 'Older chat context was shortened to fit the local model.'})}\n\n"
        status = await model_status()
        selected_status = status.get(selected_profile.key, {})
        if selected_status.get("active", 0) >= selected_status.get("limit", 1):
            yield f"data: {json.dumps({'type': 'status', 'message': 'All model workers are busy. Your request is queued.'})}\n\n"

        full_response = ""
        try:
            async with reserve_model(
                user_id=current_user.id,
                role=current_user.role,
                model_name=selected_model,
            ) as lease:
                profile = lease.profile
                if lease.queued_ahead > 0:
                    yield f"data: {json.dumps({'type': 'status', 'message': f'Queued behind {lease.queued_ahead} request(s).'})}\n\n"

                url = f"{profile.api_base}/v1/chat/completions"
                headers = {"Authorization": f"Bearer {profile.api_key}"}
                payload = {
                    "model": profile.model,
                    "messages": vllm_messages,
                    "stream": True,
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "max_tokens": response_max_tokens,
                }

                logger.info(f"[STREAM] About to call vLLM at {url} with model={profile.model}")
                logger.info("[STREAM] Creating httpx client")
                async with httpx.AsyncClient(timeout=profile.timeout_seconds) as client:
                    logger.info("[STREAM] Streaming from vLLM...")
                    async with client.stream("POST", url, json=payload, headers=headers) as response:
                        logger.info(f"[STREAM] Got vLLM response: {response.status_code}")
                        if response.status_code != 200:
                            body = await response.aread()
                            logger.error(f"[STREAM] vLLM error body: {body[:500]}")
                            error_text = body.decode("utf-8", errors="ignore")
                            if response.status_code == 400 and "maximum context length" in error_text:
                                token = "AI prompt was too long for the local model. I shortened chat history, but this request still exceeded the model context. Please start a new chat or use fewer selected documents."
                            else:
                                token = f"AI engine returned error {response.status_code}."
                            yield f"data: {json.dumps({'token': token, 'done': True})}\n\n"
                            return
                        logger.info("[STREAM] Starting to read vLLM lines")
                        token_count = 0
                        async for line in response.aiter_lines():
                            if not line.startswith("data: "):
                                continue
                            chunk = line[6:]
                            if chunk == "[DONE]":
                                logger.info("[STREAM] Got [DONE]")
                                break
                            try:
                                data = json.loads(chunk)
                                if data.get("choices"):
                                    delta = data["choices"][0].get("delta", {})
                                    token = delta.get("content", "")
                                    if token:
                                        token_count += 1
                                        full_response += token
                                        logger.debug(f"[STREAM] Token {token_count}: {token[:20]}")
                                        yield f"data: {json.dumps({'token': token})}\n\n"
                            except json.JSONDecodeError:
                                continue
        except asyncio.TimeoutError:
            logger.error("[STREAM] Timed out waiting for model capacity")
            yield f"data: {json.dumps({'token': 'AI engine is busy. Please retry shortly.', 'done': True})}\n\n"
            return
        except Exception as e:
            logger.error(f"[STREAM] Streaming error: {e}")
            yield f"data: {json.dumps({'token': 'Error connecting to AI engine.', 'done': True})}\n\n"
            return

        logger.info(f"[STREAM] Done. tokens={len(full_response)}")

        # Skip suggestions during streaming (would block the async generator)
        # Could generate async in background if needed
        suggestions = []
        citation_verification = _citation_verification_with_feature_flags(
            answer=full_response,
            sources=sources_list,
            db=db,
            bank_id=current_user.bank_id,
        )
        sources_list = attach_source_verification(sources_list, citation_verification)
        answer_metadata = derive_answer_metadata(
            mode=mode,
            sources=sources_list,
            active_document_ids=active_doc_ids,
            answer=full_response,
            citation_verification=citation_verification,
        )

        try:
            ai_msg = ChatMessage(
                bank_id=current_user.bank_id,
                session_id=session_id,
                user_id=current_user.id,
                role="assistant",
                content=full_response,
                sources_json=json.dumps(sources_list),
                suggestions_json=json.dumps(suggestions),
            )
            db.add(ai_msg)
            db.commit()
            _update_session_summary(session, safe_message, full_response, db)
            log_audit_event(
                db=db,
                action="chat_query",
                resource_type="chat",
                resource_id=str(session_id),
                bank_id=current_user.bank_id,
                user_id=current_user.id,
                metadata={
                    "query": safe_message,
                    "pii_detected": safe_message != chat_request.message,
                    "masking_mode": "redact",
                    "llm_received_masked_input": True,
                    "sources_count": len(sources_list),
                    "answer_type": answer_metadata["answer_type"],
                    "trust_label": answer_metadata.get("trust_label"),
                    "mode": mode,
                    "citation_verification": citation_verification,
                    "rewritten_query": retrieval_query if retrieval_query != safe_message else None,
                    "streamed": True,
                },
            )
        except Exception as e:
            logger.error(f"[STREAM] Error saving message: {e}")

        answer_metadata = derive_answer_metadata(
            mode=mode,
            sources=sources_list,
            active_document_ids=active_doc_ids,
            answer=full_response,
            citation_verification=citation_verification,
        )
        yield f"data: {json.dumps({'done': True, 'sources': sources_list, 'suggestions': suggestions, 'answer_metadata': answer_metadata})}\n\n"

    logger.info("[STREAM] About to return StreamingResponse with event_stream generator")
    return StreamingResponse(event_stream(), media_type="text/event-stream")

@router.post("/sessions/{session_id}/files")
async def upload_session_file(
    *,
    db: Session = Depends(get_session),
    session_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """
    Upload a file to a specific chat session for background processing.
    """
    from ..models.document import Document

    session = db.get(ChatSession, session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found")

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type '{ext}' not supported")

    ensure_chat_upload_dir()
    safe_name = _safe_filename(session_id, file.filename)
    file_path = os.path.join(CHAT_UPLOAD_DIR, safe_name)

    # Read file content asynchronously
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="File is empty")

    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="File exceeds 50 MB limit")

    # Write to disk
    with open(file_path, "wb") as buffer:
        buffer.write(content)

    file_ext = ext.lstrip(".")
    doc = Document(
        bank_id=current_user.bank_id,
        uploaded_by=current_user.id,
        title=file.filename,
        file_name=file.filename,
        file_type=file_ext,
        file_path=file_path,
        document_type="chat_upload",
        status="uploaded",
        session_id=session_id,
        document_scope="session_upload"
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    _track_session_document(session, doc.id, db)

    try:
        enqueue_document_ingestion(doc.id, db)
        db.refresh(doc)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    
    return {
        "id": doc.id,
        "document_id": doc.id,
        "session_id": session_id,
        "file_name": file.filename,
        "name": file.filename,
        "status": doc.status,
    }

@router.post("/sessions/{session_id}/stream-file")
async def stream_chat_with_file(
    *,
    db: Session = Depends(get_session),
    session_id: int,
    message: str = Form(...),
    language: str = Form("en"),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """
    Upload a file and stream AI analysis of its contents.
    Supports PDF, DOCX, XLSX, PPTX, TXT, and images.
    """
    import shutil, base64
    from ..models.document import Document

    session = db.get(ChatSession, session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found")

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type '{ext}' not supported")

    ensure_chat_upload_dir()
    safe_name = _safe_filename(session_id, file.filename)
    file_path = os.path.join(CHAT_UPLOAD_DIR, safe_name)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    if os.path.getsize(file_path) > MAX_UPLOAD_BYTES:
        os.remove(file_path)
        raise HTTPException(status_code=400, detail="File exceeds 50 MB limit")

    file_ext = ext.lstrip(".")
    doc = Document(
        bank_id=current_user.bank_id,
        uploaded_by=current_user.id,
        title=file.filename,
        file_name=file.filename,
        file_type=file_ext,
        file_path=file_path,
        document_type="chat_upload",
        status="uploaded",
        session_id=session_id,
        document_scope="session_upload",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    _track_session_document(session, doc.id, db)

    # Save user message
    user_msg = ChatMessage(
        bank_id=current_user.bank_id,
        session_id=session_id,
        user_id=current_user.id,
        role="user",
        content=message
    )
    db.add(user_msg)
    db.commit()
    _maybe_update_session_title(session, message, db)
    
    from sqlalchemy import asc
    history = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(asc(ChatMessage.created_at)).all()
    
    sys_identity = get_system_identity(language)
    vllm_messages = [{"role": "system", "content": sys_identity}]
    for msg in history[-10:]:
        vllm_messages.append({
            "role": "assistant" if msg.role == "assistant" else "user",
            "content": msg.content
        })

    is_image = file_ext in ['jpg', 'jpeg', 'png']

    if is_image:
        with open(file_path, 'rb') as f:
            image_b64 = base64.b64encode(f.read()).decode('utf-8')
        vllm_messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": f"I uploaded \"{file.filename}\". {message}"},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}},
            ]
        })
    else:
        from ..services.ingestion_service import extract_pages
        from ..services.large_document_context_service import build_large_file_prompt

        extracted_pages = extract_pages(file_path, file_ext)
        file_prompt, file_prompt_metadata = build_large_file_prompt(
            file_name=file.filename,
            user_request=message,
            pages=extracted_pages or [{"page_number": None, "text": "(No text could be extracted from this file)"}],
            context_window_tokens=settings.LLM_DEEP_CONTEXT_WINDOW_TOKENS,
            output_tokens=settings.LLM_DEEP_MAX_TOKENS,
        )
        vllm_messages.append({"role": "user", "content": file_prompt})

    try:
        enqueue_document_ingestion(doc.id, db)
        db.refresh(doc)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    async def event_stream():
        full_response = ""

        yield f"data: {json.dumps({'type': 'status', 'message': 'Analyzing uploaded file...'})}\n\n"

        try:
            async with reserve_model(
                user_id=current_user.id,
                role=current_user.role,
                model_name=select_model_key_for_workflow("analyze_file"),
            ) as lease:
                profile = lease.profile
                if lease.queued_ahead > 0:
                    yield f"data: {json.dumps({'type': 'status', 'message': f'Queued behind {lease.queued_ahead} request(s).'})}\n\n"

                url = f"{profile.api_base}/v1/chat/completions"
                headers = {"Authorization": f"Bearer {profile.api_key}"}
                payload = {
                    "model": profile.model,
                    "messages": vllm_messages,
                    "stream": True,
                    "temperature": 0.7,
                    "max_tokens": profile.max_tokens,
                }

                async with httpx.AsyncClient(timeout=profile.timeout_seconds) as client:
                    async with client.stream("POST", url, json=payload, headers=headers) as response:
                        if response.status_code != 200:
                            body = await response.aread()
                            logger.error(f"[STREAM-FILE] vLLM error {response.status_code}: {body[:300]}")
                            yield f"data: {json.dumps({'token': 'Error connecting to AI engine.'})}\n\n"
                        else:
                            async for line in response.aiter_lines():
                                if not line.startswith("data: "):
                                    continue
                                chunk = line[6:]
                                if chunk == "[DONE]":
                                    break
                                try:
                                    data = json.loads(chunk)
                                    if data.get("choices"):
                                        token = data["choices"][0].get("delta", {}).get("content", "")
                                        if token:
                                            full_response += token
                                            yield f"data: {json.dumps({'token': token})}\n\n"
                                except json.JSONDecodeError:
                                    continue
        except asyncio.TimeoutError:
            logger.error("[STREAM-FILE] Timed out waiting for model capacity")
            yield f"data: {json.dumps({'token': 'AI engine is busy. Please retry shortly.'})}\n\n"
        except Exception as e:
            logger.error(f"[STREAM-FILE] Error: {e}")
            yield f"data: {json.dumps({'token': 'Error connecting to AI engine.'})}\n\n"

        try:
            ai_msg = ChatMessage(
                bank_id=current_user.bank_id,
                session_id=session_id,
                user_id=current_user.id,
                role="assistant",
                content=full_response,
                sources_json=json.dumps([{
                    "document_id": doc.id,
                    "document_title": doc.title or doc.file_name,
                    "title": doc.title or doc.file_name,
                    "file_name": doc.file_name,
                    "file_type": doc.file_type,
                    "source_file_url": f"/api/documents/{doc.id}/file",
                    "analysis_metadata": file_prompt_metadata if not is_image else {},
                }])
            )
            db.add(ai_msg)
            db.commit()
            _update_session_summary(session, message, full_response, db)
        except Exception as e:
            logger.error(f"[STREAM-FILE] Error saving message: {e}")

        yield f"data: {json.dumps({'done': True, 'id': doc.id, 'document_id': doc.id})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
