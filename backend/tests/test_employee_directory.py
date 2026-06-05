import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine, select
from sqlmodel.pool import StaticPool

from app.api import employee_directory
from app.core.security import create_access_token, get_password_hash
from app.db.session import get_session
from app.models.bank import Bank
from app.models.chat import ChatMessage, ChatSession  # noqa: F401 - registers SQLModel relationships
from app.models.document import Document  # noqa: F401 - registers SQLModel relationships
from app.models.employee_profile import EmployeeProfile
from app.models.feature_flag import BankFeatureFlag  # noqa: F401 - registers feature flag table
from app.models.user import User
from app.services.feature_flag_service import set_feature_flag


sqlite_url = "sqlite://"
engine = create_engine(
    sqlite_url,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


def get_session_override():
    with Session(engine) as session:
        yield session


test_app = FastAPI()
test_app.include_router(employee_directory.router, prefix="/api/employee-directory")
test_app.dependency_overrides[get_session] = get_session_override
client = TestClient(test_app)


@pytest.fixture(autouse=True)
def setup_employee_directory_db():
    client.cookies.clear()
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        bank = Bank(name="Directory Bank", code="DIR01")
        other_bank = Bank(name="Other Directory Bank", code="ODIR01")
        session.add(bank)
        session.add(other_bank)
        session.commit()
        session.refresh(bank)
        session.refresh(other_bank)

        users = [
            User(
                email="super@test.local",
                password_hash=get_password_hash("Password1"),
                name="Super Admin",
                role="super_admin",
                bank_id=bank.id,
                is_active=True,
            ),
            User(
                email="admin@test.local",
                password_hash=get_password_hash("Password1"),
                name="Bank Admin",
                role="bank_admin",
                department="Administration",
                bank_id=bank.id,
                is_active=True,
            ),
            User(
                email="ram.ops@test.local",
                password_hash=get_password_hash("Password1"),
                name="Ram Ops",
                role="staff_user",
                department="Operations",
                bank_id=bank.id,
                is_active=True,
            ),
            User(
                email="sita.compliance@test.local",
                password_hash=get_password_hash("Password1"),
                name="Sita Compliance",
                role="compliance_officer",
                department="Compliance",
                bank_id=bank.id,
                is_active=True,
            ),
            User(
                email="inactive.teller@test.local",
                password_hash=get_password_hash("Password1"),
                name="Inactive Teller",
                role="staff_user",
                department="Branch",
                bank_id=bank.id,
                is_active=False,
            ),
            User(
                email="other.bank@test.local",
                password_hash=get_password_hash("Password1"),
                name="Other Bank User",
                role="staff_user",
                department="Operations",
                bank_id=other_bank.id,
                is_active=True,
            ),
        ]
        session.add_all(users)
        session.commit()
        for user in users:
            session.refresh(user)

        profiles = [
            EmployeeProfile(
                bank_id=bank.id,
                user_id=users[2].id,
                branch="Kathmandu Main",
                job_title="Branch Operations Officer",
                phone_extension="221",
                expertise_tags_json='["KYC", "cash operations"]',
                escalation_areas_json='["branch operations"]',
                availability_status="available",
            ),
            EmployeeProfile(
                bank_id=bank.id,
                user_id=users[3].id,
                branch="Lalitpur",
                job_title="AML Review Lead",
                phone_extension="305",
                expertise_tags_json='["AML", "sanctions"]',
                escalation_areas_json='["compliance escalation"]',
                availability_status="busy",
            ),
            EmployeeProfile(
                bank_id=bank.id,
                user_id=users[4].id,
                branch="Bhaktapur",
                job_title="Teller",
                phone_extension="118",
                expertise_tags_json='["cash counter"]',
                escalation_areas_json='["cash exception"]',
                availability_status="away",
            ),
            EmployeeProfile(
                bank_id=other_bank.id,
                user_id=users[5].id,
                branch="Pokhara",
                job_title="Other Bank Officer",
                phone_extension="772",
                expertise_tags_json='["remittance"]',
                escalation_areas_json='["other bank only"]',
                availability_status="available",
            ),
        ]
        session.add_all(profiles)
        session.commit()

    yield
    client.cookies.clear()
    SQLModel.metadata.drop_all(engine)


def _token(email: str) -> str:
    with Session(engine) as session:
        user = session.exec(select(User).where(User.email == email)).first()
        assert user is not None
        assert user.id is not None
        return create_access_token(user.id)


def _bank_id(code: str = "DIR01") -> int:
    with Session(engine) as session:
        bank = session.exec(select(Bank).where(Bank.code == code)).first()
        assert bank is not None
        assert bank.id is not None
        return bank.id


def _enable_employee_directory():
    with Session(engine) as session:
        bank_id = _bank_id()
        admin = session.exec(select(User).where(User.email == "super@test.local")).first()
        assert admin is not None
        set_feature_flag(
            session,
            bank_id=bank_id,
            feature_key="employee_directory",
            enabled=True,
            configured_by_user_id=admin.id,
            reason="Directory pilot",
        )


def test_employee_profile_is_bank_scoped_and_linked_to_user():
    with Session(engine) as session:
        user = session.exec(select(User).where(User.email == "ram.ops@test.local")).first()
        assert user is not None
        profile = session.exec(select(EmployeeProfile).where(EmployeeProfile.user_id == user.id)).first()
        assert profile is not None
        assert profile.user_id == user.id
        assert profile.bank_id == user.bank_id


def test_employee_directory_rejects_disabled_feature():
    token = _token("ram.ops@test.local")

    response = client.get(
        "/api/employee-directory",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "feature_disabled"
    assert response.json()["detail"]["feature"] == "employee_directory"


def test_staff_can_search_active_users_in_own_bank_only():
    _enable_employee_directory()
    token = _token("ram.ops@test.local")

    response = client.get(
        "/api/employee-directory?q=operations",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    names = {item["name"] for item in response.json()}
    assert "Ram Ops" in names
    assert "Other Bank User" not in names
    assert "Inactive Teller" not in names
    assert all("password_hash" not in item for item in response.json())


def test_search_matches_profile_fields_and_json_lists():
    _enable_employee_directory()
    token = _token("ram.ops@test.local")

    kyc = client.get(
        "/api/employee-directory?q=kyc",
        headers={"Authorization": f"Bearer {token}"},
    )
    branch = client.get(
        "/api/employee-directory?branch=lalitpur",
        headers={"Authorization": f"Bearer {token}"},
    )
    expertise = client.get(
        "/api/employee-directory?expertise=sanctions",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert kyc.status_code == 200
    assert [item["name"] for item in kyc.json()] == ["Ram Ops"]
    assert branch.status_code == 200
    assert [item["name"] for item in branch.json()] == ["Sita Compliance"]
    assert expertise.status_code == 200
    assert [item["name"] for item in expertise.json()] == ["Sita Compliance"]


def test_bank_admin_can_include_disabled_users():
    _enable_employee_directory()
    token = _token("admin@test.local")

    response = client.get(
        "/api/employee-directory?include_disabled=true",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    inactive = [item for item in response.json() if item["name"] == "Inactive Teller"]
    assert len(inactive) == 1
    assert inactive[0]["is_active"] is False


def test_staff_cannot_include_disabled_users():
    _enable_employee_directory()
    token = _token("ram.ops@test.local")

    response = client.get(
        "/api/employee-directory?include_disabled=true",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


def test_non_super_admin_cannot_search_another_bank():
    _enable_employee_directory()
    other_bank_id = _bank_id("ODIR01")
    token = _token("ram.ops@test.local")

    response = client.get(
        f"/api/employee-directory?bank_id={other_bank_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


def test_super_admin_can_search_selected_bank():
    _enable_employee_directory()
    token = _token("super@test.local")
    bank_id = _bank_id()

    response = client.get(
        f"/api/employee-directory?bank_id={bank_id}&role=compliance_officer",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert [item["email"] for item in response.json()] == ["sita.compliance@test.local"]
    assert response.json()[0]["can_message"] is True
