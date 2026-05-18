from types import SimpleNamespace

from app.models.document import Document
from app.services import ingestion_queue


class FakeQueue:
    def __init__(self):
        self.calls = []

    def enqueue(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return SimpleNamespace(id=kwargs["job_id"])


class FakeSession:
    def __init__(self, doc):
        self.doc = doc
        self.commits = 0

    def get(self, model, document_id):
        assert model is Document
        assert document_id == self.doc.id
        return self.doc

    def add(self, obj):
        assert obj is self.doc

    def commit(self):
        self.commits += 1


def test_enqueue_document_ingestion_marks_document_queued(monkeypatch):
    fake_queue = FakeQueue()
    monkeypatch.setattr(ingestion_queue, "get_ingestion_queue", lambda: fake_queue)
    monkeypatch.setattr(ingestion_queue, "_retry_policy", lambda: None)
    monkeypatch.setattr(ingestion_queue.uuid, "uuid4", lambda: SimpleNamespace(hex="abc123"))

    doc = Document(
        id=42,
        bank_id=1,
        uploaded_by=7,
        file_name="policy.pdf",
        file_type="pdf",
        file_path="/tmp/policy.pdf",
    )
    db = FakeSession(doc)

    job_id = ingestion_queue.enqueue_document_ingestion(42, db)

    assert job_id == "document-42-abc123"
    assert doc.status == "queued"
    assert doc.processing_progress == 5
    assert "document-42-abc123" in doc.processing_message
    assert db.commits == 1
    assert fake_queue.calls[0][0] == ("app.services.ingestion_service.process_document", 42)
    assert fake_queue.calls[0][1]["job_id"] == "document-42-abc123"
