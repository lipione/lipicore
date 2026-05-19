import pytest
from sqlmodel import SQLModel, Session, select

from app.models.bank import Bank
from app.models.branding import BrandingSettings
from app.models.user import User
from app.core.security import get_password_hash
from test_main import client, engine, get_token


@pytest.fixture(autouse=True)
def setup_branding_db():
    client.cookies.clear()
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        bank = Bank(name="Test Bank", code="TEST01")
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
        session.commit()

    yield
    client.cookies.clear()
    SQLModel.metadata.drop_all(engine)


def test_public_branding_returns_defaults_when_not_configured():
    response = client.get("/api/config/branding")

    assert response.status_code == 200
    data = response.json()
    assert data["product_name"] == "BankAi"
    assert data["bank_name"] == "Test Bank"
    assert data["primary_color"] == "#17324d"
    assert "ask_knowledge" in data["allowed_modes"]


def test_super_admin_can_update_bank_branding():
    token = get_token("super@test.local")

    with Session(engine) as session:
        bank = session.exec(select(Bank).where(Bank.code == "TEST01")).first()
        bank_id = bank.id

    response = client.patch(
        f"/api/config/branding/{bank_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "product_name": "Everest Bank GPT",
            "bank_name": "Everest Bank",
            "primary_color": "#0f3d2e",
            "accent_color": "#c7902c",
            "welcome_message": "Ask approved bank knowledge.",
            "support_contact": "it-helpdesk@everest.example",
            "disclaimer": "Internal use only.",
            "allowed_modes": ["ask_knowledge", "summarize", "draft"],
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["product_name"] == "Everest Bank GPT"
    assert data["bank_name"] == "Everest Bank"
    assert data["allowed_modes"] == ["ask_knowledge", "summarize", "draft"]


def test_public_branding_can_be_resolved_by_bank_code():
    token = get_token("super@test.local")

    with Session(engine) as session:
        bank = session.exec(select(Bank).where(Bank.code == "TEST01")).first()
        bank_id = bank.id

    client.patch(
        f"/api/config/branding/{bank_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"product_name": "StaffGPT", "bank_name": "Test Bank"},
    )

    response = client.get("/api/config/branding?bank_code=TEST01")

    assert response.status_code == 200
    assert response.json()["product_name"] == "StaffGPT"


def test_staff_cannot_update_branding():
    token = get_token("staff@test.local")

    response = client.patch(
        "/api/config/branding/1",
        headers={"Authorization": f"Bearer {token}"},
        json={"product_name": "Unauthorized"},
    )

    assert response.status_code == 403


def test_branding_persists_as_one_row_per_bank():
    token = get_token("super@test.local")

    client.patch(
        "/api/config/branding/1",
        headers={"Authorization": f"Bearer {token}"},
        json={"product_name": "First Name"},
    )
    client.patch(
        "/api/config/branding/1",
        headers={"Authorization": f"Bearer {token}"},
        json={"product_name": "Second Name"},
    )

    with Session(engine) as session:
        rows = session.exec(select(BrandingSettings).where(BrandingSettings.bank_id == 1)).all()

    assert len(rows) == 1
    assert rows[0].product_name == "Second Name"
