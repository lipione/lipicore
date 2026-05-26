from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool

from app.core.security import verify_password
from app.models.bank import Bank
from app.models.chat import ChatSession  # noqa: F401 - registers Document foreign keys
from app.models.document import Document  # noqa: F401 - registers Bank relationships
from app.models.user import User
from app.services.demo_accounts_service import create_demo_bank_accounts


def test_create_demo_bank_accounts_is_idempotent_and_sets_roles():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        rows = create_demo_bank_accounts(
            session,
            ["sanima"],
            password="SanimaDemo2026!",
            email_domain="demo.local",
            staff_count=2,
        )
        repeat_rows = create_demo_bank_accounts(
            session,
            ["sanima"],
            password="SanimaDemo2026!",
            email_domain="demo.local",
            staff_count=2,
        )

        banks = session.exec(select(Bank)).all()
        users = session.exec(select(User).order_by(User.email)).all()

    assert len(banks) == 1
    assert banks[0].code == "SANIMA"
    assert banks[0].name == "Sanima Demo Bank"
    assert len(users) == 5
    assert len(rows) == 5
    assert len(repeat_rows) == 5

    users_by_email = {user.email: user for user in users}
    assert {
        "bankadmin.sanima.demo@demo.local": "bank_admin",
        "branch.sanima.demo@demo.local": "staff_user",
        "compliance.sanima.demo@demo.local": "compliance_user",
        "staff1.sanima.demo@demo.local": "staff_user",
        "staff2.sanima.demo@demo.local": "staff_user",
    } == {email: user.role for email, user in users_by_email.items()}

    for row in rows:
        assert row["bank_code"] == "SANIMA"
        assert row["password"] == "SanimaDemo2026!"
        assert verify_password(row["password"], users_by_email[row["email"]].password_hash)

    assert all(row["status"] == "created" for row in rows)
    assert all(row["status"] == "updated" for row in repeat_rows)
