import json

from sqlmodel import Session, SQLModel, select

from app.core.security import get_password_hash
from app.models.audit import AuditLog
from app.models.bank import Bank
from app.models.document import Document, DocumentChunk
from app.models.user import User
from test_main import client, engine, get_token


def test_backfill_updates_existing_policy_chunks_and_qdrant_payload(monkeypatch):
    updates = []
    point_updates = []

    def fake_update_points(document_id, bank_id, payload):
        updates.append({"document_id": document_id, "bank_id": bank_id, "payload": payload})

    def fake_update_point(point_id, payload, *, bank_id, document_id):
        point_updates.append({
            "point_id": point_id,
            "payload": payload,
            "bank_id": bank_id,
            "document_id": document_id,
        })

    monkeypatch.setattr(
        "app.services.policy_citation_backfill_service.update_points_by_document_payload",
        fake_update_points,
    )
    monkeypatch.setattr(
        "app.services.policy_citation_backfill_service.update_point_payload",
        fake_update_point,
    )

    SQLModel.metadata.create_all(engine)
    try:
        from app.services.policy_citation_backfill_service import backfill_document_citation_metadata

        with Session(engine) as session:
            bank = Bank(name="Backfill Bank", code="BACK01")
            session.add(bank)
            session.commit()
            session.refresh(bank)
            user = User(
                email="backfill@test.local",
                password_hash="x",
                name="Backfill User",
                role="bank_admin",
                bank_id=bank.id,
            )
            session.add(user)
            session.commit()
            document = Document(
                bank_id=bank.id,
                uploaded_by=user.id,
                title="Credit Policy",
                file_name="credit.pdf",
                file_type="pdf",
                file_path="credit.pdf",
                document_type="policy",
                status="approved",
                version_state="approved",
            )
            session.add(document)
            session.commit()
            session.refresh(document)
            chunk = DocumentChunk(
                bank_id=bank.id,
                document_id=document.id,
                chunk_index=0,
                chunk_text="Chapter 5: SME Lending\nClause 5.1(a) DSR limit\nPage 38",
                page_number=42,
                printed_page_number="stale-page",
                document_heading="Chapter 99: Stale Heading",
                clause_number="Clause 99.9",
                qdrant_point_id="point-1",
            )
            session.add(chunk)
            session.commit()

            result = backfill_document_citation_metadata(session, document_id=document.id, bank_id=bank.id)
            refreshed = session.exec(select(DocumentChunk).where(DocumentChunk.document_id == document.id)).first()
            expected_bank_id = bank.id
            expected_document_id = document.id

        assert result["updated_chunks"] == 1
        assert refreshed.document_heading == "Chapter 5: SME Lending"
        assert refreshed.clause_number == "Clause 5.1(a)"
        assert refreshed.printed_page_number == "38"
        assert json.loads(refreshed.citation_incomplete_reasons_json) == []
        assert updates[0]["payload"]["citation_metadata_backfilled"] is True
        assert point_updates[0]["point_id"] == "point-1"
        assert point_updates[0]["bank_id"] == expected_bank_id
        assert point_updates[0]["document_id"] == expected_document_id
        assert point_updates[0]["payload"]["document_heading"] == "Chapter 5: SME Lending"
    finally:
        SQLModel.metadata.drop_all(engine)


def test_backfill_commits_database_metadata_when_qdrant_point_update_fails(monkeypatch):
    def fake_update_points(*_args, **_kwargs):
        return None

    def failing_update_point(*_args, **_kwargs):
        raise RuntimeError("qdrant unavailable")

    monkeypatch.setattr(
        "app.services.policy_citation_backfill_service.update_points_by_document_payload",
        fake_update_points,
    )
    monkeypatch.setattr(
        "app.services.policy_citation_backfill_service.update_point_payload",
        failing_update_point,
    )

    SQLModel.metadata.create_all(engine)
    try:
        from app.services.policy_citation_backfill_service import backfill_document_citation_metadata

        with Session(engine) as session:
            bank = Bank(name="Backfill Failure Bank", code="BFAL01")
            session.add(bank)
            session.commit()
            session.refresh(bank)
            user = User(
                email="failure-owner@test.local",
                password_hash="x",
                name="Failure Owner",
                role="bank_admin",
                bank_id=bank.id,
            )
            session.add(user)
            session.commit()
            document = Document(
                bank_id=bank.id,
                uploaded_by=user.id,
                title="Credit Policy",
                file_name="credit.pdf",
                file_type="pdf",
                file_path="credit.pdf",
                document_type="policy",
                status="approved",
                version_state="approved",
            )
            session.add(document)
            session.commit()
            session.refresh(document)
            session.add(DocumentChunk(
                bank_id=bank.id,
                document_id=document.id,
                chunk_index=0,
                chunk_text="Chapter 5: SME Lending\nClause 5.1(a) DSR limit\nPage 38",
                page_number=42,
                qdrant_point_id="point-failure",
            ))
            session.commit()

            result = backfill_document_citation_metadata(session, document_id=document.id, bank_id=bank.id)
            refreshed = session.exec(select(DocumentChunk).where(DocumentChunk.document_id == document.id)).first()

        assert result["updated_chunks"] == 1
        assert result["qdrant_updated_points"] == 0
        assert result["qdrant_update_errors"][0]["point_id"] == "point-failure"
        assert refreshed.document_heading == "Chapter 5: SME Lending"
        assert refreshed.clause_number == "Clause 5.1(a)"
        assert refreshed.printed_page_number == "38"
    finally:
        SQLModel.metadata.drop_all(engine)


def test_backfill_returns_zero_for_missing_or_cross_bank_document():
    SQLModel.metadata.create_all(engine)
    try:
        from app.services.policy_citation_backfill_service import backfill_document_citation_metadata

        with Session(engine) as session:
            bank = Bank(name="Backfill Owner Bank", code="BOWN01")
            other_bank = Bank(name="Backfill Other Bank", code="BOTH01")
            session.add(bank)
            session.add(other_bank)
            session.commit()
            session.refresh(bank)
            session.refresh(other_bank)
            user = User(
                email="owner@test.local",
                password_hash="x",
                name="Owner",
                role="bank_admin",
                bank_id=bank.id,
            )
            session.add(user)
            session.commit()
            document = Document(
                bank_id=bank.id,
                uploaded_by=user.id,
                title="Credit Policy",
                file_name="credit.pdf",
                file_type="pdf",
                file_path="credit.pdf",
                document_type="policy",
                status="approved",
                version_state="approved",
            )
            session.add(document)
            session.commit()
            session.refresh(document)

            missing = backfill_document_citation_metadata(session, document_id=999999, bank_id=bank.id)
            cross_bank = backfill_document_citation_metadata(session, document_id=document.id, bank_id=other_bank.id)

        assert missing["updated_chunks"] == 0
        assert cross_bank["updated_chunks"] == 0
    finally:
        SQLModel.metadata.drop_all(engine)


def test_bank_admin_endpoint_backfills_citations_and_source_viewer_returns_metadata(monkeypatch, tmp_path):
    updates = []
    point_updates = []

    def fake_update_points(document_id, bank_id, payload):
        updates.append({"document_id": document_id, "bank_id": bank_id, "payload": payload})

    def fake_update_point(point_id, payload, *, bank_id, document_id):
        point_updates.append({
            "point_id": point_id,
            "payload": payload,
            "bank_id": bank_id,
            "document_id": document_id,
        })

    monkeypatch.setattr(
        "app.services.policy_citation_backfill_service.update_points_by_document_payload",
        fake_update_points,
    )
    monkeypatch.setattr(
        "app.services.policy_citation_backfill_service.update_point_payload",
        fake_update_point,
    )

    SQLModel.metadata.create_all(engine)
    try:
        policy_pdf = tmp_path / "credit.pdf"
        policy_pdf.write_bytes(b"%PDF-1.4\n% LipiCore test policy\n")

        with Session(engine) as session:
            bank = Bank(name="Backfill API Bank", code="BAPI01")
            session.add(bank)
            session.commit()
            session.refresh(bank)
            admin = User(
                email="backfill-admin@test.local",
                password_hash=get_password_hash("password"),
                name="Backfill Admin",
                role="bank_admin",
                bank_id=bank.id,
                is_active=True,
            )
            staff = User(
                email="backfill-staff@test.local",
                password_hash=get_password_hash("password"),
                name="Backfill Staff",
                role="staff_user",
                bank_id=bank.id,
                is_active=True,
            )
            compliance_user = User(
                email="backfill-compliance-user@test.local",
                password_hash=get_password_hash("password"),
                name="Backfill Compliance User",
                role="compliance_user",
                bank_id=bank.id,
                is_active=True,
            )
            other_bank = Bank(name="Backfill Other API Bank", code="BOAPI01")
            session.add(other_bank)
            session.commit()
            session.refresh(other_bank)
            other_admin = User(
                email="backfill-other-admin@test.local",
                password_hash=get_password_hash("password"),
                name="Backfill Other Admin",
                role="bank_admin",
                bank_id=other_bank.id,
                is_active=True,
            )
            session.add(admin)
            session.add(staff)
            session.add(compliance_user)
            session.add(other_admin)
            session.commit()
            document = Document(
                bank_id=bank.id,
                uploaded_by=admin.id,
                title="Credit Policy",
                file_name="credit.pdf",
                file_type="pdf",
                file_path=str(policy_pdf),
                document_type="policy",
                status="approved",
                version_state="approved",
                document_scope="global_knowledge",
            )
            session.add(document)
            session.commit()
            session.refresh(document)
            session.add(DocumentChunk(
                bank_id=bank.id,
                document_id=document.id,
                chunk_index=0,
                chunk_text="Chapter 5: SME Lending\nClause 5.1(a) DSR limit\nPage 38",
                page_number=42,
                qdrant_point_id="point-api",
                document_status="approved",
                version_state="approved",
            ))
            session.commit()
            document_id = document.id
            bank_id = bank.id

        admin_token = get_token("backfill-admin@test.local")
        response = client.post(
            f"/api/documents/{document_id}/citation-backfill",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        assert response.json()["updated_chunks"] == 1
        assert response.json()["qdrant_update_errors"] == []
        assert updates
        assert point_updates[0]["payload"]["clause_number"] == "Clause 5.1(a)"
        assert point_updates[0]["bank_id"] == bank_id
        assert point_updates[0]["document_id"] == document_id

        with Session(engine) as session:
            audit = session.exec(
                select(AuditLog).where(AuditLog.action == "backfill_citation_metadata")
            ).first()
            assert audit is not None
            assert audit.resource_id == str(document_id)
            assert audit.user_id is not None
            assert json.loads(audit.metadata_json)["updated_chunks"] == 1

        compliance_token = get_token("backfill-compliance-user@test.local")
        denied_response = client.post(
            f"/api/documents/{document_id}/citation-backfill",
            headers={"Authorization": f"Bearer {compliance_token}"},
        )
        assert denied_response.status_code == 403

        other_token = get_token("backfill-other-admin@test.local")
        cross_bank_response = client.post(
            f"/api/documents/{document_id}/citation-backfill",
            headers={"Authorization": f"Bearer {other_token}"},
        )
        assert cross_bank_response.status_code == 404

        staff_token = get_token("backfill-staff@test.local")
        source_response = client.get(
            f"/api/documents/{document_id}/source?page_number=42",
            headers={"Authorization": f"Bearer {staff_token}"},
        )

        assert source_response.status_code == 200
        chunk = source_response.json()["chunks"][0]
        assert chunk["pdf_page_number"] == 42
        assert chunk["printed_page_number"] == "38"
        assert chunk["document_heading"] == "Chapter 5: SME Lending"
        assert chunk["clause_number"] == "Clause 5.1(a)"
        assert chunk["citation_incomplete_reasons_json"] == "[]"

        file_response = client.get(
            f"/api/documents/{document_id}/file",
            headers={"Authorization": f"Bearer {staff_token}"},
        )
        assert file_response.status_code == 200
        assert file_response.content.startswith(b"%PDF-1.4")
        assert file_response.headers["content-type"].startswith("application/pdf")
        assert file_response.headers["content-disposition"].startswith("inline;")
    finally:
        SQLModel.metadata.drop_all(engine)
