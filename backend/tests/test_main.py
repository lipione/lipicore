import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool

from app.main import app
from app.db.session import get_session
from app.models.user import User
from app.models.bank import Bank
from app.core.security import create_access_token, get_password_hash

# Setup in-memory database for testing
sqlite_url = "sqlite://"
engine = create_engine(sqlite_url, connect_args={"check_same_thread": False}, poolclass=StaticPool)

def get_session_override():
    with Session(engine) as session:
        yield session

app.dependency_overrides[get_session] = get_session_override
client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        # Create test bank
        bank = Bank(name="Test Bank", code="TEST01")
        session.add(bank)
        session.commit()
        
        # Create test super admin
        admin = User(
            email="super@test.local",
            password_hash=get_password_hash("password"),
            name="Super Admin",
            role="super_admin",
            bank_id=bank.id,
            is_active=True
        )
        session.add(admin)
        
        # Create test staff user
        staff = User(
            email="staff@test.local",
            password_hash=get_password_hash("password"),
            name="Staff User",
            role="staff_user",
            bank_id=bank.id,
            is_active=True
        )
        session.add(staff)

        # Create test auditor user
        auditor = User(
            email="auditor@test.local",
            password_hash=get_password_hash("password"),
            name="Audit User",
            role="auditor",
            bank_id=bank.id,
            is_active=True
        )
        session.add(auditor)
        session.commit()
        
    yield
    SQLModel.metadata.drop_all(engine)

def get_token(email: str):
    with Session(engine) as session:
        user = session.exec(select(User).where(User.email == email)).first()
        assert user is not None
        return create_access_token(user.id)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200

def test_unauthorized_access():
    response = client.get("/api/users")
    assert response.status_code == 401

def test_login_success():
    response = client.post("/api/auth/login", data={"username": "staff@test.local", "password": "password"})
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_role_based_route_protection():
    token = get_token("staff@test.local")
    
    # Staff cannot view all users (only Bank Admin / Super Admin)
    response = client.get("/api/users", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403

def test_audit_logs_access():
    admin_token = get_token("super@test.local")
    staff_token = get_token("staff@test.local")
    
    # Super admin can view
    response = client.get("/api/audit", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    
    # Staff cannot view
    response = client.get("/api/audit", headers={"Authorization": f"Bearer {staff_token}"})
    assert response.status_code == 403

def test_analytics_summary_requires_analytics_role():
    admin_token = get_token("super@test.local")
    auditor_token = get_token("auditor@test.local")
    staff_token = get_token("staff@test.local")

    response = client.get("/api/analytics/summary", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200

    response = client.get("/api/analytics/summary", headers={"Authorization": f"Bearer {auditor_token}"})
    assert response.status_code == 200

    response = client.get("/api/analytics/summary", headers={"Authorization": f"Bearer {staff_token}"})
    assert response.status_code == 403

def test_model_status_requires_analytics_role():
    admin_token = get_token("super@test.local")
    auditor_token = get_token("auditor@test.local")
    staff_token = get_token("staff@test.local")

    response = client.get("/api/chat/models/status", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200

    response = client.get("/api/chat/models/status", headers={"Authorization": f"Bearer {auditor_token}"})
    assert response.status_code == 200

    response = client.get("/api/chat/models/status", headers={"Authorization": f"Bearer {staff_token}"})
    assert response.status_code == 403
