from typing import Any

from pydantic import BaseModel, Field


class RagEvaluationCase(BaseModel):
    id: str
    question: str
    expected_source_document_ids: list[int] = Field(default_factory=list)
    expected_source_titles: list[str] = Field(default_factory=list)
    required_citation_terms: list[str] = Field(default_factory=list)
    required_answer_terms: list[str] = Field(default_factory=list)
    expect_not_found: bool = False
    not_found_required: bool = False
    source_required: bool = False
    citation_required: bool = False
    no_general_policy_advice: bool = False
    active_document_ids: list[int] | None = None
    session_id: int | None = None


class RagEvaluationRequest(BaseModel):
    cases: list[RagEvaluationCase] = Field(min_length=1, max_length=50)
    pass_threshold: float = Field(default=1.0, ge=0, le=1)
    user_role: str = "staff_user"
    bank_id: int | None = None


class RagEvaluationCaseResult(BaseModel):
    id: str
    question: str
    passed: bool
    answer: str
    sources: list[dict[str, Any]]
    source_recall: float
    citation_term_recall: float
    answer_term_recall: float
    not_found_passed: bool | None
    failures: list[str]


class RagEvaluationSummary(BaseModel):
    total_cases: int
    passed_cases: int
    failed_cases: int
    pass_rate: float
    gate_passed: bool
    failed_case_ids: list[str]
    source_recall_avg: float
    citation_term_recall_avg: float
    answer_term_recall_avg: float


class RagEvaluationResponse(BaseModel):
    summary: RagEvaluationSummary
    cases: list[RagEvaluationCaseResult]
