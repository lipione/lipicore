from typing import Any, Callable

from sqlmodel import Session

from .rag_service import NOT_FOUND_RESPONSE, generate_rag_response


AnswerGenerator = Callable[..., tuple[str, list[dict[str, Any]]]]


def _value(case: Any, key: str, default: Any = None) -> Any:
    if isinstance(case, dict):
        return case.get(key, default)
    return getattr(case, key, default)


def _case_id(case: Any, index: int) -> str:
    return str(_value(case, "id", None) or f"case-{index + 1}")


def _normalize(text: Any) -> str:
    return " ".join(str(text or "").lower().split())


def _contains_term(text: str, term: str) -> bool:
    normalized_term = _normalize(term)
    return bool(normalized_term) and normalized_term in text


def _recall(found: set[Any], expected: list[Any]) -> float:
    expected_set = set(expected or [])
    if not expected_set:
        return 1.0
    return len(found & expected_set) / len(expected_set)


def _normalized_recall(found: set[str], expected: list[str]) -> float:
    expected_set = {_normalize(value) for value in expected or [] if _normalize(value)}
    if not expected_set:
        return 1.0
    return len(found & expected_set) / len(expected_set)


def _normalize_location(value: Any) -> str:
    return " ".join(str(value or "").lower().split())


def _score_location_recall(
    *,
    sources: list[dict[str, Any]],
    expected_section_labels: list[str],
    expected_page_numbers: list[int],
    expected_chunk_indexes: list[int],
) -> float:
    expected: list[tuple[str, str]] = []
    expected.extend(("section", _normalize_location(label)) for label in expected_section_labels)
    expected.extend(("page", str(number)) for number in expected_page_numbers)
    expected.extend(("chunk", str(index)) for index in expected_chunk_indexes)
    expected = [item for item in expected if item[1]]
    if not expected:
        return 1.0

    observed: set[tuple[str, str]] = set()
    for source in sources or []:
        section = source.get("section_label") or source.get("section_number")
        if section:
            observed.add(("section", _normalize_location(section)))
        if source.get("page_number") is not None:
            observed.add(("page", str(source.get("page_number"))))
        if source.get("chunk_index") is not None:
            observed.add(("chunk", str(source.get("chunk_index"))))

    matches = sum(1 for item in expected if item in observed)
    return matches / len(expected)


def _term_recall(text: str, terms: list[str]) -> float:
    terms = [term for term in (terms or []) if str(term).strip()]
    if not terms:
        return 1.0
    hits = sum(1 for term in terms if _contains_term(text, term))
    return hits / len(terms)


def _citation_text(sources: list[dict[str, Any]]) -> str:
    chunks: list[str] = []
    for source in sources or []:
        chunks.extend(
            str(source.get(key) or "")
            for key in ("document_title", "file_name", "section_label", "snippet")
        )
        if source.get("page_number") is not None:
            chunks.append(f"page {source.get('page_number')}")
    return _normalize(" ".join(chunks))


def _format_missing_terms(terms: list[str], text: str) -> str:
    missing = [term for term in terms or [] if not _contains_term(text, term)]
    return ", ".join(missing)


POLICY_ADVICE_TERMS = (
    "approve",
    "approval",
    "reject",
    "decline",
    "policy",
    "required",
    "must",
    "should",
    "compliance",
    "regulation",
    "directive",
    "escalate",
    "supervisor",
    "customer",
    "staff",
)


def _has_verified_citations(sources: list[dict[str, Any]]) -> bool:
    if not sources:
        return False
    statuses = [str(source.get("citation_verification") or "") for source in sources]
    return bool(statuses) and all(status == "supported" for status in statuses)


def _citation_verification_from_sources(sources: list[dict[str, Any]]) -> dict[str, str]:
    if not sources:
        return {"status": "no_sources", "trust_label": "no_sources"}
    statuses = [str(source.get("citation_verification") or "") for source in sources]
    if all(status == "supported" for status in statuses):
        return {"status": "supported", "trust_label": "source_supported"}
    if any(status == "unsupported" for status in statuses):
        return {"status": "unsupported", "trust_label": "not_source_supported"}
    if any(status == "partially_supported" for status in statuses):
        return {"status": "partially_supported", "trust_label": "partially_source_supported"}
    return {"status": "unknown", "trust_label": "source_unverified"}


def _case_passed(case: Any, result: dict[str, Any]) -> bool:
    if result.get("failures"):
        return False
    if bool(
        _value(case, "expected_not_found", False)
        or _value(case, "expect_not_found", False)
        or _value(case, "not_found_required", False)
    ):
        return bool(result.get("not_found_passed") or result.get("expected_not_found_passed"))
    if _value(case, "source_required", False) and result.get("source_recall", 0) <= 0:
        return False
    if _value(case, "citation_required", False) and result.get("citation_term_recall", 0) <= 0:
        return False
    trust_label = (result.get("citation_verification") or {}).get("trust_label")
    if _value(case, "citation_required", False) and trust_label not in (None, "source_supported"):
        return False
    if (
        _value(case, "no_general_policy_advice", False)
        and not result.get("no_general_policy_advice_passed", True)
    ):
        return False
    return True


def _looks_like_policy_advice(answer: str) -> bool:
    normalized = _normalize(answer)
    if not normalized or normalized == _normalize(NOT_FOUND_RESPONSE):
        return False
    return any(_contains_term(normalized, term) for term in POLICY_ADVICE_TERMS)


def evaluate_rag_cases(
    *,
    cases: list[Any],
    db: Session,
    bank_id: int,
    user_role: str = "staff_user",
    pass_threshold: float = 1.0,
    answer_generator: AnswerGenerator = generate_rag_response,
) -> dict[str, Any]:
    results: list[dict[str, Any]] = []

    for index, case in enumerate(cases):
        case_id = _case_id(case, index)
        question = str(_value(case, "question", "") or "")
        expected_doc_ids = [int(doc_id) for doc_id in (_value(case, "expected_source_document_ids", []) or [])]
        expected_source_titles = list(_value(case, "expected_source_titles", []) or [])
        expected_page_numbers = [
            int(value) for value in (_value(case, "expected_page_numbers", []) or [])
        ]
        expected_section_labels = list(_value(case, "expected_section_labels", []) or [])
        expected_chunk_indexes = [
            int(value) for value in (_value(case, "expected_chunk_indexes", []) or [])
        ]
        citation_terms = list(_value(case, "required_citation_terms", []) or [])
        answer_terms = list(_value(case, "required_answer_terms", []) or [])
        expect_not_found = bool(
            _value(case, "expected_not_found", False)
            or _value(case, "expect_not_found", False)
            or _value(case, "not_found_required", False)
        )
        source_required = bool(_value(case, "source_required", False))
        citation_required = bool(_value(case, "citation_required", False))
        no_general_policy_advice = bool(_value(case, "no_general_policy_advice", False))
        active_document_ids = _value(case, "active_document_ids", None)
        session_id = _value(case, "session_id", None)

        failures: list[str] = []
        try:
            answer, sources = answer_generator(
                question,
                bank_id,
                user_role,
                db,
                active_document_ids=active_document_ids,
                session_id=session_id,
            )
        except Exception as exc:
            answer = ""
            sources = []
            failures.append(f"generator error: {type(exc).__name__}: {exc}")

        source_ids = {source.get("document_id") for source in sources or [] if source.get("document_id") is not None}
        source_titles = {
            _normalize(source.get("document_title") or source.get("title") or source.get("file_name"))
            for source in sources or []
            if _normalize(source.get("document_title") or source.get("title") or source.get("file_name"))
        }

        if source_required and not sources:
            failures.append("expected source-backed answer")
        if citation_required and not _has_verified_citations(sources or []):
            failures.append("expected verified citations")

        id_recall = _recall(source_ids, expected_doc_ids)
        title_recall = _normalized_recall(source_titles, expected_source_titles)
        source_recall = min(id_recall, title_recall)
        if id_recall < 1:
            missing_ids = sorted(set(expected_doc_ids) - source_ids)
            failures.append(f"missing expected source documents: {', '.join(str(doc_id) for doc_id in missing_ids)}")
        if title_recall < 1:
            missing_titles = [
                title for title in expected_source_titles
                if _normalize(title) not in source_titles
            ]
            failures.append(f"missing expected source titles: {', '.join(missing_titles)}")

        location_recall = _score_location_recall(
            sources=sources or [],
            expected_section_labels=expected_section_labels,
            expected_page_numbers=expected_page_numbers,
            expected_chunk_indexes=expected_chunk_indexes,
        )
        if location_recall < 1:
            failures.append("missing expected citation locations")

        normalized_citations = _citation_text(sources or [])
        citation_term_recall = _term_recall(normalized_citations, citation_terms)
        if citation_term_recall < 1:
            failures.append(f"missing citation terms: {_format_missing_terms(citation_terms, normalized_citations)}")

        normalized_answer = _normalize(answer)
        answer_term_recall = _term_recall(normalized_answer, answer_terms)
        if answer_term_recall < 1:
            failures.append(f"missing answer terms: {_format_missing_terms(answer_terms, normalized_answer)}")
        if no_general_policy_advice and not sources and _looks_like_policy_advice(answer):
            failures.append("general policy advice without sources")

        not_found_passed = None
        if expect_not_found:
            not_found_passed = normalized_answer == _normalize(NOT_FOUND_RESPONSE) and len(sources or []) == 0
            if not not_found_passed:
                failures.append("expected not-found response with no sources")

        citation_verification = _citation_verification_from_sources(sources or [])
        no_general_policy_advice_passed = "general policy advice without sources" not in failures
        case_result = {
            "id": case_id,
            "question": question,
            "answer": answer,
            "sources": sources or [],
            "source_recall": round(source_recall, 4),
            "location_recall": round(location_recall, 4),
            "citation_term_recall": round(citation_term_recall, 4),
            "answer_term_recall": round(answer_term_recall, 4),
            "not_found_passed": not_found_passed,
            "expected_not_found_passed": not_found_passed,
            "no_general_policy_advice_passed": no_general_policy_advice_passed,
            "citation_verification": citation_verification,
            "failures": failures,
        }
        case_result["passed"] = _case_passed(case, case_result)
        results.append(
            case_result
        )

    total = len(results)
    passed = sum(1 for result in results if result["passed"])
    pass_rate = passed / total if total else 0

    def avg(key: str) -> float:
        if not results:
            return 0
        return round(sum(float(result[key]) for result in results) / len(results), 4)

    return {
        "summary": {
            "total_cases": total,
            "passed_cases": passed,
            "failed_cases": total - passed,
            "pass_rate": round(pass_rate, 4),
            "gate_passed": pass_rate >= pass_threshold,
            "failed_case_ids": [result["id"] for result in results if not result["passed"]],
            "source_recall_avg": avg("source_recall"),
            "location_recall_avg": avg("location_recall"),
            "citation_term_recall_avg": avg("citation_term_recall"),
            "answer_term_recall_avg": avg("answer_term_recall"),
        },
        "cases": results,
    }
