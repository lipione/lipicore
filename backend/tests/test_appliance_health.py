import pytest
from sqlmodel import SQLModel, Session, select

from app.core.security import get_password_hash
from app.models.bank import Bank
from app.models.document import Document
from app.models.user import User
from app.services.appliance_health_service import collect_appliance_health
from test_main import client, engine, get_token


class FakeQdrant:
    def __init__(self, fail=False):
        self.fail = fail

    def get_collections(self):
        if self.fail:
            raise RuntimeError("qdrant unavailable")
        return object()


class FakeQueue:
    def __init__(self, count=0, fail=False):
        self.count = count
        self.fail = fail

    def __call__(self):
        if self.fail:
            raise RuntimeError("redis unavailable")
        return self

    def __len__(self):
        return self.count


@pytest.fixture(autouse=True)
def setup_health_db():
    client.cookies.clear()
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        bank = Bank(name="Health Bank", code="HEALTH01")
        session.add(bank)
        session.commit()
        session.refresh(bank)
        admin = User(
            email="admin@test.local",
            password_hash=get_password_hash("password"),
            name="Bank Admin",
            role="bank_admin",
            bank_id=bank.id,
            is_active=True,
        )
        staff = User(
            email="staff@test.local",
            password_hash=get_password_hash("password"),
            name="Staff User",
            role="staff_user",
            bank_id=bank.id,
            is_active=True,
        )
        session.add_all([admin, staff])
        session.commit()
    yield
    client.cookies.clear()
    SQLModel.metadata.drop_all(engine)


def _bank_id() -> int:
    with Session(engine) as session:
        return session.exec(select(Bank).where(Bank.code == "HEALTH01")).first().id


def test_collect_appliance_health_counts_documents_and_queue(tmp_path):
    bank_id = _bank_id()
    with Session(engine) as session:
        session.add_all([
            Document(
                bank_id=bank_id,
                uploaded_by=1,
                title="Approved.pdf",
                file_name="Approved.pdf",
                file_type="pdf",
                file_path="/tmp/approved.pdf",
                status="approved",
                version_state="approved",
                document_scope="global_knowledge",
            ),
            Document(
                bank_id=bank_id,
                uploaded_by=1,
                title="Failed.pdf",
                file_name="Failed.pdf",
                file_type="pdf",
                file_path="/tmp/failed.pdf",
                status="failed",
                version_state="draft",
                document_scope="global_knowledge",
            ),
        ])
        session.commit()

        result = collect_appliance_health(
            db=session,
            bank_id=bank_id,
            qdrant_client=FakeQdrant(),
            queue_factory=FakeQueue(count=3),
            disk_paths=[str(tmp_path)],
        )

    assert result["status"] == "healthy"
    assert result["services"]["database"]["status"] == "healthy"
    assert result["services"]["qdrant"]["status"] == "healthy"
    assert result["services"]["redis"]["status"] == "healthy"
    assert result["ingestion"]["queued_jobs"] == 3
    assert result["documents"]["total"] == 2
    assert result["documents"]["by_status"]["approved"] == 1
    assert result["documents"]["by_status"]["failed"] == 1


def test_collect_appliance_health_reports_degraded_dependencies(tmp_path):
    bank_id = _bank_id()
    with Session(engine) as session:
        result = collect_appliance_health(
            db=session,
            bank_id=bank_id,
            qdrant_client=FakeQdrant(fail=True),
            queue_factory=FakeQueue(fail=True),
            disk_paths=[str(tmp_path / "missing")],
        )

    assert result["status"] == "degraded"
    assert result["services"]["qdrant"]["status"] == "degraded"
    assert result["services"]["redis"]["status"] == "degraded"
    assert result["services"]["storage"]["status"] == "degraded"


def test_appliance_health_endpoint_requires_analytics_role(monkeypatch):
    def fake_collect_appliance_health(**kwargs):
        return {
            "status": "healthy",
            "checked_at": "2026-05-27T00:00:00",
            "services": {},
            "documents": {"total": 0},
            "ingestion": {"queued_jobs": 0},
        }

    monkeypatch.setattr("app.api.analytics.collect_appliance_health", fake_collect_appliance_health)
    admin_token = get_token("admin@test.local")
    staff_token = get_token("staff@test.local")

    ok = client.get("/api/analytics/appliance-health", headers={"Authorization": f"Bearer {admin_token}"})
    denied = client.get("/api/analytics/appliance-health", headers={"Authorization": f"Bearer {staff_token}"})

    assert ok.status_code == 200
    assert ok.json()["status"] == "healthy"
    assert denied.status_code == 403


def test_bank_readiness_endpoint_requires_analytics_role():
    admin_token = get_token("admin@test.local")
    response = client.get(
        "/api/analytics/bank-readiness",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert "status" in payload
    assert "blockers" in payload
    assert "warnings" in payload
