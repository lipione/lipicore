import hashlib

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool

from app.core.security import get_password_hash, password_hash_needs_rehash, verify_password
from app.db.session import get_session
from app.main import app
from app.models.bank import Bank
from app.models.user import User


sqlite_url = "sqlite://"
engine = create_engine(sqlite_url, connect_args={"check_same_thread": False}, poolclass=StaticPool)


def get_session_override():
    with Session(engine) as session:
        yield session


client = TestClient(app)


def legacy_pbkdf2_hash(password: str) -> str:
    salt = "0123456789abcdef0123456789abcdef"
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000)
    return salt + key.hex()


@pytest.fixture(autouse=True)
def setup_db():
    previous_override = app.dependency_overrides.get(get_session)
    app.dependency_overrides[get_session] = get_session_override
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        bank = Bank(name="Security Test Bank", code="SEC01")
        session.add(bank)
        session.commit()

        session.add(
            User(
                email="legacy@test.local",
                password_hash=legacy_pbkdf2_hash("password"),
                name="Legacy User",
                role="staff_user",
                bank_id=bank.id,
                is_active=True,
            )
        )
        session.add(
            User(
                email="locked@test.local",
                password_hash=get_password_hash("password"),
                name="Locked User",
                role="staff_user",
                bank_id=bank.id,
                is_active=True,
            )
        )
        session.commit()

    yield
    SQLModel.metadata.drop_all(engine)
    if previous_override is None:
        app.dependency_overrides.pop(get_session, None)
    else:
        app.dependency_overrides[get_session] = previous_override


def test_new_password_hash_uses_argon2_and_legacy_pbkdf2_still_verifies():
    hashed = get_password_hash("password")

    assert hashed.startswith("$argon2")
    assert verify_password("password", hashed)
    assert not verify_password("wrong-password", hashed)
    assert password_hash_needs_rehash(hashed) is False

    legacy_hash = legacy_pbkdf2_hash("password")
    assert verify_password("password", legacy_hash)
    assert password_hash_needs_rehash(legacy_hash) is True


def test_successful_login_migrates_legacy_password_hash():
    response = client.post("/api/auth/login", data={"username": "legacy@test.local", "password": "password"})

    assert response.status_code == 200
    with Session(engine) as session:
        user = session.exec(select(User).where(User.email == "legacy@test.local")).first()
        assert user is not None
        assert user.password_hash.startswith("$argon2")
        assert verify_password("password", user.password_hash)


def test_repeated_failed_logins_lock_existing_account():
    for _ in range(5):
        response = client.post("/api/auth/login", data={"username": "locked@test.local", "password": "wrong"})
        assert response.status_code == 401

    response = client.post("/api/auth/login", data={"username": "locked@test.local", "password": "password"})

    assert response.status_code == 429
    assert response.json()["detail"] == "Too many failed login attempts. Try again later."
