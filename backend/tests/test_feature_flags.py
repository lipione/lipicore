import pytest
from fastapi import APIRouter, Depends, FastAPI
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine, select
from sqlmodel.pool import StaticPool

from app.api import feature_flags
from app.api.deps import get_current_user
from app.core.security import create_access_token, get_password_hash
from app.db.session import get_session
from app.models.audit import AuditLog
from app.models.bank import Bank
from app.models.chat import ChatMessage, ChatSession  # noqa: F401 - registers document FK targets
from app.models.document import Document  # noqa: F401 - registers Bank relationship target for SQLModel tests
from app.models.user import User
from app.services.feature_flag_service import require_feature_enabled


sqlite_url = "sqlite://"
engine = create_engine(
    sqlite_url,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


def get_session_override():
    with Session(engine) as session:
        yield session


guard_router = APIRouter()


@guard_router.get("/guarded-market-time")
def guarded_market_time(
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    require_feature_enabled(db, current_user.bank_id, "market_time")
    return {"status": "enabled"}


test_app = FastAPI()
test_app.include_router(feature_flags.router, prefix="/api/feature-flags")
test_app.include_router(guard_router, prefix="/api/test")
test_app.dependency_overrides[get_session] = get_session_override
client = TestClient(test_app)


@pytest.fixture(autouse=True)
def setup_feature_flag_db():
    client.cookies.clear()
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        bank = Bank(name="Feature Bank", code="FEAT01")
        other_bank = Bank(name="Other Bank", code="OTHER01")
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
                bank_id=bank.id,
                is_active=True,
            ),
            User(
                email="staff@test.local",
                password_hash=get_password_hash("Password1"),
                name="Staff User",
                role="staff_user",
                bank_id=bank.id,
                is_active=True,
            ),
            User(
                email="other-admin@test.local",
                password_hash=get_password_hash("Password1"),
                name="Other Admin",
                role="bank_admin",
                bank_id=other_bank.id,
                is_active=True,
            ),
        ]
        session.add_all(users)
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


def _bank_id(code: str = "FEAT01") -> int:
    with Session(engine) as session:
        bank = session.exec(select(Bank).where(Bank.code == code)).first()
        assert bank is not None
        assert bank.id is not None
        return bank.id


def test_new_feature_flags_default_disabled_for_bank():
    bank_id = _bank_id()
    token = _token("super@test.local")

    response = client.get(
        f"/api/feature-flags?bank_id={bank_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    flags = {item["feature_key"]: item for item in response.json()["features"]}
    assert flags["employee_directory"]["enabled"] is False
    assert flags["market_time"]["enabled"] is False
    assert flags["ceo_messages"]["enabled"] is False
    assert "citation_nli_verification" in flags
    assert "citation_semantic_verification" in flags
    assert isinstance(flags["citation_nli_verification"]["enabled"], bool)
    assert isinstance(flags["citation_semantic_verification"]["enabled"], bool)


def test_super_admin_can_enable_and_disable_bank_feature():
    bank_id = _bank_id()
    token = _token("super@test.local")

    enable = client.patch(
        f"/api/feature-flags/{bank_id}/employee_directory",
        headers={"Authorization": f"Bearer {token}"},
        json={"enabled": True, "reason": "Pilot rollout"},
    )
    assert enable.status_code == 200
    assert enable.json()["feature_key"] == "employee_directory"
    assert enable.json()["enabled"] is True
    assert enable.json()["reason"] == "Pilot rollout"

    disable = client.patch(
        f"/api/feature-flags/{bank_id}/employee_directory",
        headers={"Authorization": f"Bearer {token}"},
        json={"enabled": False, "reason": "Pause pilot"},
    )
    assert disable.status_code == 200
    assert disable.json()["enabled"] is False


def test_bank_admin_can_read_own_bank_flags_but_not_toggle():
    bank_id = _bank_id()
    token = _token("admin@test.local")

    read = client.get(
        "/api/feature-flags",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert read.status_code == 200
    assert read.json()["bank_id"] == bank_id

    update = client.patch(
        f"/api/feature-flags/{bank_id}/market_time",
        headers={"Authorization": f"Bearer {token}"},
        json={"enabled": True, "reason": "Bank admin request"},
    )
    assert update.status_code == 403


def test_bank_admin_cannot_read_other_bank_flags():
    other_bank_id = _bank_id("OTHER01")
    token = _token("admin@test.local")

    response = client.get(
        f"/api/feature-flags?bank_id={other_bank_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


def test_staff_cannot_read_feature_flag_management_api():
    token = _token("staff@test.local")

    response = client.get(
        "/api/feature-flags",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


def test_staff_can_read_effective_flags_for_own_bank():
    token = _token("staff@test.local")

    response = client.get(
        "/api/feature-flags/effective",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    flags = {item["feature_key"]: item for item in response.json()["features"]}
    assert flags["employee_directory"]["enabled"] is False
    assert flags["market_time"]["enabled"] is False


def test_disabled_feature_guard_returns_feature_disabled_detail():
    token = _token("staff@test.local")

    response = client.get(
        "/api/test/guarded-market-time",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "feature_disabled"
    assert response.json()["detail"]["feature"] == "market_time"


def test_enabled_feature_guard_allows_normal_api_flow():
    bank_id = _bank_id()
    super_token = _token("super@test.local")
    staff_token = _token("staff@test.local")
    client.patch(
        f"/api/feature-flags/{bank_id}/market_time",
        headers={"Authorization": f"Bearer {super_token}"},
        json={"enabled": True, "reason": "Enable market utility pilot"},
    )

    response = client.get(
        "/api/test/guarded-market-time",
        headers={"Authorization": f"Bearer {staff_token}"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "enabled"


def test_feature_flag_updates_are_audited():
    bank_id = _bank_id()
    token = _token("super@test.local")

    response = client.patch(
        f"/api/feature-flags/{bank_id}/ceo_messages",
        headers={"Authorization": f"Bearer {token}"},
        json={"enabled": True, "reason": "CEO launch"},
    )
    assert response.status_code == 200

    with Session(engine) as session:
        logs = session.exec(select(AuditLog).where(AuditLog.action == "feature_flag_update")).all()

    assert len(logs) == 1
    assert logs[0].bank_id == bank_id
    assert logs[0].resource_type == "feature_flag"
    assert logs[0].resource_id == "ceo_messages"
