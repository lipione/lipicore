import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine, select
from sqlmodel.pool import StaticPool

from app.api import market_utilities
from app.core.security import create_access_token, get_password_hash
from app.db.session import get_session
from app.models.bank import Bank
from app.models.chat import ChatMessage, ChatSession  # noqa: F401 - registers SQLModel relationships
from app.models.document import Document  # noqa: F401 - registers SQLModel relationships
from app.models.feature_flag import BankFeatureFlag  # noqa: F401 - registers feature flag table
from app.models.market_utility import ExchangeRate, ExchangeRateBatch
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
test_app.include_router(market_utilities.router, prefix="/api/market-utilities")
test_app.dependency_overrides[get_session] = get_session_override
client = TestClient(test_app)


@pytest.fixture(autouse=True)
def setup_market_utility_db():
    client.cookies.clear()
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        bank = Bank(name="Market Bank", code="MKT01")
        other_bank = Bank(name="Other Market Bank", code="OMKT01")
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
                email="other@test.local",
                password_hash=get_password_hash("Password1"),
                name="Other Staff",
                role="staff_user",
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


def _bank_id(code: str = "MKT01") -> int:
    with Session(engine) as session:
        bank = session.exec(select(Bank).where(Bank.code == code)).first()
        assert bank is not None
        assert bank.id is not None
        return bank.id


def _enable_market_time(bank_code: str = "MKT01"):
    with Session(engine) as session:
        bank_id = _bank_id(bank_code)
        admin = session.exec(select(User).where(User.email == "super@test.local")).first()
        assert admin is not None
        set_feature_flag(
            session,
            bank_id=bank_id,
            feature_key="market_time",
            enabled=True,
            configured_by_user_id=admin.id,
            reason="Market utility pilot",
        )


def _rate_payload(source_name: str = "Treasury Desk") -> dict:
    return {
        "source_name": source_name,
        "notes": "Morning treasury board",
        "rates": [
            {
                "currency_code": "USD",
                "currency_name": "US Dollar",
                "unit": 1,
                "buy_rate": 132.15,
                "sell_rate": 132.75,
                "middle_rate": 132.45,
            },
            {
                "currency_code": "EUR",
                "currency_name": "Euro",
                "unit": 1,
                "buy_rate": 142.5,
                "sell_rate": 143.2,
                "middle_rate": 142.85,
            },
        ],
    }


def test_market_utility_rejects_disabled_feature():
    token = _token("staff@test.local")

    response = client.get(
        "/api/market-utilities/summary",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "feature_disabled"
    assert response.json()["detail"]["feature"] == "market_time"


def test_bank_admin_can_publish_rate_batch_and_staff_can_read_latest_summary():
    _enable_market_time()
    admin_token = _token("admin@test.local")
    staff_token = _token("staff@test.local")

    created = client.post(
        "/api/market-utilities/rate-batches",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=_rate_payload(),
    )
    assert created.status_code == 200
    assert created.json()["source_name"] == "Treasury Desk"
    assert len(created.json()["rates"]) == 2

    summary = client.get(
        "/api/market-utilities/summary",
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    assert summary.status_code == 200
    body = summary.json()
    assert body["timezone"] == "Asia/Kathmandu"
    assert body["business_date"]
    assert body["latest_rate_batch"]["source_name"] == "Treasury Desk"
    assert [rate["currency_code"] for rate in body["latest_rate_batch"]["rates"]] == ["USD", "EUR"]


def test_staff_cannot_publish_rate_batch():
    _enable_market_time()
    token = _token("staff@test.local")

    response = client.post(
        "/api/market-utilities/rate-batches",
        headers={"Authorization": f"Bearer {token}"},
        json=_rate_payload(),
    )

    assert response.status_code == 403


def test_market_summary_is_bank_scoped():
    _enable_market_time()
    _enable_market_time("OMKT01")
    admin_token = _token("admin@test.local")
    other_token = _token("other@test.local")

    created = client.post(
        "/api/market-utilities/rate-batches",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=_rate_payload(),
    )
    assert created.status_code == 200

    other_summary = client.get(
        "/api/market-utilities/summary",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert other_summary.status_code == 200
    assert other_summary.json()["latest_rate_batch"] is None


def test_super_admin_can_read_selected_bank_rate_batches():
    _enable_market_time()
    bank_id = _bank_id()
    admin_token = _token("admin@test.local")
    super_token = _token("super@test.local")

    created = client.post(
        "/api/market-utilities/rate-batches",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=_rate_payload(source_name="Afternoon Treasury Desk"),
    )
    assert created.status_code == 200

    response = client.get(
        f"/api/market-utilities/rate-batches?bank_id={bank_id}",
        headers={"Authorization": f"Bearer {super_token}"},
    )

    assert response.status_code == 200
    assert response.json()[0]["source_name"] == "Afternoon Treasury Desk"
    with Session(engine) as session:
        batches = session.exec(select(ExchangeRateBatch)).all()
        rates = session.exec(select(ExchangeRate)).all()
    assert len(batches) == 1
    assert len(rates) == 2
