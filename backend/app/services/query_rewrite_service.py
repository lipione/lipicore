import json
import re
from typing import Iterable

from ..models.chat import ChatMessage
from .llm_service import call_llm


FOLLOW_UP_HINTS = {
    "it",
    "its",
    "this",
    "that",
    "they",
    "them",
    "those",
    "above",
    "same",
    "previous",
    "what about",
    "how about",
    "explain more",
    "compare",
}

SOURCE_LOOKUP_HINTS = {
    "quote",
    "cite",
    "citation",
    "source",
    "reference",
    "exact",
    "exait",
}

SOURCE_LOOKUP_PHRASES = {
    "exact policy",
    "exait policy",
    "quote me",
    "cite me",
    "show source",
    "show me source",
    "which source",
    "what source",
    "which policy",
    "legal provision",
}


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def _recent_history_text(history: Iterable[ChatMessage], limit: int = 6) -> str:
    lines = []
    for msg in list(history)[-limit:]:
        role = "Assistant" if msg.role == "assistant" else "User"
        content = _normalize_text(msg.content or "")
        if content:
            lines.append(f"{role}: {content[:700]}")
    return "\n".join(lines)


def _looks_like_source_lookup_follow_up(question: str) -> bool:
    q = _normalize_text(question).lower()
    if not q:
        return False
    if any(phrase in q for phrase in SOURCE_LOOKUP_PHRASES):
        return True
    return len(q.split()) <= 7 and any(hint in q for hint in SOURCE_LOOKUP_HINTS)


def looks_like_follow_up(question: str) -> bool:
    q = _normalize_text(question).lower()
    has_hint = any(hint in q for hint in FOLLOW_UP_HINTS)
    has_source_lookup_hint = _looks_like_source_lookup_follow_up(q)
    # Only trigger on short queries when they also contain a reference pronoun/hint,
    # not for short self-contained questions like "What is KYC?"
    if len(q.split()) <= 7 and (has_hint or has_source_lookup_hint):
        return True
    return has_hint or has_source_lookup_hint


def _subject_from_user_message(content: str) -> str:
    subject = _normalize_text(content).strip(" ?.!:")
    subject = re.sub(
        r"^(please\s+)?(tell|explain|describe|summarize)\s+(me\s+)?(about\s+)?",
        "",
        subject,
        flags=re.IGNORECASE,
    )
    subject = re.sub(
        r"^(what|which)\s+(is|are|was|were)\s+",
        "",
        subject,
        flags=re.IGNORECASE,
    )
    subject = re.sub(r"^define\s+", "", subject, flags=re.IGNORECASE)
    return subject.strip(" ?.!:")


def _last_user_subject(history: Iterable[ChatMessage]) -> str:
    for msg in reversed(list(history)):
        if msg.role != "user":
            continue
        subject = _subject_from_user_message(msg.content or "")
        if subject:
            return subject[:180]
    return ""


def _fallback_rewrite(question: str, history: Iterable[ChatMessage]) -> str:
    if not _looks_like_source_lookup_follow_up(question):
        return question
    subject = _last_user_subject(history)
    normalized_question = _normalize_text(question)
    if not subject or subject.lower() in normalized_question.lower():
        return normalized_question or question
    return f"{normalized_question} about {subject}"


def rewrite_query_for_retrieval(question: str, history: list[ChatMessage] | None) -> str:
    """
    Convert short follow-up questions into standalone retrieval queries.
    Falls back to the original question if rewriting fails or is unnecessary.
    """
    if not history or not looks_like_follow_up(question):
        return question

    history_text = _recent_history_text(history)
    if not history_text:
        return question

    prompt = f"""Rewrite the user's latest question as one standalone search query for banking document retrieval.
Keep the user's intent. Include relevant subjects from the conversation history. Do not answer the question.
Return JSON only in this shape: {{"query":"..."}}

Conversation:
{history_text}

Latest question: {question}
"""

    try:
        raw = call_llm(prompt)
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        payload = json.loads(match.group(0) if match else raw)
        rewritten = str(payload.get("query", "")).strip()
        if rewritten and rewritten.lower() != _normalize_text(question).lower():
            return rewritten
        return _fallback_rewrite(question, history)
    except Exception as exc:
        print(f"Query rewrite failed: {exc}")
        return _fallback_rewrite(question, history)
