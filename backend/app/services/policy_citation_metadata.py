from __future__ import annotations

import re
from typing import Any

from .legal_reference_parser import legal_hierarchy_path, parse_legal_hierarchy


POLICY_DOCUMENT_TYPES = {
    "policy",
    "procedure",
    "manual",
    "compliance",
    "circular",
    "directive",
    "law",
    "act",
    "sop",
}

COMMON_SENTENCE_VERBS = {
    "allows",
    "applies",
    "approve",
    "approved",
    "approves",
    "prohibits",
    "require",
    "requires",
    "review",
    "reviews",
    "says",
    "sets",
    "shall",
    "states",
    "must",
}

HEADING_RE = re.compile(
    r"^\s*((?i:Chapter|Section|Part|Article)\s+[0-9]+(?:\.[0-9]+)*"
    r"(?:\s*[:\-–]\s*[^\n]{1,120}|\s+(?:[A-Z][^\n.]{0,119}|[^\x00-\x7F][^\n.]{0,119})))\s*$|"
    r"^\s*((?:परिच्छेद|खण्ड)\s*[०-९0-9]+(?:[.\-][०-९0-9]+)*"
    r"(?:\s*[:\-–]\s*|\s+)[^\n]{1,120})\s*$",
    re.MULTILINE,
)
ENGLISH_HEADING_LABEL_RE = re.compile(
    r"^\s*(?i:Chapter|Section|Part|Article)\s+[0-9]+(?:\.[0-9]+)*"
    r"(?:\s*[:\-–]\s*|\s+)(?P<label>[^\n]{1,120})\s*$"
)
CLAUSE_RE = re.compile(
    r"\b((?:Clause|Section|Article|Rule)\s+[0-9]+(?:\.[0-9]+)*(?:\([a-zA-Z0-9]+\))?)(?=$|\s|[^\w(])|"
    r"\b((?:दफा|बुँदा)\s*[०-९0-9]+(?:[.\-][०-९0-9]+)*(?:\([^)]+\))?)",
    re.IGNORECASE,
)
PRINTED_PAGE_RE = re.compile(
    r"(?:^|\b)(?:page|pg\.?|p\.|printed\s+page)\s*[:#\-]?\s*([०-९0-9ivxlcdmIVXLCDM]+)\b|"
    r"(?:पृष्ठ|पेज)\s*[:#\-]?\s*([०-९0-9]+)",
    re.IGNORECASE,
)


def _normalize_string(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = " ".join(str(value).strip().split())
    if not normalized:
        return None
    return normalized[:160]


def _normalize_printed_page_number(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        return None
    normalized = " ".join(str(value).strip().split())
    if not normalized:
        return None
    return normalized[:160]


def _text_value(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value)
    if not text.strip():
        return None
    return text


def _page_number_is_present(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    if isinstance(value, int):
        return True
    if isinstance(value, str):
        return bool(value.strip())
    return False


def _first_group(match: re.Match[str] | None) -> str | None:
    if not match:
        return None
    for group in match.groups():
        normalized = _normalize_string(group)
        if normalized:
            return normalized
    return None


def _edge_text(text: str, line_count: int = 8) -> str:
    lines = [line.strip() for line in (text or "").splitlines() if line.strip()]
    if len(lines) <= line_count * 2:
        return "\n".join(lines)
    return "\n".join([*lines[:line_count], *lines[-line_count:]])


def _containing_line(text: str, match: re.Match[str]) -> str:
    line_start = text.rfind("\n", 0, match.start()) + 1
    line_end = text.find("\n", match.end())
    if line_end == -1:
        line_end = len(text)
    return text[line_start:line_end].strip()


def _contains_sentence_verb(line: str) -> bool:
    match = ENGLISH_HEADING_LABEL_RE.fullmatch(line)
    if not match:
        return False
    words = re.findall(r"[A-Za-z]+", match.group("label"))
    return any(word.lower() in COMMON_SENTENCE_VERBS for word in words)


def _is_heading_line(line: str) -> bool:
    return bool(HEADING_RE.fullmatch(line) and not _contains_sentence_verb(line))


def extract_document_heading(text: str | None) -> str | None:
    for line in (text or "").splitlines():
        if _is_heading_line(line):
            return _normalize_string(line)
    hierarchy = parse_legal_hierarchy(text)
    if hierarchy.document_title:
        return hierarchy.document_title
    return None


def extract_clause_number(text: str | None) -> str | None:
    value = (text or "")[:1600]
    for match in CLAUSE_RE.finditer(value):
        if _is_heading_line(_containing_line(value, match)):
            continue
        return _first_group(match)
    hierarchy = parse_legal_hierarchy(text)
    if hierarchy.clause:
        return hierarchy.clause
    return None


def extract_printed_page_number(text: str | None) -> str | None:
    return _first_group(PRINTED_PAGE_RE.search(_edge_text(text or "")))


def is_policy_document_type(document_type: str | None) -> bool:
    return (document_type or "").strip().lower() in POLICY_DOCUMENT_TYPES


def citation_is_complete_for_policy(metadata: Any) -> bool:
    if not isinstance(metadata, dict):
        return False
    return (
        not metadata.get("citation_incomplete_reasons")
        and _page_number_is_present(metadata.get("pdf_page_number"))
        and _normalize_string(metadata.get("document_heading")) is not None
        and _normalize_string(metadata.get("clause_number")) is not None
    )


def build_citation_metadata(*, page: Any, chunk_text: str | None, document_type: str | None) -> dict[str, Any]:
    if not isinstance(page, dict):
        page = {}

    hierarchy = parse_legal_hierarchy(
        "\n".join(
            value
            for value in (
                _text_value(page.get("section_label")),
                _text_value(page.get("text")),
                _text_value(chunk_text),
            )
            if value
        )
    )

    heading_text = "\n".join(
        value
        for value in (
            _text_value(page.get("section_label")),
            _text_value(chunk_text),
            _text_value(page.get("text")),
        )
        if value
    )
    chunk_text_value = _text_value(chunk_text)
    clause_source = chunk_text_value if chunk_text_value else _text_value(page.get("text"))
    clause_text = "\n".join(
        value
        for value in (
            _text_value(page.get("section_label")),
            clause_source,
        )
        if value
    )
    pdf_page_number = page.get("page_number")
    document_heading = _normalize_string(page.get("document_heading")) or extract_document_heading(heading_text)
    clause_number = _normalize_string(page.get("clause_number")) or extract_clause_number(clause_text)
    printed_page_number = _normalize_printed_page_number(page.get("printed_page_number")) or extract_printed_page_number(
        _text_value(page.get("text")) or chunk_text
    )
    document_heading = document_heading or hierarchy.document_title
    legal_path = legal_hierarchy_path(hierarchy=hierarchy)

    reasons: list[str] = []
    if is_policy_document_type(document_type):
        if not _page_number_is_present(pdf_page_number):
            reasons.append("missing_pdf_page_number")
        if not document_heading:
            reasons.append("missing_document_heading")
        if not clause_number:
            reasons.append("missing_clause_number")

    present = sum(
        (
            _page_number_is_present(pdf_page_number),
            bool(document_heading),
            bool(clause_number),
            bool(printed_page_number),
        )
    )
    confidence = min(1.0, 0.25 + (present * 0.2) + (0.15 if not reasons else 0.0))

    return {
        "pdf_page_number": pdf_page_number,
        "printed_page_number": printed_page_number,
        "document_heading": document_heading,
        "clause_number": clause_number,
        "citation_confidence": round(confidence, 2),
        "citation_incomplete_reasons": reasons,
        "legal_hierarchy": legal_path,
    }
