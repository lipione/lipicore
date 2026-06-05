import os
import re
from collections import Counter
from functools import lru_cache
from typing import Any, Callable


TOKEN_RE = re.compile(r"[\w०-९]+", re.UNICODE)
SENTENCE_RE = re.compile(r"(?<=[.!?।])\s+")
NEPALI_CHAR_RE = re.compile(r"[\u0900-\u097F]")
ASCII_WORD_RE = re.compile(r"[A-Za-z]")

NliPredictor = Callable[[str, str], dict[str, Any]]
SemanticScorer = Callable[[list[str], list[str]], list[float]]

ENTAILMENT_LABELS = {"entailment", "entailed", "supported", "support"}
SUPPORT_STOPWORDS = {
    "the",
    "this",
    "that",
    "these",
    "those",
    "and",
    "for",
    "from",
    "with",
    "within",
}


def _tokens(text: str | None) -> list[str]:
    if not text:
        return []
    return [
        token.lower()
        for token in TOKEN_RE.findall(text)
        if len(token) > 2 and token.lower() not in SUPPORT_STOPWORDS
    ]


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


def _env_float(name: str, default: str) -> float:
    return float(os.getenv(name, default))


def _env_int(name: str, default: str) -> int:
    return int(os.getenv(name, default))


def _is_long_sentence(sentence: str) -> bool:
    return len((sentence or "").strip()) >= 25


def _is_likely_english(text: str | None) -> bool:
    return bool(text and ASCII_WORD_RE.search(text))


def _contains_nepali(text: str | None) -> bool:
    return bool(text and NEPALI_CHAR_RE.search(text))


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


def _segment_source_evidence(source_passages: list[str]) -> list[str]:
    max_segments = _env_int("CITATION_SEMANTIC_MAX_SOURCE_SEGMENTS", "18")
    segments: list[str] = []
    for passage in source_passages:
        if not passage:
            continue
        for sentence in (chunk.strip() for chunk in SENTENCE_RE.split(passage)):
            if sentence:
                segments.append(sentence)
                if len(segments) >= max_segments:
                    return segments[:max_segments]
    if not segments and source_passages:
        return [source_passages[0][:500]]
    return segments[:max_segments]


def _default_semantic_scorer(sentences: list[str], source_segments: list[str]) -> list[float]:
    if not sentences or not source_segments:
        return [0.0 for _ in sentences]

    from .embedding_service import generate_embeddings

    all_texts = [*sentences, *source_segments]
    vectors = generate_embeddings(all_texts)
    if not vectors:
        return [0.0 for _ in sentences]

    sent_vectors = vectors[:len(sentences)]
    source_vectors = vectors[len(sentences):]

    if not source_vectors:
        return [0.0 for _ in sentences]

    source_norms = []
    for source_vec in source_vectors:
        norm = sum(value * value for value in source_vec) ** 0.5
        source_norms.append(norm)

    scores: list[float] = []
    for sentence_vec in sent_vectors:
        sent_norm = sum(value * value for value in sentence_vec) ** 0.5
        if sent_norm == 0:
            scores.append(0.0)
            continue
        sims = []
        for source_vec, source_norm in zip(source_vectors, source_norms, strict=False):
            if source_norm == 0:
                continue
            dot = sum(a * b for a, b in zip(sentence_vec, source_vec, strict=False))
            sims.append(float(dot) / (sent_norm * source_norm))
        scores.append(max(sims) if sims else 0.0)

    return scores


def verify_answer_against_sources(
    *,
    answer: str | None,
    sources: list[dict] | None,
    min_overlap: float = 0.38,
    nli_enabled: bool | None = None,
    nli_predictor: NliPredictor | None = None,
    nli_threshold: float | None = None,
    semantic_enabled: bool | None = None,
    semantic_scorer: SemanticScorer | None = None,
    semantic_threshold: float | None = None,
    semantic_only_cross_lang: bool = True,
) -> dict:
    source_passages = [
        (source.get("passage") or source.get("snippet") or "")
        for source in (sources or [])
    ]
    evidence = "\n".join(source_passages)
    if not answer or not evidence.strip():
        return {
            "status": "no_sources",
            "trust_label": "no_sources",
            "verification_stage": "lexical",
            "supported_sentence_count": 0,
            "unsupported_sentence_count": 0,
            "unsupported_sentences": [],
            "nli_checked_sentence_count": 0,
            "semantic_checked_sentence_count": 0,
            "semantic_supported_sentence_count": 0,
            "semantic_top_score": 0.0,
            "semantic_threshold": _env_float("CITATION_SEMANTIC_THRESHOLD", "0.7"),
        }

    sentences = [sentence.strip() for sentence in SENTENCE_RE.split(answer) if _is_long_sentence(sentence)]

    unsupported: list[str] = []
    supported_count = 0
    nli_checked = 0
    nli_error = None
    semantic_checked = 0
    semantic_supported = 0
    semantic_top_score = 0.0

    use_nli = _env_flag("CITATION_NLI_ENABLED") if nli_enabled is None else nli_enabled
    nli_threshold = nli_threshold if nli_threshold is not None else _env_float("CITATION_NLI_THRESHOLD", "0.7")

    use_semantic = _env_flag("CITATION_SEMANTIC_VERIFICATION_ENABLED", "true") if semantic_enabled is None else semantic_enabled
    semantic_threshold = semantic_threshold if semantic_threshold is not None else _env_float("CITATION_SEMANTIC_THRESHOLD", "0.70")
    cross_language_target = _is_likely_english(answer) and _contains_nepali(evidence)

    if cross_language_target:
        use_semantic = use_semantic and True
    elif (
        semantic_only_cross_lang
        and use_semantic
        and (_is_likely_english(answer) is False or _contains_nepali(evidence) is False)
    ):
        use_semantic = False
    if use_nli and nli_predictor is None:
        nli_predictor = _default_nli_predictor
    if use_semantic and semantic_scorer is None:
        semantic_scorer = _default_semantic_scorer

    source_segments = _segment_source_evidence(source_passages) if use_semantic else []
    max_semantic_sentences = _env_int("CITATION_SEMANTIC_MAX_SENTENCES", "8")
    semantic_candidates = sentences[:max_semantic_sentences]
    semantic_scores = semantic_scorer(semantic_candidates, source_segments) if use_semantic and semantic_candidates else []
    semantic_lookup: dict[int, float] = {
        index: score for index, score in enumerate(semantic_scores[: len(semantic_candidates)])
    }
    if semantic_scores:
        semantic_top_score = max(semantic_scores)

    for idx, sentence in enumerate(sentences):
        score = _token_overlap_score(sentence, evidence)
        if cross_language_target and use_semantic and semantic_candidates:
            semantic_score = semantic_lookup.get(idx, 0.0)
            semantic_checked += 1
            if semantic_score >= semantic_threshold:
                supported_count += 1
                semantic_supported += 1
                semantic_top_score = max(semantic_top_score, semantic_score)
                continue
            if use_nli and nli_predictor:
                try:
                    nli_checked += 1
                    nli_result = nli_predictor(evidence, sentence)
                except Exception as exc:
                    nli_error = f"{type(exc).__name__}: {exc}"
                    continue
                if _nli_supports_claim(nli_result, nli_threshold):
                    supported_count += 1
                else:
                    unsupported.append(sentence[:240])
            else:
                unsupported.append(sentence[:240])
            continue
        if score < min_overlap:
            nli_or_semantic_tried = False
            if idx < len(semantic_candidates):
                semantic_score = semantic_lookup.get(idx, 0.0)
                semantic_checked += 1
                nli_or_semantic_tried = True
                if semantic_score >= semantic_threshold:
                    supported_count += 1
                    semantic_supported += 1
                    semantic_top_score = max(semantic_top_score, semantic_score)
                    continue
            if not use_nli and not use_semantic:
                unsupported.append(sentence[:240])
                continue
            if use_nli and nli_predictor:
                nli_or_semantic_tried = True
                try:
                    nli_checked += 1
                    nli_result = nli_predictor(evidence, sentence)
                except Exception as exc:
                    nli_error = f"{type(exc).__name__}: {exc}"
                    supported_count += 1
                    continue
                if _nli_supports_claim(nli_result, nli_threshold):
                    supported_count += 1
                else:
                    unsupported.append(sentence[:240])
                continue
            if not nli_or_semantic_tried:
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
            if _nli_supports_claim(nli_result, nli_threshold):
                supported_count += 1
            else:
                unsupported.append(sentence[:240])
            continue
        supported_count += 1

    if not sentences:
        status = "not_enough_claims"
    elif unsupported and supported_count == 0:
        status = "unsupported"
    elif unsupported:
        status = "partially_supported"
    else:
        status = "supported"

    unsupported_sentence_count = len(unsupported)
    if not sources:
        trust_label = "no_sources"
    elif unsupported_sentence_count == 0:
        trust_label = "source_supported"
    elif supported_count > 0:
        trust_label = "partially_source_supported"
    else:
        trust_label = "not_source_supported"

    if use_nli and use_semantic and nli_checked:
        stage = "hybrid"
    elif use_nli and nli_checked:
        stage = "lexical+nli"
    elif use_semantic:
        stage = "lexical+semantic"
    else:
        stage = "lexical"

    return {
        "status": status,
        "trust_label": trust_label,
        "verification_stage": stage,
        "supported_sentence_count": supported_count,
        "unsupported_sentence_count": unsupported_sentence_count,
        "unsupported_sentences": unsupported[:5],
        "nli_checked_sentence_count": nli_checked,
        "semantic_checked_sentence_count": semantic_checked,
        "semantic_supported_sentence_count": semantic_supported,
        "semantic_top_score": round(float(semantic_top_score), 4),
        "semantic_threshold": round(float(semantic_threshold), 4),
        "nli_error": nli_error,
    }


def attach_source_verification(sources: list[dict] | None, verification: dict) -> list[dict]:
    if not sources:
        return []
    status = verification.get("status", "unknown")
    return [{**source, "citation_verification": status} for source in sources]
