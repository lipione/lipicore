import json
from types import SimpleNamespace

import pytest
from sqlmodel import Session
from sqlmodel import SQLModel

from app.models.bank import Bank
from app.models.chat import ChatSession
from app.models.document import Document, DocumentChunk
from app.models.user import User
from app.core.security import get_password_hash
from app.services import rag_service
from test_main import client, engine, get_token


@pytest.fixture(autouse=True)
def setup_test_db():
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
    SQLModel.metadata.drop_all(engine)


def test_staff_can_reload_own_ready_session_upload():
    token = get_token("staff@test.local")

    with Session(engine) as session:
        staff = session.query(User).filter(User.email == "staff@test.local").first()
        bank = session.query(Bank).filter(Bank.code == "TEST01").first()
        chat = ChatSession(bank_id=bank.id, user_id=staff.id, title="Session A")
        session.add(chat)
        session.commit()
        session.refresh(chat)

        own_doc = Document(
            bank_id=bank.id,
            uploaded_by=staff.id,
            title="Loan Policy.pdf",
            file_name="Loan Policy.pdf",
            file_type="pdf",
            file_path="loan-policy.pdf",
            document_type="chat_upload",
            status="ready",
            session_id=chat.id,
            document_scope="session_upload",
            processing_progress=100,
        )
        global_draft = Document(
            bank_id=bank.id,
            uploaded_by=staff.id,
            title="Draft Global.pdf",
            file_name="Draft Global.pdf",
            file_type="pdf",
            file_path="draft-global.pdf",
            document_type="policy",
            status="ready",
            document_scope="global_knowledge",
        )
        session.add(own_doc)
        session.add(global_draft)
        session.commit()
        session.refresh(own_doc)

        chat.active_document_ids_json = json.dumps([own_doc.id])
        session.add(chat)
        session.commit()

    response = client.get("/api/documents?limit=200", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    docs = response.json()
    titles = {doc["title"] for doc in docs}
    assert "Loan Policy.pdf" in titles
    assert "Draft Global.pdf" not in titles


def test_session_rag_prioritizes_active_upload_before_global(monkeypatch):
    calls = []

    def fake_embeddings(_texts):
        return [[0.1, 0.2, 0.3]]

    def fake_search_points(_query_vector, bank_id, limit=5, document_ids=None, session_id=None, document_scope=None, **_kwargs):
        calls.append({
            "bank_id": bank_id,
            "limit": limit,
            "document_ids": document_ids,
            "session_id": session_id,
            "document_scope": document_scope,
        })
        if document_scope == "session_upload":
            return [
                SimpleNamespace(
                    payload={"document_id": 1, "text": "Session loan policy says risk review is required."},
                    score=0.95,
                )
            ]
        return [
            SimpleNamespace(
                payload={"document_id": 2, "text": "Global policy has a different answer."},
                score=0.75,
            )
        ]

    def fake_call_llm(prompt):
        assert "Session loan policy says risk review is required." in prompt
        assert "Global policy has a different answer." not in prompt
        return "Answer from session upload."

    monkeypatch.setattr(rag_service, "generate_embeddings", fake_embeddings)
    monkeypatch.setattr(rag_service, "search_points", fake_search_points)
    monkeypatch.setattr(rag_service, "call_llm", fake_call_llm)

    with Session(engine) as session:
        bank = Bank(name="RAG Bank", code="RAG01")
        user = User(
            email="rag@test.local",
            password_hash="x",
            name="RAG User",
            role="staff_user",
            bank_id=1,
            is_active=True,
        )
        session.add(bank)
        session.commit()
        session.refresh(bank)
        user.bank_id = bank.id
        session.add(user)
        session.commit()

        session_doc = Document(
            id=1,
            bank_id=bank.id,
            uploaded_by=user.id,
            title="Loan Policy.pdf",
            file_name="Loan Policy.pdf",
            file_type="pdf",
            file_path="loan-policy.pdf",
            document_type="chat_upload",
            status="ready",
            session_id=10,
            document_scope="session_upload",
        )
        global_doc = Document(
            id=2,
            bank_id=bank.id,
            uploaded_by=user.id,
            title="Global Policy.pdf",
            file_name="Global Policy.pdf",
            file_type="pdf",
            file_path="global-policy.pdf",
            document_type="policy",
            status="approved",
            version_state="approved",
            document_scope="global_knowledge",
        )
        session.add(session_doc)
        session.add(global_doc)
        session.commit()

        answer, sources = rag_service.generate_rag_response(
            "What are the risks?",
            bank.id,
            "staff_user",
            session,
            active_document_ids=[1],
            session_id=10,
        )

    assert answer == "Answer from session upload."
    assert sources[0]["document_title"] == "Loan Policy.pdf"
    assert len(calls) == 1
    assert calls[0]["document_scope"] == "session_upload"
    assert calls[0]["session_id"] == 10
    assert calls[0]["document_ids"] == [1]


def test_global_rag_returns_cited_sources(monkeypatch):
    def fake_embeddings(_texts):
        return [[0.1, 0.2, 0.3]]

    def fake_search_points(_query_vector, bank_id, limit=5, document_ids=None, session_id=None, document_scope=None, **_kwargs):
        assert document_scope == "global_knowledge"
        return [
            SimpleNamespace(
                payload={
                    "document_id": 3,
                    "text": "Section 4.2 requires branch staff to verify KYC documents before account opening.",
                    "page_number": 12,
                    "section_label": "Section 4.2",
                    "chunk_index": 7,
                },
                score=0.91,
            )
        ]

    def fake_call_llm(prompt):
        assert "Section 4.2 requires branch staff" in prompt
        return "Branch staff must verify KYC documents before account opening."

    monkeypatch.setattr(rag_service, "generate_embeddings", fake_embeddings)
    monkeypatch.setattr(rag_service, "search_points", fake_search_points)
    monkeypatch.setattr(rag_service, "call_llm", fake_call_llm)

    with Session(engine) as session:
        bank = Bank(name="Global RAG Bank", code="GRAG01")
        user = User(
            email="global-rag@test.local",
            password_hash="x",
            name="Global RAG User",
            role="staff_user",
            bank_id=1,
            is_active=True,
        )
        session.add(bank)
        session.commit()
        session.refresh(bank)
        user.bank_id = bank.id
        session.add(user)
        session.commit()

        global_doc = Document(
            id=3,
            bank_id=bank.id,
            uploaded_by=user.id,
            title="Account Opening SOP",
            file_name="account-opening.pdf",
            file_type="pdf",
            file_path="account-opening.pdf",
            document_type="procedure",
            status="approved",
            version_state="approved",
            document_scope="global_knowledge",
        )
        session.add(global_doc)
        session.commit()

        answer, sources = rag_service.generate_rag_response(
            "What should branch staff verify before account opening?",
            bank.id,
            "staff_user",
            session,
    )

    assert "verify KYC" in answer
    assert len(sources) == 1
    assert sources[0]["document_id"] == 3
    assert sources[0]["document_title"] == "Account Opening SOP"
    assert sources[0]["file_name"] == "account-opening.pdf"
    assert sources[0]["document_type"] == "procedure"
    assert sources[0]["page_number"] == 12
    assert sources[0]["section_label"] == "Section 4.2"
    assert sources[0]["chunk_index"] == 7
    assert sources[0]["snippet"] == "Section 4.2 requires branch staff to verify KYC documents before account opening."
    assert sources[0]["passage"] == "Section 4.2 requires branch staff to verify KYC documents before account opening."
    assert sources[0]["relevance_score"] >= rag_service.MIN_SOURCE_RELEVANCE_SCORE


def test_global_rag_returns_not_found_when_relevance_is_too_low(monkeypatch):
    llm_called = False

    def fake_embeddings(_texts):
        return [[0.1, 0.2, 0.3]]

    def fake_search_points(_query_vector, bank_id, limit=5, document_ids=None, session_id=None, document_scope=None, **_kwargs):
        return [
            SimpleNamespace(
                payload={
                    "document_id": 4,
                    "text": "This unrelated HR policy describes leave applications.",
                    "chunk_index": 1,
                },
                score=0.22,
            )
        ]

    def fake_call_llm(_prompt):
        nonlocal llm_called
        llm_called = True
        return "Should not be called."

    monkeypatch.setattr(rag_service, "generate_embeddings", fake_embeddings)
    monkeypatch.setattr(rag_service, "search_points", fake_search_points)
    monkeypatch.setattr(rag_service, "call_llm", fake_call_llm)

    with Session(engine) as session:
        bank = Bank(name="Threshold Bank", code="THR01")
        user = User(
            email="threshold@test.local",
            password_hash="x",
            name="Threshold User",
            role="staff_user",
            bank_id=1,
            is_active=True,
        )
        session.add(bank)
        session.commit()
        session.refresh(bank)
        user.bank_id = bank.id
        session.add(user)
        session.commit()

        doc = Document(
            id=4,
            bank_id=bank.id,
            uploaded_by=user.id,
            title="HR Leave Policy",
            file_name="hr-leave.pdf",
            file_type="pdf",
            file_path="hr-leave.pdf",
            document_type="policy",
            status="approved",
            version_state="approved",
            document_scope="global_knowledge",
        )
        session.add(doc)
        session.commit()

        answer, sources = rag_service.generate_rag_response(
            "What is the suspicious transaction escalation process?",
            bank.id,
            "staff_user",
            session,
        )

    assert answer == rag_service.NOT_FOUND_RESPONSE
    assert sources == []
    assert llm_called is False


def test_hybrid_rag_uses_keyword_match_when_vector_search_misses(monkeypatch):
    def fake_embeddings(_texts):
        return [[0.1, 0.2, 0.3]]

    def fake_search_points(*_args, **_kwargs):
        return []

    def fake_call_llm(prompt):
        assert "Suspicious Transaction Report must be escalated to Compliance within 24 hours." in prompt
        return "Suspicious Transaction Reports must be escalated to Compliance within 24 hours."

    monkeypatch.setattr(rag_service, "generate_embeddings", fake_embeddings)
    monkeypatch.setattr(rag_service, "search_points", fake_search_points)
    monkeypatch.setattr(rag_service, "call_llm", fake_call_llm)

    with Session(engine) as session:
        bank = Bank(name="Hybrid Bank", code="HYB01")
        user = User(
            email="hybrid@test.local",
            password_hash="x",
            name="Hybrid User",
            role="staff_user",
            bank_id=1,
            is_active=True,
        )
        session.add(bank)
        session.commit()
        session.refresh(bank)
        user.bank_id = bank.id
        session.add(user)
        session.commit()

        doc = Document(
            id=5,
            bank_id=bank.id,
            uploaded_by=user.id,
            title="AML SOP",
            file_name="aml-sop.pdf",
            file_type="pdf",
            file_path="aml-sop.pdf",
            document_type="procedure",
            status="approved",
            version_state="approved",
            document_scope="global_knowledge",
        )
        session.add(doc)
        session.commit()
        chunk = DocumentChunk(
            bank_id=bank.id,
            document_id=doc.id,
            chunk_index=2,
            chunk_text="Section 7.1 Suspicious Transaction Report must be escalated to Compliance within 24 hours.",
            page_number=17,
            qdrant_point_id="keyword-only",
            document_status="approved",
            version_state="approved",
        )
        session.add(chunk)
        session.commit()

        answer, sources = rag_service.generate_rag_response(
            "What is the suspicious transaction report escalation timeline?",
            bank.id,
            "staff_user",
            session,
        )

    assert "24 hours" in answer
    assert sources[0]["document_title"] == "AML SOP"
    assert sources[0]["page_number"] == 17
    assert sources[0]["section_label"] == "Section 7.1"
    assert sources[0]["relevance_score"] >= rag_service.MIN_SOURCE_RELEVANCE_SCORE


def test_hybrid_rag_reranks_exact_keyword_match_above_weaker_vector_match(monkeypatch):
    def fake_embeddings(_texts):
        return [[0.1, 0.2, 0.3]]

    def fake_search_points(_query_vector, bank_id, limit=5, document_ids=None, session_id=None, document_scope=None, **_kwargs):
        return [
            SimpleNamespace(
                payload={
                    "document_id": 6,
                    "text": "This generic risk policy discusses transaction monitoring in broad terms.",
                    "chunk_index": 1,
                },
                score=0.7,
            )
        ]

    def fake_call_llm(prompt):
        keyword_position = prompt.index("Section 9.3 Cash Transaction Threshold is NPR 1,000,000.")
        vector_position = prompt.index("This generic risk policy discusses transaction monitoring")
        assert keyword_position < vector_position
        return "The cash transaction threshold is NPR 1,000,000."

    monkeypatch.setattr(rag_service, "generate_embeddings", fake_embeddings)
    monkeypatch.setattr(rag_service, "search_points", fake_search_points)
    monkeypatch.setattr(rag_service, "call_llm", fake_call_llm)

    with Session(engine) as session:
        bank = Bank(name="Rerank Bank", code="RERANK01")
        user = User(
            email="rerank@test.local",
            password_hash="x",
            name="Rerank User",
            role="staff_user",
            bank_id=1,
            is_active=True,
        )
        session.add(bank)
        session.commit()
        session.refresh(bank)
        user.bank_id = bank.id
        session.add(user)
        session.commit()

        vector_doc = Document(
            id=6,
            bank_id=bank.id,
            uploaded_by=user.id,
            title="Generic Risk Policy",
            file_name="risk.pdf",
            file_type="pdf",
            file_path="risk.pdf",
            document_type="policy",
            status="approved",
            version_state="approved",
            document_scope="global_knowledge",
        )
        keyword_doc = Document(
            id=7,
            bank_id=bank.id,
            uploaded_by=user.id,
            title="Cash Transaction SOP",
            file_name="cash-sop.pdf",
            file_type="pdf",
            file_path="cash-sop.pdf",
            document_type="procedure",
            status="approved",
            version_state="approved",
            document_scope="global_knowledge",
        )
        session.add(vector_doc)
        session.add(keyword_doc)
        session.commit()
        chunk = DocumentChunk(
            bank_id=bank.id,
            document_id=keyword_doc.id,
            chunk_index=4,
            chunk_text="Section 9.3 Cash Transaction Threshold is NPR 1,000,000.",
            page_number=22,
            qdrant_point_id="keyword-rerank",
            document_status="approved",
            version_state="approved",
        )
        session.add(chunk)
        session.commit()

        answer, sources = rag_service.generate_rag_response(
            "What is the Cash Transaction Threshold NPR 1,000,000?",
            bank.id,
            "staff_user",
            session,
        )

    assert "NPR 1,000,000" in answer
    assert sources[0]["document_title"] == "Cash Transaction SOP"


def test_postgres_keyword_search_uses_sqlalchemy_execute_api():
    class FakeRows:
        def mappings(self):
            return self

        def all(self):
            return [
                {
                    "document_id": 8,
                    "chunk_index": 3,
                    "chunk_text": "Section 10.2 Customer care must verify identity before account support.",
                    "page_number": 11,
                    "document_scope": "global_knowledge",
                    "session_id": None,
                    "rank": 0.8,
                }
            ]

    class FakeSession:
        executed_params = None

        def execute(self, statement, params):
            self.executed_params = params
            assert "websearch_to_tsquery" in str(statement)
            return FakeRows()

    fake_session = FakeSession()

    results = rag_service._postgres_keyword_search(
        db=fake_session,
        query="customer care identity support",
        bank_id=1,
        limit=3,
        document_scope="global_knowledge",
    )

    assert fake_session.executed_params["query"] == "customer care identity support"
    assert fake_session.executed_params["document_scope"] == "global_knowledge"
    assert results[0].payload["retrieval_source"] == "postgres_fts"
    assert results[0].payload["section_label"] == "Section 10.2"
