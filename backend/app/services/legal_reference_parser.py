from __future__ import annotations

import re
from dataclasses import dataclass


deva_to_western_map = str.maketrans("०१२३४५६७८९", "0123456789")


@dataclass(frozen=True)
class LegalHierarchy:
    document_title: str | None = None
    part: str | None = None
    chapter: str | None = None
    section: str | None = None
    article: str | None = None
    clause: str | None = None


DOC_TITLE_RE = re.compile(
    r"^\s*(?:the\s+)?(?:nepal(?:e|es)?\s+)?(?:"
    r"(?:bank\s+)?(?:act|loan|credit|customer|governance|policy|procedure|manual|directive|compliance|circular)[\s\-:]"
    r"|(?:act|loan|credit|customer|governance|policy|procedure|manual|directive|compliance|circular)\s*$"
    r"|(?:कानुन|नियम|विधान|अधिनियम|निदेश|सर्कुलर|सञ्चालक|नीति)\s*$"
    r")\s*$",
    re.IGNORECASE,
)
DOC_TITLE_HINT_RE = re.compile(
    r"अधिनियम|नियम|विधान|निदेश|सर्कुलर|सञ्चालन|नीति|Policy|Rules?|Act|Directive|Circular|Procedure|Manual|Compliance",
    re.IGNORECASE,
)
PART_RE = re.compile(
    r"^\s*(?:(?:Part|भाग|खण्ड)\s+(?:[A-Za-z0-9]+(?:\.[A-Za-z0-9]+)*|[०-९]+(?:\.[०-९]+)*)|"
    r"परिच्छेद\s*[०-९0-9]+(?:[.\-][०-९0-9]+)*)\s*(?:[:\-–]\s*)?.{0,120}$",
    re.IGNORECASE | re.MULTILINE,
)
CHAPTER_RE = re.compile(
    r"^\s*(?:(?:Chapter|च्याप्टर|अध्याय)\s+[०-९0-9]+(?:\.[०-९0-9]+)*|खण्ड\s+[०-९0-9]+(?:[.\-][०-९0-9]+)*)\s*(?:[:\-–]\s*)?.{0,120}$",
    re.IGNORECASE | re.MULTILINE,
)
SECTION_RE = re.compile(
    r"^\s*(?:(?:Section|Article|Rule)\s+[०-९0-9]+(?:\.[०-९0-9]+)*(?:\([^)]+\))?)\s*(?:[:\-–]\s*)?.{0,120}$",
    re.IGNORECASE | re.MULTILINE,
)
CLAUSE_RE = re.compile(
    r"^\s*(?:(?:Clause|Rule|दफा|धारा|बुँदा)\s+[०-९0-9]+(?:\.[०-९0-9]+)*(?:\([^)]+\))?)\s*(?:[:\-–]\s*)?.{0,140}$",
    re.IGNORECASE | re.MULTILINE,
)


def _normalize_digits(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    if not normalized:
        return None
    return normalized.translate(deva_to_western_map)


def _has_nepali_text(value: str | None) -> bool:
    text = str(value or "")
    return any("\u0900" <= char <= "\u097f" for char in text)


def _normalize(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = " ".join(str(value).split())
    if not normalized:
        return None
    return normalized[:160]


def _normalize_heading_value(value: str | None, *, convert_nepali_digits: bool = False) -> str | None:
    normalized = _normalize(value)
    if normalized is None:
        return None
    if convert_nepali_digits:
        normalized = normalized.translate(deva_to_western_map)
    if _has_nepali_text(normalized):
        return normalized
    return normalized.lower()


def _is_legal_heading_line(line: str) -> bool:
    value = str(line or "").strip()
    if not value or len(value) > 220:
        return False
    lowered = value.lower()
    if any(token in lowered for token in ("shall", "must", "shall be", "shall not", "must be", "may", "may be")):
        return False
    if any(marker in value for marker in (",", ";", "(", ")")):
        return False
    return bool(
        DOC_TITLE_RE.search(value)
        or DOC_TITLE_HINT_RE.search(value)
        or PART_RE.search(value)
        or CHAPTER_RE.search(value)
        or SECTION_RE.search(value)
        or CLAUSE_RE.search(value)
    )


def _first_line_match(text: str, pattern: re.Pattern[str]) -> str | None:
    for line in (text or "").splitlines():
        value = line.strip()
        if not value:
            continue
        match = pattern.search(value)
        if not match:
            continue
        if not _is_legal_heading_line(value):
            continue
        return _normalize(value)
    return None


def _first_title_hint_line(text: str) -> str | None:
    for line in (text or "").splitlines():
        value = line.strip()
        if not value:
            continue
        if DOC_TITLE_RE.search(value):
            return _normalize(value)
        if DOC_TITLE_HINT_RE.search(value) and _is_legal_heading_line(value):
            return _normalize(value)
    return None


def parse_legal_hierarchy(text: str | None) -> LegalHierarchy:
    document_title = _first_title_hint_line(text or "")
    part = _first_line_match(text or "", PART_RE)
    chapter = _first_line_match(text or "", CHAPTER_RE)
    section = _first_line_match(text or "", SECTION_RE)
    clause = _first_line_match(text or "", CLAUSE_RE)

    part = _normalize_heading_value(part)
    chapter = _normalize_heading_value(chapter)
    section = _normalize_heading_value(section)
    clause = _normalize_heading_value(clause, convert_nepali_digits=True)

    return LegalHierarchy(
        document_title=document_title,
        part=part,
        chapter=chapter,
        section=section,
        clause=clause,
    )


def legal_hierarchy_path(*, hierarchy: LegalHierarchy) -> str | None:
    labels = [
        hierarchy.document_title,
        hierarchy.part,
        hierarchy.chapter,
        hierarchy.section,
    ]
    labels = [label for label in labels if label]
    if not labels:
        return None
    return " / ".join(labels)
