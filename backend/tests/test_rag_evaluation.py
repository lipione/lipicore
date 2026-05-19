import pytest
from sqlmodel import Session, SQLModel, select

from app.core.security import create_access_token, get_password_hash
from app.models.bank import Bank
from app.models.user import User
from app.services import rag_service
from app.services.rag_evaluation_service import evaluate_rag_cases
from test_main import client, engine


@pytest.fixture(autouse=True)
def setup_eval_db():
    client.cookies.clear()
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        bank = Bank(name="Eval Bank", code="EVAL01")
        session.add(bank)
        session.commit()

        session.add(
            User(
                email="super@test.local",
                password_hash=get_password_hash("password"),
                name="Super Admin",
                role="super_admin",
                bank_id=bank.id,
                is_active=True,
            )
        )
        session.add(
            User(
                email="staff@test.local",
                password_hash=get_password_hash("password"),
                name="Staff User",
                role="staff_user",
                bank_id=bank.id,
                is_active=True,
            )
        )
        session.add(
            User(
                email="auditor@test.local",
                password_hash=get_password_hash("password"),
                name="Audit User",
                role="auditor",
                bank_id=bank.id,
                is_active=True,
            )
        )
        session.commit()

    yield
    client.cookies.clear()
    SQLModel.metadata.drop_all(engine)


def auth_header(email: str) -> dict[str, str]:
    with Session(engine) as session:
        user = session.exec(select(User).where(User.email == email)).first()
        return {"Authorization": f"Bearer {create_access_token(user.id)}"}


def test_evaluate_rag_cases_scores_sources_citation_terms_and_answer_terms():
    def fake_generator(question, bank_id, user_role, db, active_document_ids=None, session_id=None):
        assert question == "What is the STR escalation timeline?"
        assert bank_id == 1
        assert user_role == "staff_user"
        return (
            "Suspicious Transaction Reports must be escalated within 24 hours.",
            [
                {
                    "document_id": 10,
                    "document_title": "AML SOP",
                    "snippet": "Section 7.1 STR escalation must happen within 24 hours.",
                    "section_label": "Section 7.1",
                    "page_number": 17,
                }
            ],
        )

    cases = [
        {
            "id": "aml-str-escalation",
            "question": "What is the STR escalation timeline?",
            "expected_source_document_ids": [10],
            "required_citation_terms": ["Section 7.1", "24 hours"],
            "required_answer_terms": ["Suspicious Transaction Reports", "24 hours"],
        }
    ]

    with Session(engine) as session:
        result = evaluate_rag_cases(
            cases=cases,
            db=session,
            bank_id=1,
            user_role="staff_user",
            answer_generator=fake_generator,
        )

    assert result["summary"]["total_cases"] == 1
    assert result["summary"]["passed_cases"] == 1
    assert result["summary"]["gate_passed"] is True
    assert result["cases"][0]["passed"] is True
    assert result["cases"][0]["source_recall"] == 1
    assert result["cases"][0]["citation_term_recall"] == 1
    assert result["cases"][0]["answer_term_recall"] == 1


def test_evaluate_rag_cases_fails_when_citation_points_to_wrong_document():
    def fake_generator(*_args, **_kwargs):
        return (
            "The escalation timeline is 24 hours.",
            [
                {
                    "document_id": 99,
                    "document_title": "Generic Risk Policy",
                    "snippet": "A generic policy mentions monitoring.",
                }
            ],
        )

    cases = [
        {
            "id": "wrong-citation",
            "question": "What is the STR escalation timeline?",
            "expected_source_document_ids": [10],
            "required_citation_terms": ["Section 7.1", "24 hours"],
            "required_answer_terms": ["24 hours"],
        }
    ]

    with Session(engine) as session:
        result = evaluate_rag_cases(
            cases=cases,
            db=session,
            bank_id=1,
            user_role="staff_user",
            answer_generator=fake_generator,
        )

    case = result["cases"][0]
    assert case["passed"] is False
    assert case["source_recall"] == 0
    assert "missing expected source documents: 10" in case["failures"]
    assert result["summary"]["gate_passed"] is False


def test_evaluate_rag_cases_can_match_expected_source_titles():
    def fake_generator(*_args, **_kwargs):
        return (
            "Customer care must verify identity before account support.",
            [
                {
                    "document_id": 25,
                    "document_title": "Customer Care SOP",
                    "snippet": "Section 2.1 Verify identity before account support.",
                }
            ],
        )

    cases = [
        {
            "id": "customer-care-identity",
            "question": "What should customer care verify before account support?",
            "expected_source_titles": ["Customer Care SOP"],
            "required_citation_terms": ["Section 2.1"],
            "required_answer_terms": ["verify identity"],
        }
    ]

    with Session(engine) as session:
        result = evaluate_rag_cases(
            cases=cases,
            db=session,
            bank_id=1,
            user_role="staff_user",
            answer_generator=fake_generator,
        )

    assert result["cases"][0]["source_recall"] == 1
    assert result["cases"][0]["passed"] is True


def test_evaluate_rag_cases_scores_expected_not_found_answers():
    def fake_generator(*_args, **_kwargs):
        return rag_service.NOT_FOUND_RESPONSE, []

    cases = [
        {
            "id": "unknown-policy",
            "question": "What is the policy for unsupported product X?",
            "expect_not_found": True,
        }
    ]

    with Session(engine) as session:
        result = evaluate_rag_cases(
            cases=cases,
            db=session,
            bank_id=1,
            user_role="staff_user",
            answer_generator=fake_generator,
        )

    assert result["cases"][0]["passed"] is True
    assert result["cases"][0]["not_found_passed"] is True


def test_bank_admin_can_run_rag_evaluation(monkeypatch):
    def fake_evaluate_rag_cases(**kwargs):
        assert kwargs["bank_id"] == 1
        assert kwargs["user_role"] == "staff_user"
        return {
            "summary": {
                "total_cases": 1,
                "passed_cases": 1,
                "failed_cases": 0,
                "pass_rate": 1,
                "gate_passed": True,
                "failed_case_ids": [],
                "source_recall_avg": 1,
                "citation_term_recall_avg": 1,
                "answer_term_recall_avg": 1,
            },
            "cases": [
                {
                    "id": "case-1",
                    "question": "Question?",
                    "passed": True,
                    "answer": "Answer.",
                    "sources": [],
                    "source_recall": 1,
                    "citation_term_recall": 1,
                    "answer_term_recall": 1,
                    "not_found_passed": None,
                    "failures": [],
                }
            ],
        }

    monkeypatch.setattr("app.api.evaluations.evaluate_rag_cases", fake_evaluate_rag_cases)
    response = client.post(
        "/api/evaluations/rag",
        headers=auth_header("super@test.local"),
        json={
            "cases": [{"id": "case-1", "question": "Question?"}],
            "pass_threshold": 0.9,
            "user_role": "staff_user",
        },
    )

    assert response.status_code == 200
    assert response.json()["summary"]["gate_passed"] is True


def test_auditor_can_run_rag_evaluation(monkeypatch):
    def fake_evaluate_rag_cases(**kwargs):
        assert kwargs["bank_id"] == 1
        return {
            "summary": {
                "total_cases": 1,
                "passed_cases": 1,
                "failed_cases": 0,
                "pass_rate": 1,
                "gate_passed": True,
                "failed_case_ids": [],
                "source_recall_avg": 1,
                "citation_term_recall_avg": 1,
                "answer_term_recall_avg": 1,
            },
            "cases": [
                {
                    "id": "case-1",
                    "question": "Question?",
                    "passed": True,
                    "answer": "Answer.",
                    "sources": [],
                    "source_recall": 1,
                    "citation_term_recall": 1,
                    "answer_term_recall": 1,
                    "not_found_passed": None,
                    "failures": [],
                }
            ],
        }

    monkeypatch.setattr("app.api.evaluations.evaluate_rag_cases", fake_evaluate_rag_cases)
    response = client.post(
        "/api/evaluations/rag",
        headers=auth_header("auditor@test.local"),
        json={"cases": [{"id": "case-1", "question": "Question?"}]},
    )

    assert response.status_code == 200


def test_staff_cannot_run_rag_evaluation():
    response = client.post(
        "/api/evaluations/rag",
        headers=auth_header("staff@test.local"),
        json={"cases": [{"id": "case-1", "question": "Question?"}]},
    )

    assert response.status_code == 403
