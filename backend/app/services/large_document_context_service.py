import re
from typing import Any

from .ingestion_service import build_indexable_chunks


APPROX_CHARS_PER_TOKEN = 3
CONTEXT_OVERHEAD_TOKENS = 256
TOKEN_RE = re.compile(r"[\w०-९]+", re.UNICODE)


def _tokens(text: str | None) -> set[str]:
    return {token.lower() for token in TOKEN_RE.findall(text or "") if len(token) > 1}


def _score_chunk(question: str, chunk: dict[str, Any]) -> float:
    query_tokens = _tokens(question)
    text_tokens = _tokens(chunk.get("text"))
    if not query_tokens or not text_tokens:
        return 0
    overlap = query_tokens & text_tokens
    score = len(overlap) / len(query_tokens)
    normalized_query = " ".join(sorted(query_tokens))
    if normalized_query and normalized_query in " ".join(sorted(text_tokens)):
        score += 0.25
    if chunk.get("section_label"):
        score += 0.05
    return score


def select_relevant_file_chunks(
    *,
    pages: list[dict],
    question: str,
    max_chars: int,
    chunk_size: int = 1400,
    chunk_overlap: int = 160,
) -> list[dict]:
    chunks = build_indexable_chunks(pages, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    if not chunks:
        return []

    scored = [
        {
            **chunk,
            "score": _score_chunk(question, chunk),
            "original_index": index,
        }
        for index, chunk in enumerate(chunks)
    ]
    ranked = sorted(scored, key=lambda item: (item["score"], -item["original_index"]), reverse=True)
    if any(item["score"] > 0 for item in ranked):
        ranked = [item for item in ranked if item["score"] > 0]
    else:
        ranked = [scored[0], *(scored[-1:] if len(scored) > 1 else [])]

    selected: list[dict] = []
    used = 0
    seen = set()
    for chunk in ranked:
        key = (chunk.get("page_number"), chunk.get("original_index"))
        if key in seen:
            continue
        text = chunk.get("text") or ""
        projected = used + len(text)
        if selected and projected > max_chars:
            continue
        selected.append(chunk)
        seen.add(key)
        used += len(text)
        if used >= max_chars:
            break

    return selected


def _source_label(chunk: dict[str, Any]) -> str:
    parts = []
    if chunk.get("page_number") is not None:
        parts.append(f"Page {chunk['page_number']}")
    if chunk.get("section_label"):
        parts.append(str(chunk["section_label"]))
    if not parts:
        parts.append("Document excerpt")
    return " / ".join(parts)


def build_large_file_prompt(
    *,
    file_name: str,
    user_request: str,
    pages: list[dict],
    context_window_tokens: int,
    output_tokens: int,
) -> tuple[str, dict[str, Any]]:
    input_budget_tokens = max(512, context_window_tokens - output_tokens - CONTEXT_OVERHEAD_TOKENS)
    input_budget_chars = max(1200, input_budget_tokens * APPROX_CHARS_PER_TOKEN)
    total_chars = sum(len(page.get("text") or "") for page in pages)
    chunks = build_indexable_chunks(pages, chunk_size=1400, chunk_overlap=160)
    selected = select_relevant_file_chunks(
        pages=pages,
        question=user_request,
        max_chars=max(800, input_budget_chars - 1400),
    )

    context_blocks = []
    for chunk in selected:
        context_blocks.append(f"[{_source_label(chunk)}]\n{chunk.get('text', '').strip()}")
    context = "\n\n---\n\n".join(context_blocks)
    selected_chars = sum(len(chunk.get("text") or "") for chunk in selected)
    shortened = selected_chars < total_chars or len(selected) < len(chunks)
    notice = (
        "Content was shortened to fit the local model context. The excerpts below were selected by relevance and page/section metadata."
        if shortened
        else "Full extracted content fits the local model context."
    )
    prompt = (
        f"I uploaded \"{file_name}\".\n\n"
        f"{notice}\n"
        f"Total extracted characters: {total_chars}. Selected excerpts: {len(selected)}.\n\n"
        f"--- FILE EXCERPTS ---\n{context}\n--- END FILE EXCERPTS ---\n\n"
        f"My request: {user_request}\n\n"
        "Answer using the excerpts above. Cite page or section labels when available. "
        "If the selected excerpts do not contain the answer, say what is missing instead of guessing."
    )
    return prompt, {
        "input_budget_chars": input_budget_chars,
        "total_chars": total_chars,
        "selected_chars": selected_chars,
        "total_chunks": len(chunks),
        "selected_chunks": len(selected),
        "shortened": shortened,
    }
