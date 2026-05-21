import json

import pytest
from sqlmodel import SQLModel, Session, select

from app.core.security import get_password_hash
from app.models.bank import Bank
from app.models.user import User
from app.schemas.compliance_review import ComplianceReviewCreate
from app.schemas.loan_support import LoanSupportCreate
from app.schemas.support_case import SupportCaseCreate
from app.services.compliance_review_service import create_compliance_review, update_compliance_review_summary
from app.services.loan_support_service import create_loan_support_case, save_credit_memo_draft
from app.services.support_case_service import create_support_case, save_support_case_draft
from test_main import engine


@pytest.fixture(autouse=True)
def setup_workflow_db():
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        bank = Bank(name="Workflow Bank", code="WF01")
        session.add(bank)
        session.commit()
        session.refresh(bank)
        staff = User(
            email="workflow-staff@test.local",
            password_hash=get_password_hash("password"),
            name="Workflow Staff",
            role="staff_user",
            bank_id=bank.id,
            is_active=True,
        )
        session.add(staff)
        session.commit()

    yield
    SQLModel.metadata.drop_all(engine)


def _bank_and_staff(session: Session):
    bank = session.exec(select(Bank).where(Bank.code == "WF01")).first()
    staff = session.exec(select(User).where(User.email == "workflow-staff@test.local")).first()
    return bank, staff


def test_support_case_draft_is_marked_for_staff_review():
    with Session(engine) as session:
        bank, staff = _bank_and_staff(session)
        staff_id = staff.id
        case = create_support_case(
            session,
            bank_id=bank.id,
            created_by=staff_id,
            data=SupportCaseCreate(
                customer_issue="Customer says ATM cash was debited but not dispensed.",
                category="failed_transaction",
                channel="branch",
                priority="high",
            ),
        )

        updated = save_support_case_draft(
            session,
            case_id=case.id,
            generated_by=staff_id,
            draft_response="We will verify the switch report and update the customer.",
            sources=[{"document_id": 22, "document_title": "Failed Transaction SOP"}],
        )

    assert updated.status == "draft_ready"
    assert updated.staff_review_required is True
    assert json.loads(updated.source_document_ids_json) == [22]
    metadata = json.loads(updated.answer_metadata_json)
    assert metadata["staff_review_required"] is True
    assert metadata["generated_by"] == staff_id


def test_compliance_review_keeps_human_approval_and_disclaimer():
    with Session(engine) as session:
        bank, staff = _bank_and_staff(session)
        review = create_compliance_review(
            session,
            bank_id=bank.id,
            created_by=staff.id,
            data=ComplianceReviewCreate(
                title="NRB circular impact review",
                circular_document_id=77,
                affected_departments=["Operations", "Compliance"],
            ),
        )

        updated = update_compliance_review_summary(
            session,
            review_id=review.id,
            generated_by=staff.id,
            impact_summary="Operations must update branch checklist by the effective date.",
            obligations=[{"owner": "Operations", "action": "Update checklist", "status": "open"}],
            sources=[{"document_id": 77, "document_title": "NRB Circular"}],
        )

    assert updated.status == "under_review"
    assert updated.approval_status == "requires_officer_review"
    assert "not a regulatory guarantee" in updated.disclaimer.lower()
    assert json.loads(updated.source_document_ids_json) == [77]
    assert json.loads(updated.obligations_json)[0]["owner"] == "Operations"


def test_loan_support_credit_memo_never_sets_automated_decision():
    with Session(engine) as session:
        bank, staff = _bank_and_staff(session)
        loan = create_loan_support_case(
            session,
            bank_id=bank.id,
            created_by=staff.id,
            data=LoanSupportCreate(
                applicant_name="Test Borrower",
                loan_type="home_loan",
                requested_amount=5_000_000,
                required_documents=["KYC", "Income proof", "Collateral valuation"],
                received_documents=["KYC"],
            ),
        )

        updated = save_credit_memo_draft(
            session,
            loan_id=loan.id,
            generated_by=staff.id,
            memo_draft="Borrower summary, facility request, collateral notes, and open questions.",
            risk_factors=["Income proof missing", "Collateral valuation missing"],
            sources=[{"document_id": 99, "document_title": "Home Loan Policy"}],
        )

    assert updated.status == "memo_draft_ready"
    assert updated.human_review_required is True
    assert updated.automated_decision is None
    assert json.loads(updated.missing_documents_json) == ["Income proof", "Collateral valuation"]
    assert json.loads(updated.risk_factors_json) == ["Income proof missing", "Collateral valuation missing"]
