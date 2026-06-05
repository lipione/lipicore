import re
from datetime import datetime


POLICY_CONFLICT_RESPONSE = (
    "I found conflicting approved sources for this policy question. "
    "Please confirm with Compliance before relying on one answer."
)
POLICY_CLARIFICATION_PREFIX = "I need one policy scope detail before answering"

_WORD_RE = re.compile(r"[\w०-९]+", re.UNICODE)
_AMOUNT_RE = re.compile(
    r"(?:\b(?:npr|rs\.?|rupees?|amount|threshold|limit)\b|[0-9][0-9,]*(?:\.[0-9]+)?)",
    re.IGNORECASE,
)
_THRESHOLD_SOURCE_RE = re.compile(
    r"\b(?:above|below|over|under|exceed(?:s|ing)?|up to|less than|greater than|threshold|limit|amount|npr|rs\.?)\b",
    re.IGNORECASE,
)
_DENY_RE = re.compile(
    r"\b(?:not allowed|not permitted|shall not|must not|cannot|can't|prohibited|may not|is not eligible)\b",
    re.IGNORECASE,
)
_ALLOW_RE = re.compile(
    r"\b(?:may be approved|can be approved|is allowed|are allowed|is permitted|are permitted|may waive|can waive|may be waived|can be waived)\b",
    re.IGNORECASE,
)
_EXCEPTION_RE = re.compile(
    r"\b(?:exception|except|unless|waiv(?:e|er|ed|ing)|exempt(?:ion|ed)?|override|notwithstanding|subject to|may be approved|can be approved)\b",
    re.IGNORECASE,
)
_QUESTION_EXCEPTION_RE = re.compile(
    r"\b(?:can|may|allow|allowed|approve|approval|exception|waiv(?:e|er|ed|ing)|exempt|unless|permitted)\b",
    re.IGNORECASE,
)

_STOPWORDS = {
    "what",
    "when",
    "where",
    "which",
    "who",
    "whom",
    "whose",
    "why",
    "how",
    "can",
    "may",
    "should",
    "must",
    "the",
    "this",
    "that",
    "these",
    "those",
    "for",
    "from",
    "with",
    "and",
    "are",
    "is",
    "was",
    "were",
    "staff",
}

_POLICY_DOCUMENT_TYPES = {
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

POLICY_BUNDLE_GROUPS = {
    "account_opening_kyc": {
        "triggers": (
            "account opening",
            "open account",
            "open an account",
            "new account",
            "kyc",
            "identity document",
            "identity documents",
            "customer identification",
            "customer due diligence",
            "cdd",
            "beneficial owner",
        ),
        "queries": (
            "kyc customer identification account opening identity documents",
            "customer due diligence beneficial owner aml sanctions pep",
        ),
    },
    "fee_waiver": {
        "triggers": (
            "fee waiver",
            "waive fee",
            "waived fee",
            "fees may be waived",
            "charge waiver",
            "tariff waiver",
            "account opening fees",
        ),
        "queries": (
            "fee waiver charges tariff approval exception",
            "customer fee exception branch manager approval",
        ),
    },
    "aml_reporting": {
        "triggers": (
            "suspicious transaction",
            "str",
            "aml",
            "transaction monitoring",
            "sanctions",
            "pep",
        ),
        "queries": (
            "aml suspicious transaction report escalation compliance",
            "transaction monitoring sanctions pep customer due diligence",
        ),
    },
    "credit_policy": {
        "triggers": (
            "loan",
            "credit",
            "borrower",
            "collateral",
            "dsr",
            "debt service",
            "approval memo",
        ),
        "queries": (
            "credit policy borrower eligibility collateral dsr exception",
            "loan approval checklist risk summary missing documents",
        ),
    },
}


def _normalized_text(value: str | None) -> str:
    return " ".join((value or "").lower().split())


def _contains_term(text: str, term: str) -> bool:
    normalized_term = _normalized_text(term)
    if not normalized_term:
        return False
    if " " in normalized_term:
        return normalized_term in text
    return re.search(rf"\b{re.escape(normalized_term)}\b", text) is not None


def _tokens(value: str | None) -> set[str]:
    return {
        token.lower()
        for token in _WORD_RE.findall(value or "")
        if len(token) > 2 and token.lower() not in _STOPWORDS
    }


def is_exception_clause(text: str | None) -> bool:
    return bool(_EXCEPTION_RE.search(text or ""))


def policy_bundle_terms_for_text(text: str | None) -> list[str]:
    normalized = _normalized_text(text)
    terms: list[str] = []
    for bundle_name, config in POLICY_BUNDLE_GROUPS.items():
        triggers = config["triggers"]
        if any(_contains_term(normalized, trigger) for trigger in triggers):
            terms.append(bundle_name)
    if is_exception_clause(text) and any(term in normalized for term in ("fee", "fees", "charge", "tariff")):
        if "fee_waiver" not in terms:
            terms.append("fee_waiver")
    return terms


def policy_bundle_queries(query: str | None) -> list[str]:
    normalized = _normalized_text(query)
    expanded: list[str] = []
    for config in POLICY_BUNDLE_GROUPS.values():
        triggers = config["triggers"]
        if any(_contains_term(normalized, trigger) for trigger in triggers):
            expanded.extend(config["queries"])
    deduped: list[str] = []
    seen = {_normalized_text(query)}
    for expanded_query in expanded:
        key = _normalized_text(expanded_query)
        if key and key not in seen:
            deduped.append(expanded_query)
            seen.add(key)
    return deduped[:4]


def policy_payload_metadata(payload: dict | None) -> dict:
    payload = dict(payload or {})
    text = payload.get("text") or ""
    bundle_terms = payload.get("policy_bundle_terms")
    if isinstance(bundle_terms, str):
        bundle_terms = [term.strip() for term in bundle_terms.split(",") if term.strip()]
    if not isinstance(bundle_terms, list) or not bundle_terms:
        bundle_terms = policy_bundle_terms_for_text(text)
    payload["policy_exception"] = bool(payload.get("policy_exception") or is_exception_clause(text))
    payload["policy_bundle_terms"] = bundle_terms
    payload["policy_scope_hints"] = policy_scope_hints(text)
    return payload


def policy_scope_hints(text: str | None) -> list[str]:
    hints: list[str] = []
    if _THRESHOLD_SOURCE_RE.search(text or ""):
        hints.append("transaction amount or threshold")
    return hints


def policy_rerank_boost(query: str | None, payload: dict | None) -> float:
    payload = policy_payload_metadata(payload)
    text = payload.get("text") or ""
    query_text = query or ""
    boost = 0.0
    if payload.get("policy_exception"):
        boost += 0.10
        if _QUESTION_EXCEPTION_RE.search(query_text):
            boost += 0.14
        if "waiv" in query_text.lower() and "waiv" in text.lower():
            boost += 0.08
    query_terms = set(policy_bundle_terms_for_text(query_text))
    source_terms = set(payload.get("policy_bundle_terms") or [])
    if query_terms and source_terms.intersection(query_terms):
        boost += 0.06
    return min(boost, 0.32)


def document_is_current(doc, as_of: datetime | None = None) -> bool:
    if getattr(doc, "document_scope", None) == "session_upload":
        return True
    now = as_of or datetime.utcnow()
    effective_from = getattr(doc, "effective_from", None)
    effective_to = getattr(doc, "effective_to", None)
    if effective_from and effective_from > now:
        return False
    if effective_to and effective_to < now:
        return False
    return True


def _source_text(source: dict) -> str:
    return source.get("passage") or source.get("snippet") or ""


def _policy_sources(sources: list[dict]) -> list[dict]:
    return [
        source
        for source in sources
        if (source.get("document_type") or "").strip().lower() in _POLICY_DOCUMENT_TYPES
    ]


def _source_stance(source: dict) -> str | None:
    text = _source_text(source)
    if _DENY_RE.search(text):
        return "deny"
    if _ALLOW_RE.search(text):
        return "allow"
    return None


def detect_policy_conflict(question: str | None, sources: list[dict]) -> bool:
    query_tokens = _tokens(question)
    if not query_tokens or len(sources) < 2:
        return False
    relevant = []
    for source in sources:
        source_tokens = _tokens(_source_text(source))
        if len(query_tokens.intersection(source_tokens)) < 2:
            continue
        stance = _source_stance(source)
        if stance:
            relevant.append(stance)
    return "allow" in relevant and "deny" in relevant


def missing_policy_scope_labels(question: str | None, sources: list[dict]) -> list[str]:
    if not sources:
        return []
    question_text = question or ""
    labels: list[str] = []
    combined_source_text = "\n".join(_source_text(source) for source in sources)
    if _THRESHOLD_SOURCE_RE.search(combined_source_text) and not _AMOUNT_RE.search(question_text):
        labels.append("transaction amount or threshold")
    return labels


def policy_guardrail_response(question: str | None, sources: list[dict]) -> str | None:
    policy_sources = _policy_sources(sources)
    if not policy_sources:
        return None
    if detect_policy_conflict(question, policy_sources):
        return POLICY_CONFLICT_RESPONSE
    missing_labels = missing_policy_scope_labels(question, policy_sources)
    if missing_labels:
        return f"{POLICY_CLARIFICATION_PREFIX}: please specify {', '.join(missing_labels)}."
    return None
