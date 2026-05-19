import re
from collections import Counter


TOKEN_RE = re.compile(r"[\w०-९]+", re.UNICODE)
SENTENCE_RE = re.compile(r"(?<=[.!?।])\s+")


def _tokens(text: str | None) -> list[str]:
    if not text:
        return []
    return [token.lower() for token in TOKEN_RE.findall(text) if len(token) > 2]


def _token_overlap_score(sentence: str, evidence: str) -> float:
    sentence_tokens = _tokens(sentence)
    evidence_tokens = _tokens(evidence)
    if not sentence_tokens or not evidence_tokens:
        return 0.0

    evidence_counts = Counter(evidence_tokens)
    matched = sum(1 for token in set(sentence_tokens) if token in evidence_counts)
    return matched / max(len(set(sentence_tokens)), 1)


def verify_answer_against_sources(
    *,
    answer: str | None,
    sources: list[dict] | None,
    min_overlap: float = 0.38,
) -> dict:
    source_passages = [
        (source.get("passage") or source.get("snippet") or "")
        for source in (sources or [])
    ]
    evidence = "\n".join(source_passages)
    if not answer or not evidence.strip():
        return {
            "status": "no_sources",
            "supported_sentence_count": 0,
            "unsupported_sentence_count": 0,
            "unsupported_sentences": [],
        }

    sentences = [
        sentence.strip()
        for sentence in SENTENCE_RE.split(answer)
        if len(sentence.strip()) >= 25
    ]
    unsupported = []
    supported_count = 0
    for sentence in sentences:
        score = _token_overlap_score(sentence, evidence)
        if score >= min_overlap:
            supported_count += 1
        else:
            unsupported.append(sentence[:240])

    if not sentences:
        status = "not_enough_claims"
    elif unsupported:
        status = "partially_supported"
    else:
        status = "supported"

    return {
        "status": status,
        "supported_sentence_count": supported_count,
        "unsupported_sentence_count": len(unsupported),
        "unsupported_sentences": unsupported[:5],
    }


def attach_source_verification(sources: list[dict] | None, verification: dict) -> list[dict]:
    if not sources:
        return []
    status = verification.get("status", "unknown")
    return [{**source, "citation_verification": status} for source in sources]
