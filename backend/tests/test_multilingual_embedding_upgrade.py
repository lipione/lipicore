from types import SimpleNamespace
from subprocess import run
import os
import sys

from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool

from app.models.bank import Bank
from app.models.chat import ChatSession  # noqa: F401
from app.models.document import Document, DocumentChunk
from app.models.user import User
from app.services import qdrant_service, reindex_service


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


def setup_function():
    SQLModel.metadata.create_all(engine)


def teardown_function():
    SQLModel.metadata.drop_all(engine)


def test_qdrant_init_rejects_existing_collection_with_wrong_vector_size(monkeypatch):
    class FakeClient:
        def get_collections(self):
            return SimpleNamespace(collections=[SimpleNamespace(name=qdrant_service.COLLECTION_NAME)])

        def get_collection(self, _collection_name):
            return SimpleNamespace(config=SimpleNamespace(params=SimpleNamespace(vectors=SimpleNamespace(size=384))))

    monkeypatch.setattr(qdrant_service, "qdrant_client", FakeClient())
    monkeypatch.setattr(qdrant_service.settings, "EMBEDDING_DIMENSION", 1024)

    try:
        qdrant_service.init_qdrant(max_retries=1)
    except qdrant_service.QdrantCollectionDimensionError as exc:
        assert "384" in str(exc)
        assert "1024" in str(exc)
    else:
        raise AssertionError("Expected dimension mismatch to fail startup")


def test_reindex_service_registers_model_relationships_for_scripts():
    env = os.environ.copy()
    env.update(
        {
            "JWT_SECRET": "test-secret",
            "SUPER_ADMIN_PASSWORD": "test-password",
            "DATABASE_URL": "sqlite://",
        }
    )
    result = run(
        [
            sys.executable,
            "-c",
            (
                "from sqlalchemy.orm import configure_mappers; "
                "import app.services.reindex_service; "
                "configure_mappers()"
            ),
        ],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr or result.stdout


def test_reindex_document_vectors_reuses_existing_chunks(monkeypatch):
    deleted = []
    uploaded_batches = []

    def fake_delete_points(document_id, bank_id):
        deleted.append((document_id, bank_id))

    def fake_generate_embeddings(texts):
        return [[float(index)] * 1024 for index, _text in enumerate(texts, start=1)]

    def fake_upload_points(points):
        uploaded_batches.append(points)

    monkeypatch.setattr(reindex_service, "delete_points_by_document", fake_delete_points)
    monkeypatch.setattr(reindex_service, "generate_embeddings", fake_generate_embeddings)
    monkeypatch.setattr(reindex_service, "upload_points", fake_upload_points)
    monkeypatch.setattr(reindex_service.settings, "EMBEDDING_MODEL", "BAAI/bge-m3")
    monkeypatch.setattr(reindex_service.settings, "EMBEDDING_DIMENSION", 1024)

    with Session(engine) as session:
        bank = Bank(name="Bilingual Bank", code="BI")
        session.add(bank)
        session.commit()
        session.refresh(bank)
        user = User(
            email="staff@bank.local",
            password_hash="x",
            name="Staff",
            role="staff_user",
            bank_id=bank.id,
            is_active=True,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        document = Document(
            bank_id=bank.id,
            uploaded_by=user.id,
            title="Nepali Policy",
            file_name="nepali-policy.pdf",
            file_type="pdf",
            file_path="/tmp/nepali-policy.pdf",
            document_type="policy",
            status="approved",
            version_state="approved",
            document_scope="global_knowledge",
        )
        session.add(document)
        session.commit()
        session.refresh(document)
        bank_id = bank.id
        document_id = document.id
        session.add(
            DocumentChunk(
                bank_id=bank.id,
                document_id=document.id,
                chunk_index=0,
                chunk_text="जोखिम व्यवस्थापन सम्बन्धी नीति",
                page_number=1,
                qdrant_point_id="old-point",
                document_status="approved",
                version_state="approved",
                document_scope="global_knowledge",
            )
        )
        session.commit()

        result = reindex_service.reindex_document_vectors(session, document.id, batch_size=10)
        chunks = session.exec(select(DocumentChunk).where(DocumentChunk.document_id == document.id)).all()

    assert result["indexed_chunks"] == 1
    assert deleted == [(document_id, bank_id)]
    assert len(uploaded_batches) == 1
    assert len(uploaded_batches[0]) == 1
    point = uploaded_batches[0][0]
    assert len(point.vector) == 1024
    assert point.payload["embedding_model"] == "BAAI/bge-m3"
    assert point.payload["embedding_dimension"] == 1024
    assert chunks[0].qdrant_point_id != "old-point"
    assert chunks[0].document_status == "approved"
