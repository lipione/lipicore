import re
from collections import Counter
from functools import lru_cache
import os
from typing import Any, Callable


TOKEN_RE = re.compile(r"[\w०-९]+", re.UNICODE)
SENTENCE_RE = re.compile(r"(?<=[.!?।])\s+")
NliPredictor = Callable[[str, str], dict[str, Any]]
ENTAILMENT_LABELS = {"entailment", "entailed", "supported", "support"}


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


def _env_flag(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).lower() in {"1", "true", "yes", "on"}


@lru_cache(maxsize=2)
def _load_nli_pipeline(model_name: str):
    from transformers import pipeline

    return pipeline("text-classification", model=model_name)


def _default_nli_predictor(premise: str, hypothesis: str) -> dict[str, Any]:
    model_name = os.getenv("CITATION_NLI_MODEL", "cross-encoder/nli-deberta-v3-base")
    classifier = _load_nli_pipeline(model_name)
    result = classifier({"text": premise[:6000], "text_pair": hypothesis[:1000]})
    if isinstance(result, list):
        if result and isinstance(result[0], list):
            result = result[0]
        if result:
            result = max(result, key=lambda item: float(item.get("score") or 0))
    return dict(result or {})


def _nli_supports_claim(result: dict[str, Any], threshold: float) -> bool:
    label = str(result.get("label") or "").lower()
    score = float(result.get("score") or 0)
    return any(entailment in label for entailment in ENTAILMENT_LABELS) and score >= threshold


def verify_answer_against_sources(
    *,
    answer: str | None,
    sources: list[dict] | None,
    min_overlap: float = 0.38,
    nli_enabled: bool | None = None,
    nli_predictor: NliPredictor | None = None,
    nli_threshold: float | None = None,
) -> dict:
    source_passages = [
        (source.get("passage") or source.get("snippet") or "")
        for source in (sources or [])
    ]
    evidence = "\n".join(source_passages)
    if not answer or not evidence.strip():
        return {
            "status": "no_sources",
            "verification_stage": "lexical",
            "supported_sentence_count": 0,
            "unsupported_sentence_count": 0,
            "unsupported_sentences": [],
            "nli_checked_sentence_count": 0,
        }

    sentences = [
        sentence.strip()
        for sentence in SENTENCE_RE.split(answer)
        if len(sentence.strip()) >= 25
    ]
    unsupported = []
    supported_count = 0
    nli_checked = 0
    nli_error = None
    use_nli = _env_flag("CITATION_NLI_ENABLED") if nli_enabled is None else nli_enabled
    threshold = nli_threshold if nli_threshold is not None else float(os.getenv("CITATION_NLI_THRESHOLD", "0.7"))
    if use_nli and nli_predictor is None:
        nli_predictor = _default_nli_predictor

    for sentence in sentences:
        score = _token_overlap_score(sentence, evidence)
        if score < min_overlap:
            unsupported.append(sentence[:240])
            continue
        if use_nli and nli_predictor:
            try:
                nli_checked += 1
                nli_result = nli_predictor(evidence, sentence)
            except Exception as exc:
                nli_error = f"{type(exc).__name__}: {exc}"
                supported_count += 1
                continue
            if _nli_supports_claim(nli_result, threshold):
                supported_count += 1
            else:
                unsupported.append(sentence[:240])
            continue
        supported_count += 1

    if not sentences:
        status = "not_enough_claims"
    elif unsupported:
        status = "partially_supported"
    else:
        status = "supported"

    return {
        "status": status,
        "verification_stage": "lexical+nli" if use_nli and nli_checked else "lexical",
        "supported_sentence_count": supported_count,
        "unsupported_sentence_count": len(unsupported),
        "unsupported_sentences": unsupported[:5],
        "nli_checked_sentence_count": nli_checked,
        "nli_error": nli_error,
    }


def attach_source_verification(sources: list[dict] | None, verification: dict) -> list[dict]:
    if not sources:
        return []
    status = verification.get("status", "unknown")
    return [{**source, "citation_verification": status} for source in sources]
