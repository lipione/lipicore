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
    GLOBAL_RETRIEVAL_STATUSES,
    GLOBAL_RETRIEVAL_VERSION_STATES,
    MAX_CANDIDATE_RESULTS,
    MIN_SOURCE_RELEVANCE_SCORE,
    NOT_FOUND_RESPONSE,
    SESSION_RETRIEVAL_STATUSES,
    _document_visible_to_user,
    _rerank_results,
    generate_rag_response,
    async_generate_rag_response,
    get_system_identity,
    RAG_PROMPT_TEMPLATE,
)
from ..services.audit_service import log_audit_event
from ..services.guardrail_service import detect_prompt_injection, detect_and_mask_pii
from ..services.query_rewrite_service import rewrite_query_for_retrieval
from ..services.llm_service import async_call_llm
from ..services.llm_gateway import model_status, reserve_model, resolve_model_profile
from ..services.ingestion_queue import enqueue_document_ingestion
from ..services.citation_verifier import attach_source_verification, verify_answer_against_sources
from ..core.config import settings


def _resolve_model_endpoint(model_name: Optional[str]) -> tuple[str, str, str]:
    """
    Map model name to (API_BASE, MODEL, API_KEY).
    Returns default (LLM_A) if model_name is None or unknown.
    """
    model_map = {
        'gemma-4': (settings.LLM_A_API_BASE, settings.LLM_A_MODEL, settings.LLM_A_API_KEY),
        'gemma-4-26b-4bit': (settings.LLM_C_API_BASE, settings.LLM_C_MODEL, settings.LLM_C_API_KEY),
    }
    if model_name in model_map:
        return model_map[model_name]
    # Default to LLM_A if not found
    return (settings.LLM_A_API_BASE, settings.LLM_A_MODEL, settings.LLM_A_API_KEY)


def _model_supports_vision(model_name: Optional[str]) -> bool:
    """
    Check if a model supports vision/image analysis.
    For now, none of the vLLM text models support vision — fallback to general prompt.
    """
    # All current models are text-only; would need multimodal models to support vision
    return False

router = APIRouter()

CHAT_UPLOAD_DIR = settings.CHAT_UPLOAD_DIR

KNOWLEDGE_SEARCH_MODES = {"ask_knowledge", "analyze_file", "compare"}
SOURCE_REQUIRED_MODES = {"analyze_file", "compare"}

MODE_INSTRUCTIONS = {
    "ask_knowledge": (
        "Mode: Ask BankAi. Use approved bank knowledge with citations when relevant sources are available. "
        "If no approved source matches, answer as general knowledge and clearly avoid presenting it as approved bank policy."
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
        "Do not claim this is official bank policy, an approved circular, or a bank-specific rule. "
        "For internal bank policy, tell the user to verify against approved documents or a supervisor."
    )


def should_show_document_search_status(
    *,
    active_document_ids: list[int] | None,
    mode: str,
    has_image: bool,
) -> bool:
    if has_image:
        return False
    return bool(active_document_ids) or mode in KNOWLEDGE_SEARCH_MODES


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

    if source_count > 0:
        answer_type = "uploaded_file_answer" if mode == "analyze_file" or active_document_ids else "official_source_backed"
    elif requires_sources:
        answer_type = "not_found"
    else:
        answer_type = "general_answer"

    if answer and requires_sources and source_count == 0:
        if any(term in answer.lower() for term in ("escalate", "supervisor", "compliance team")):
            answer_type = "escalate"

    return {
        "mode": mode,
        "answer_type": answer_type,
        "source_count": source_count,
        "requires_sources": requires_sources,
        "citation_verification": citation_verification or {},
    }


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

def _should_mix_global_knowledge(message: str) -> bool:
    text = (message or "").lower()
    global_terms = (
        "global",
        "knowledge base",
        "policy library",
        "nrb",
        "regulation",
        "directive",
        "compare",
        "against",
        "across documents",
        "all documents",
        "other documents",
    )
    return any(term in text for term in global_terms)

SECTION_RE = re.compile(
    r"\b(?:section|sec\.?|clause|article|chapter|part)\s+([0-9]+(?:\.[0-9]+)*)\b|"
    r"\b(?:दफा|परिच्छेद|बुँदा)\s*([०-९0-9]+(?:[.\-][०-९0-9]+)*)",
    re.IGNORECASE,
)


def _extract_section_label(text: str | None) -> str | None:
    if not text:
        return None
    match = SECTION_RE.search(text[:1200])
    if not match:
        return None
    return " ".join(match.group(0).strip().split())[:80]


def _source_prefix(doc, payload: dict) -> str:
    parts = [f"Source: {(doc.title or doc.file_name) if doc else 'Document'}"]
    section = payload.get("section_label") or payload.get("section_number") or _extract_section_label(payload.get("text"))
    if section:
        parts.append(f"Section: {section}")
    if payload.get("page_number"):
        parts.append(f"Page: {payload.get('page_number')}")
    return "[" + "; ".join(parts) + "]"

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
    sys_identity = f"{get_system_identity(chat_request.language)}\n\n{mode_instruction(mode)}"
    if chat_request.image:
        from ..services.llm_service import async_call_vision_llm
        answer = await async_call_vision_llm(f"{sys_identity}\n\n{chat_request.message}", chat_request.image)
        sources = []
    else:
        active_doc_ids = _session_active_document_ids(session, chat_request.active_document_ids)
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
        )
        if answer == NOT_FOUND_RESPONSE and mode not in SOURCE_REQUIRED_MODES:
            answer = await async_call_llm(
                safe_message,
                system=general_fallback_system_identity(chat_request.language, mode),
                user_id=current_user.id,
                role=current_user.role,
            )
            sources = []

    citation_verification = verify_answer_against_sources(answer=answer, sources=sources)
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
            "llm_received_masked_input": True,
            "sources_count": len(sources),
            "answer_type": answer_metadata["answer_type"],
            "mode": mode,
            "citation_verification": citation_verification,
            "rewritten_query": retrieval_query if retrieval_query != safe_message else None,
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

        if should_show_document_search_status(active_document_ids=active_doc_ids, mode=mode, has_image=has_image):
            status_message = "Searching selected documents..." if active_doc_ids else "Searching approved knowledge..."
            yield f"data: {json.dumps({'type': 'status', 'message': status_message})}\n\n"

        sources_list = []
        sys_identity = f"{get_system_identity(chat_request.language)}\n\n{mode_instruction(mode)}"
        logger.info("[STREAM] Got system identity")

        if not has_image:
            try:
                logger.info("[STREAM] Starting RAG search")
                from ..services.embedding_service import generate_embeddings
                from ..services.qdrant_service import search_points
                from ..models.document import Document

                logger.info(f"[STREAM] Generating embeddings for query: {retrieval_query[:50]}")
                embeddings = await asyncio.to_thread(generate_embeddings, [retrieval_query])
                query_vector = embeddings[0]
                logger.info("[STREAM] Embeddings generated")

                session_results = []
                if active_doc_ids:
                    session_results = search_points(
                        query_vector,
                        current_user.bank_id,
                        limit=MAX_CANDIDATE_RESULTS,
                        document_ids=active_doc_ids,
                        session_id=session_id,
                        document_scope="session_upload",
                        document_statuses=SESSION_RETRIEVAL_STATUSES,
                    )

                allow_global_mix = not active_doc_ids or not session_results or _should_mix_global_knowledge(safe_message)
                global_limit = MAX_CANDIDATE_RESULTS if allow_global_mix else 0
                global_results = []
                if global_limit > 0:
                    global_results = search_points(
                        query_vector,
                        current_user.bank_id,
                        limit=global_limit,
                        document_scope="global_knowledge",
                        document_statuses=GLOBAL_RETRIEVAL_STATUSES,
                        version_states=GLOBAL_RETRIEVAL_VERSION_STATES,
                    )
                    seen = {r.payload.get("document_id") for r in session_results if r.payload}
                    global_results = [r for r in global_results if r.payload and r.payload.get("document_id") not in seen]

                results = session_results + global_results

                if results:
                    doc_ids = list(set(r.payload.get("document_id") for r in results if r.payload))
                    allowed_docs = set()
                    for doc_id in doc_ids:
                        doc = db.get(Document, doc_id)
                        if doc and _document_visible_to_user(
                            doc,
                            session_id,
                            current_user.role,
                            current_user.department,
                        ):
                            allowed_docs.add(doc_id)

                    filtered = _rerank_results(retrieval_query, [
                        r for r in results
                        if r.payload
                        and r.payload.get("document_id") in allowed_docs
                        and r.score >= MIN_SOURCE_RELEVANCE_SCORE
                    ])

                    if filtered:
                        context_blocks = []
                        for r in filtered:
                            doc = db.get(Document, r.payload.get("document_id"))
                            context_blocks.append(f"{_source_prefix(doc, r.payload)}\n{r.payload.get('text', '')}")
                        context = "\n\n---\n\n".join(context_blocks)
                        sys_identity += (
                            f"\n\n--- DOCUMENT CONTEXT ---\n"
                            f"Use the following context from approved documents to answer the user's question.\n\n"
                            f"{context}\n--- END DOCUMENT CONTEXT ---"
                        )
                        seen_src: set[tuple] = set()
                        for r in filtered:
                            doc_id = r.payload.get("document_id")
                            section_label = (
                                r.payload.get("section_label")
                                or r.payload.get("section_number")
                                or _extract_section_label(r.payload.get("text"))
                            )
                            source_key = (doc_id, r.payload.get("page_number"), section_label, r.payload.get("chunk_index"))
                            if doc_id and source_key not in seen_src:
                                doc = db.get(Document, doc_id)
                                passage = r.payload.get("text", "")
                                sources_list.append({
                                    "document_id":    doc_id,
                                    "document_title": (doc.title or doc.file_name) if doc else "Database Source",
                                    "title":          (doc.title or doc.file_name) if doc else "Database Source",
                                    "document_type":  doc.document_type if doc else None,
                                    "department":     doc.department if doc else None,
                                    "snippet":        passage[:180],
                                    "passage":        passage,
                                    "page_number":    r.payload.get("page_number"),
                                    "section_label":  section_label,
                                    "section_number": section_label,
                                    "chunk_index":    r.payload.get("chunk_index"),
                                    "relevance_score": r.score,
                                })
                                seen_src.add(source_key)
            except Exception as e:
                logger.error(f"RAG failed in stream: {e}")

        logger.info("[STREAM] About to yield prepare status")
        yield f"data: {json.dumps({'type': 'status', 'message': 'Generating response...'})}\n\n"

        if not has_image and mode in SOURCE_REQUIRED_MODES and not sources_list:
            full_response = NOT_FOUND_RESPONSE
            yield f"data: {json.dumps({'token': full_response})}\n\n"
            suggestions = []
            citation_verification = verify_answer_against_sources(answer=full_response, sources=sources_list)
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

        vllm_messages = [{"role": "system", "content": sys_identity}]
        for msg in history[-10:]:
            vllm_messages.append({
                "role": "assistant" if msg.role == "assistant" else "user",
                "content": msg.content,
            })

        selected_profile = resolve_model_profile(chat_request.model_override)
        status = await model_status()
        selected_status = status.get(selected_profile.key, {})
        if selected_status.get("active", 0) >= selected_status.get("limit", 1):
            yield f"data: {json.dumps({'type': 'status', 'message': 'All model workers are busy. Your request is queued.'})}\n\n"

        full_response = ""
        try:
            async with reserve_model(
                user_id=current_user.id,
                role=current_user.role,
                model_name=chat_request.model_override,
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
                    "max_tokens": profile.max_tokens,
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
                            yield f"data: {json.dumps({'token': f'AI engine returned error {response.status_code}.', 'done': True})}\n\n"
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
            citation_verification = verify_answer_against_sources(answer=full_response, sources=sources_list)
            sources_list = attach_source_verification(sources_list, citation_verification)
            answer_metadata = derive_answer_metadata(
                mode=mode,
                sources=sources_list,
                active_document_ids=active_doc_ids,
                answer=full_response,
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
                    "llm_received_masked_input": True,
                    "sources_count": len(sources_list),
                    "answer_type": answer_metadata["answer_type"],
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
            citation_verification=verify_answer_against_sources(answer=full_response, sources=sources_list),
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
        from ..services.ingestion_service import extract_text
        extracted = extract_text(file_path, file_ext)
        if not extracted.strip():
            extracted = "(No text could be extracted from this file)"
        if len(extracted) > 8000:
            extracted = extracted[:8000] + "\n\n... (truncated)"
        vllm_messages.append({
            "role": "user",
            "content": f"I have uploaded \"{file.filename}\".\n\n--- FILE CONTENT ---\n{extracted}\n--- END FILE CONTENT ---\n\nMy request: {message}"
        })

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
                model_name=None,
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
                }])
            )
            db.add(ai_msg)
            db.commit()
            _update_session_summary(session, message, full_response, db)
        except Exception as e:
            logger.error(f"[STREAM-FILE] Error saving message: {e}")

        yield f"data: {json.dumps({'done': True, 'id': doc.id, 'document_id': doc.id})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
