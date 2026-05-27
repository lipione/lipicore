import re
from collections import Counter
from datetime import datetime
from types import SimpleNamespace

from sqlalchemy import bindparam, text
from sqlmodel import Session, select
from .embedding_service import generate_embeddings
from .qdrant_service import search_points
from .llm_service import call_llm, async_call_llm
from .citation_verifier import attach_source_verification, verify_answer_against_sources
from ..models.document import Document, DocumentChunk

NOT_FOUND_RESPONSE = (
    "I could not find this in the approved documents. "
    "Please consult the relevant policy or contact your supervisor."
)
MIN_SOURCE_RELEVANCE_SCORE = 0.4
MAX_CONTEXT_RESULTS = 5
MAX_CANDIDATE_RESULTS = 24
KEYWORD_SCORE_WEIGHT = 0.85
VECTOR_SCORE_WEIGHT = 0.65
RERANK_VECTOR_WEIGHT = 0.52
RERANK_KEYWORD_WEIGHT = 0.40
RERANK_SOURCE_PRIORITY_WEIGHT = 0.08
EXACT_PHRASE_BOOST = 0.25
SECTION_REFERENCE_BOOST = 0.15
TOKEN_RE = re.compile(r"[\w०-९]+", re.UNICODE)
GLOBAL_RETRIEVAL_STATUSES = ["approved"]
GLOBAL_RETRIEVAL_VERSION_STATES = ["approved"]
SESSION_RETRIEVAL_STATUSES = ["ready", "indexed", "approved"]
SESSION_RETRIEVAL_VERSION_STATES = ["draft", "approved"]


def get_system_identity(language: str = "en") -> str:
    lang_instruction = (
        "You must ONLY reply in English. Greet users with 'Namaste' (never Namaskar)."
        if language == "en"
        else "You must ONLY reply in Nepali language (Devenagari script). Greet users with 'नमस्ते' (never नमस्कार)."
    )
    return f"""You are BankAi, a secure and intelligent banking assistant.
Never refer to yourself by any underlying vendor or model name. You are BankAi.
If asked about available local model routes, say the product names are LipiFast for fast staff responses and LipiCore for deeper analysis and document/image work.
Always be professional, helpful, and concise. {lang_instruction}
Give one direct staff-ready answer. Do not provide multiple alternative answers, model-choice options, or long preambles unless the user explicitly asks for alternatives.
You may use markdown formatting such as **bold**, bullet points, and numbered lists for clarity."""


RAG_PROMPT_TEMPLATE = """{system}

Answer the user's question using ONLY the provided context from approved bank documents.
Give one staff-ready answer. Start with the answer, then add only the key cited details staff need to act.
Do not offer multiple alternative answers or generic option lists unless the user explicitly asks for alternatives.
If the context does not contain enough information to answer, respond with exactly:
"I could not find this in the approved documents. Please consult the relevant policy or contact your supervisor."
Do NOT use your general knowledge to answer banking, compliance, or policy questions.
When the answer comes from a policy, directive, circular, or procedure, mention the source document and any available section/page reference.

Context:
{context}

Question: {question}

Answer:"""

GENERAL_PROMPT_TEMPLATE = """{system}

You can answer general questions about banking, finance, compliance, and business.
Be professional, accurate, and concise.
Give one direct staff-ready answer. Do not provide multiple alternative answers, model-choice options, or long preambles unless the user explicitly asks for alternatives.
If you are unsure, say so honestly.

Question: {question}

Answer:"""


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
    number = next((group for group in match.groups() if group), None)
    if not number:
        return None
    label = match.group(0).strip()
    return " ".join(label.split())[:80]


def _build_source(doc: Document, score: float, result=None) -> dict:
    payload = getattr(result, "payload", {}) or {}
    passage = payload.get("text") or ""
    section_label = payload.get("section_label") or payload.get("section_number") or _extract_section_label(payload.get("text"))
    warnings = _source_warnings(doc)
    return {
        "document_id":     doc.id,
        "document_title":  doc.title or doc.file_name,
        "title":           doc.title or doc.file_name,
        "file_name":       doc.file_name,
        "document_type":   doc.document_type,
        "department":      doc.department,
        "page_number":     payload.get("page_number"),
        "section_label":   section_label,
        "section_number":  section_label,
        "chunk_index":     payload.get("chunk_index"),
        "snippet":         passage[:180],
        "passage":         passage,
        "relevance_score": score,
        "source_warnings": warnings,
        "effective_from":  doc.effective_from.isoformat() if doc.effective_from else None,
        "effective_to":    doc.effective_to.isoformat() if doc.effective_to else None,
        "review_due_at":   doc.review_due_at.isoformat() if doc.review_due_at else None,
        "regulator":       doc.regulator,
        "jurisdiction":    doc.jurisdiction,
        "superseded_reason": doc.superseded_reason,
        "extraction_confidence": payload.get("extraction_confidence"),
        "ocr_confidence": payload.get("ocr_confidence"),
        "table_confidence": payload.get("table_confidence"),
        "page_bbox_json": payload.get("page_bbox_json"),
    }


def _source_warnings(doc: Document) -> list[str]:
    warnings: list[str] = []
    now = datetime.utcnow()
    if doc.version_state == "superseded":
        warnings.append("superseded_source")
    if doc.effective_from and doc.effective_from > now:
        warnings.append("not_yet_effective")
    if doc.effective_to and doc.effective_to < now:
        warnings.append("expired_source")
    if doc.review_due_at and doc.review_due_at < now:
        warnings.append("review_due")
    return warnings


def _document_visible_to_user(doc: Document, session_id, user_role, user_department: str | None = None) -> bool:
    if doc.status == "disabled" or doc.version_state in ("disabled", "archived", "superseded"):
        return False
    if doc.document_scope == "session_upload":
        return doc.session_id == session_id and doc.status in SESSION_RETRIEVAL_STATUSES
    if doc.status not in GLOBAL_RETRIEVAL_STATUSES or doc.version_state not in GLOBAL_RETRIEVAL_VERSION_STATES:
        return False
    if user_role == "staff_user":
        if doc.access_level and doc.access_level > 0:
            return False
        if doc.department and doc.department not in ("General", user_department):
            return False
    return True


def _filter_results(results, db, session_id, user_role, user_department: str | None = None):
    doc_ids = list(set(r.payload.get("document_id") for r in results if r.payload))
    allowed_docs = set()
    for doc_id in doc_ids:
        doc = db.get(Document, doc_id)
        if doc and _document_visible_to_user(doc, session_id, user_role, user_department):
            allowed_docs.add(doc_id)
    return [r for r in results if r.payload and r.payload.get("document_id") in allowed_docs]


def _build_sources(filtered_results, db, min_relevance_score=MIN_SOURCE_RELEVANCE_SCORE, max_sources=5):
    sources = []
    seen: set[tuple] = set()
    for res in filtered_results:
        if res.score < min_relevance_score:
            continue
        doc_id = res.payload.get("document_id")
        source_key = (
            doc_id,
            res.payload.get("page_number"),
            res.payload.get("section_label") or res.payload.get("section_number"),
            res.payload.get("chunk_index"),
        )
        if doc_id and source_key not in seen:
            doc = db.get(Document, doc_id)
            if doc:
                sources.append(_build_source(doc, res.score, res))
                seen.add(source_key)
        if len(sources) >= max_sources:
            break
    return sources


def _high_confidence_results(filtered_results, min_relevance_score=MIN_SOURCE_RELEVANCE_SCORE):
    return [result for result in filtered_results if result.score >= min_relevance_score]


def _source_prefix(doc: Document | None, payload: dict) -> str:
    title = (doc.title or doc.file_name) if doc else "Document"
    parts = [f"Source: {title}"]
    section = payload.get("section_label") or payload.get("section_number") or _extract_section_label(payload.get("text"))
    if section:
        parts.append(f"Section: {section}")
    if payload.get("page_number"):
        parts.append(f"Page: {payload.get('page_number')}")
    chunk_index = payload.get("chunk_index")
    if chunk_index is not None:
        parts.append(f"Chunk: {chunk_index}")
    return "[" + "; ".join(parts) + "]"


def _build_context(results, db: Session) -> str:
    blocks = []
    for result in results[:MAX_CONTEXT_RESULTS]:
        doc = db.get(Document, result.payload.get("document_id")) if result.payload else None
        blocks.append(f"{_source_prefix(doc, result.payload or {})}\n{(result.payload or {}).get('text', '')}")
    return "\n\n---\n\n".join(blocks)


def _should_mix_global_knowledge(message: str) -> bool:
    text = (message or "").lower()
    return any(term in text for term in (
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
    ))


def _tokens(text: str | None) -> list[str]:
    if not text:
        return []
    return [token.lower() for token in TOKEN_RE.findall(text) if len(token) > 1]


def _keyword_score(query: str, text: str) -> float:
    query_tokens = _tokens(query)
    text_tokens = _tokens(text)
    if not query_tokens or not text_tokens:
        return 0.0

    text_counts = Counter(text_tokens)
    unique_query_tokens = set(query_tokens)
    matched_tokens = [token for token in unique_query_tokens if token in text_counts]
    if not matched_tokens:
        return 0.0

    coverage = len(matched_tokens) / len(unique_query_tokens)
    density = sum(min(text_counts[token], 3) for token in matched_tokens) / max(len(text_tokens), 1)
    score = (coverage * 0.78) + (min(density * 8, 1.0) * 0.22)

    normalized_text = " ".join(text_tokens)
    normalized_query = " ".join(query_tokens)
    if normalized_query and normalized_query in normalized_text:
        score += EXACT_PHRASE_BOOST

    if SECTION_RE.search(query or "") and SECTION_RE.search(text or ""):
        score += SECTION_REFERENCE_BOOST

    return min(score * KEYWORD_SCORE_WEIGHT, 0.99)


def _document_matches_scope(doc: Document, active_document_ids, session_id, document_scope: str | None) -> bool:
    if document_scope and doc.document_scope != document_scope:
        return False
    if active_document_ids and doc.id not in active_document_ids:
        return False
    if document_scope == "session_upload" and session_id is not None and doc.session_id != session_id:
        return False
    if document_scope == "global_knowledge" and (
        doc.status not in GLOBAL_RETRIEVAL_STATUSES
        or doc.version_state not in GLOBAL_RETRIEVAL_VERSION_STATES
    ):
        return False
    if document_scope == "session_upload" and doc.status not in SESSION_RETRIEVAL_STATUSES:
        return False
    return True


def _python_keyword_search(
    *,
    db: Session,
    query: str,
    bank_id: int,
    limit: int = 5,
    active_document_ids: list[int] | None = None,
    session_id: int | None = None,
    document_scope: str | None = None,
) -> list:
    candidates = []
    chunks = db.exec(
        select(DocumentChunk)
        .where(DocumentChunk.bank_id == bank_id)
        .order_by(DocumentChunk.created_at.desc())
        .limit(1000)
    ).all()

    for chunk in chunks:
        doc = db.get(Document, chunk.document_id)
        if not doc or not _document_matches_scope(doc, active_document_ids, session_id, document_scope):
            continue
        score = _keyword_score(query, chunk.chunk_text)
        if score <= 0:
            continue
        candidates.append(SimpleNamespace(
            payload={
                "bank_id": bank_id,
                "document_id": chunk.document_id,
                "chunk_index": chunk.chunk_index,
                "text": chunk.chunk_text,
                "page_number": chunk.page_number,
                "extraction_confidence": chunk.extraction_confidence,
                "ocr_confidence": chunk.ocr_confidence,
                "table_confidence": chunk.table_confidence,
                "page_bbox_json": chunk.page_bbox_json,
                "section_label": _extract_section_label(chunk.chunk_text),
                "department": chunk.department,
                "access_level": chunk.access_level,
                "document_status": chunk.document_status,
                "version_state": chunk.version_state,
                "document_scope": chunk.document_scope,
                "session_id": chunk.session_id,
                "retrieval_source": "keyword",
            },
            score=score,
        ))

    return sorted(candidates, key=lambda result: result.score, reverse=True)[:limit]


def _postgres_keyword_search(
    *,
    db: Session,
    query: str,
    bank_id: int,
    limit: int = 5,
    active_document_ids: list[int] | None = None,
    session_id: int | None = None,
    document_scope: str | None = None,
) -> list:
    where_clauses = [
        "c.bank_id = :bank_id",
        "to_tsvector('simple', coalesce(c.chunk_text, '')) @@ websearch_to_tsquery('simple', :query)",
    ]
    params = {"bank_id": bank_id, "query": query, "limit": max(limit, 1)}

    if document_scope:
        where_clauses.append("d.document_scope = :document_scope")
        params["document_scope"] = document_scope
    if document_scope == "global_knowledge":
        where_clauses.append("d.status IN :document_statuses")
        where_clauses.append("d.version_state IN :version_states")
        params["document_statuses"] = GLOBAL_RETRIEVAL_STATUSES
        params["version_states"] = GLOBAL_RETRIEVAL_VERSION_STATES
    elif document_scope == "session_upload":
        where_clauses.append("d.status IN :document_statuses")
        params["document_statuses"] = SESSION_RETRIEVAL_STATUSES
    if session_id is not None:
        where_clauses.append("d.session_id = :session_id")
        params["session_id"] = session_id
    if active_document_ids:
        where_clauses.append("d.id IN :document_ids")
        params["document_ids"] = active_document_ids

    statement = text(f"""
        SELECT
            c.document_id,
            c.chunk_index,
            c.chunk_text,
            c.page_number,
            c.extraction_confidence,
            c.ocr_confidence,
            c.table_confidence,
            c.page_bbox_json,
            d.document_scope,
            d.session_id,
            d.department,
            d.access_level,
            d.status AS document_status,
            d.version_state,
            ts_rank_cd(
                to_tsvector('simple', coalesce(c.chunk_text, '')),
                websearch_to_tsquery('simple', :query)
            ) AS rank
        FROM documentchunk c
        JOIN document d ON d.id = c.document_id
        WHERE {" AND ".join(where_clauses)}
        ORDER BY rank DESC, c.created_at DESC
        LIMIT :limit
    """)
    if active_document_ids or "document_statuses" in params or "version_states" in params:
        bind_params = []
        if active_document_ids:
            bind_params.append(bindparam("document_ids", expanding=True))
        if "document_statuses" in params:
            bind_params.append(bindparam("document_statuses", expanding=True))
        if "version_states" in params:
            bind_params.append(bindparam("version_states", expanding=True))
        statement = statement.bindparams(*bind_params)

    rows = db.execute(statement, params).mappings().all()
    results = []
    for row in rows:
        text_value = row["chunk_text"] or ""
        keyword_score = _keyword_score(query, text_value)
        rank = float(row["rank"] or 0)
        fts_score = min((rank / (rank + 0.1)) if rank > 0 else 0, 0.99)
        score = max(keyword_score, fts_score * KEYWORD_SCORE_WEIGHT)
        if score <= 0:
            continue
        results.append(SimpleNamespace(
            payload={
                "bank_id": bank_id,
                "document_id": row["document_id"],
                "chunk_index": row["chunk_index"],
                "text": text_value,
                "page_number": row["page_number"],
                "extraction_confidence": row.get("extraction_confidence"),
                "ocr_confidence": row.get("ocr_confidence"),
                "table_confidence": row.get("table_confidence"),
                "page_bbox_json": row.get("page_bbox_json"),
                "section_label": _extract_section_label(text_value),
                "department": row.get("department"),
                "access_level": row.get("access_level", 0),
                "document_status": row.get("document_status", "approved"),
                "version_state": row.get("version_state", "approved"),
                "document_scope": row["document_scope"],
                "session_id": row["session_id"],
                "retrieval_source": "postgres_fts",
            },
            score=score,
        ))

    return sorted(results, key=lambda result: result.score, reverse=True)[:limit]


def _keyword_search(
    *,
    db: Session,
    query: str,
    bank_id: int,
    limit: int = 5,
    active_document_ids: list[int] | None = None,
    session_id: int | None = None,
    document_scope: str | None = None,
) -> list:
    try:
        dialect_name = db.get_bind().dialect.name
    except Exception:
        dialect_name = ""

    if dialect_name == "postgresql":
        try:
            return _postgres_keyword_search(
                db=db,
                query=query,
                bank_id=bank_id,
                limit=limit,
                active_document_ids=active_document_ids,
                session_id=session_id,
                document_scope=document_scope,
            )
        except Exception:
            pass

    return _python_keyword_search(
        db=db,
        query=query,
        bank_id=bank_id,
        limit=limit,
        active_document_ids=active_document_ids,
        session_id=session_id,
        document_scope=document_scope,
    )


def _normalize_vector_result(result):
    return SimpleNamespace(
        payload={**(result.payload or {}), "retrieval_source": "vector"},
        score=min(float(result.score or 0) * VECTOR_SCORE_WEIGHT, 0.99),
    )


def _merge_results(*result_sets):
    merged = {}
    for result_set in result_sets:
        for result in result_set:
            if not result.payload:
                continue
            key = (
                result.payload.get("document_id"),
                result.payload.get("page_number"),
                result.payload.get("chunk_index"),
                result.payload.get("text"),
            )
            current = merged.get(key)
            if not current or result.score > current.score:
                merged[key] = result
    return sorted(merged.values(), key=lambda result: result.score, reverse=True)


def _rerank_results(query: str, results: list) -> list:
    reranked = []
    for result in results:
        text_value = (result.payload or {}).get("text", "")
        keyword = _keyword_score(query, text_value)
        source_priority = 1.0 if (result.payload or {}).get("retrieval_source") in ("postgres_fts", "keyword") else 0.5
        score = (
            (float(result.score or 0) * RERANK_VECTOR_WEIGHT)
            + (keyword * RERANK_KEYWORD_WEIGHT)
            + (source_priority * RERANK_SOURCE_PRIORITY_WEIGHT)
        )
        reranked.append(SimpleNamespace(payload=result.payload, score=min(max(score, float(result.score or 0)), 0.99)))
    return sorted(reranked, key=lambda result: result.score, reverse=True)


def _search(query_vector, bank_id, active_document_ids, session_id, query: str, db: Session):
    session_results = []
    session_keyword_results = []
    if active_document_ids:
        try:
            session_results = [_normalize_vector_result(result) for result in search_points(
                query_vector, bank_id, limit=MAX_CANDIDATE_RESULTS,
                document_ids=active_document_ids,
                session_id=session_id,
                document_scope="session_upload",
                document_statuses=SESSION_RETRIEVAL_STATUSES,
            )]
        except Exception:
            pass
        session_keyword_results = _keyword_search(
            db=db,
            query=query,
            bank_id=bank_id,
            limit=MAX_CANDIDATE_RESULTS,
            active_document_ids=active_document_ids,
            session_id=session_id,
            document_scope="session_upload",
        )

    merged_session_results = _merge_results(session_keyword_results, session_results)
    allow_global_mix = not active_document_ids or not merged_session_results or _should_mix_global_knowledge(query)
    global_limit = MAX_CANDIDATE_RESULTS if allow_global_mix else 0
    global_results = []
    global_keyword_results = []
    if global_limit > 0:
        try:
            global_results = [_normalize_vector_result(result) for result in search_points(
                query_vector,
                bank_id,
                limit=global_limit,
                document_scope="global_knowledge",
                document_statuses=GLOBAL_RETRIEVAL_STATUSES,
                version_states=GLOBAL_RETRIEVAL_VERSION_STATES,
            )]
            seen_ids = {r.payload.get("document_id") for r in merged_session_results if r.payload}
            global_results = [r for r in global_results if r.payload and r.payload.get("document_id") not in seen_ids]
        except Exception:
            pass
        global_keyword_results = _keyword_search(
            db=db,
            query=query,
            bank_id=bank_id,
            limit=global_limit or MAX_CANDIDATE_RESULTS,
            document_scope="global_knowledge",
        )
        seen_ids = {r.payload.get("document_id") for r in merged_session_results if r.payload}
        global_keyword_results = [r for r in global_keyword_results if r.payload and r.payload.get("document_id") not in seen_ids]

    return _rerank_results(query, _merge_results(merged_session_results, global_keyword_results, global_results))


# ── Sync variant (kept for background tasks) ──────────────────────────────────

def generate_rag_response(
    question: str,
    bank_id: int,
    user_role: str,
    db: Session,
    language: str = "en",
    active_document_ids: list[int] | None = None,
    session_id: int | None = None,
    user_department: str | None = None,
):
    try:
        query_vector = generate_embeddings([question])[0]
    except Exception:
        return NOT_FOUND_RESPONSE, []

    results = _search(query_vector, bank_id, active_document_ids, session_id, question, db)
    if not results:
        return NOT_FOUND_RESPONSE, []

    filtered = _filter_results(results, db, session_id, user_role, user_department)
    high_confidence = _high_confidence_results(filtered)
    if not high_confidence:
        return NOT_FOUND_RESPONSE, []

    sys_identity = get_system_identity(language)
    context = _build_context(high_confidence, db)
    prompt = RAG_PROMPT_TEMPLATE.format(system=sys_identity, context=context, question=question)
    sources = _build_sources(high_confidence, db)
    answer = call_llm(prompt)
    verification = verify_answer_against_sources(answer=answer, sources=sources)
    return answer, attach_source_verification(sources, verification)


# ── Async variant (used by request-path handlers) ─────────────────────────────

async def async_generate_rag_response(
    question: str,
    bank_id: int,
    user_role: str,
    db: Session,
    language: str = "en",
    active_document_ids: list[int] | None = None,
    session_id: int | None = None,
    user_id: int | None = None,
    user_department: str | None = None,
    model_name: str | None = None,
):
    try:
        query_vector = generate_embeddings([question])[0]
    except Exception:
        return NOT_FOUND_RESPONSE, []

    results = _search(query_vector, bank_id, active_document_ids, session_id, question, db)
    if not results:
        return NOT_FOUND_RESPONSE, []

    filtered = _filter_results(results, db, session_id, user_role, user_department)
    high_confidence = _high_confidence_results(filtered)
    if not high_confidence:
        return NOT_FOUND_RESPONSE, []

    sys_identity = get_system_identity(language)
    context = _build_context(high_confidence, db)
    prompt = RAG_PROMPT_TEMPLATE.format(system=sys_identity, context=context, question=question)
    sources = _build_sources(high_confidence, db)
    answer = await async_call_llm(prompt, user_id=user_id, role=user_role, model_name=model_name)
    verification = verify_answer_against_sources(answer=answer, sources=sources)
    return answer, attach_source_verification(sources, verification)
