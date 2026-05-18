# Secure Messenger Add-on Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a separate LipiCore Secure Messenger add-on Phase 1 with a web widget, isolated messaging storage, secure attachments, automatic department channels, custom groups, announcements, and no RAG/AI integration.

**Architecture:** The backend adds an isolated `/api/messenger` router backed by messenger-specific models, schemas, services, policy, audit, and attachment storage. LipiCore Core only hosts the frontend widget and uses narrow session/user integration; no RAG, embedding, document ingestion, or AI service is imported by messenger code.

**Tech Stack:** FastAPI, SQLModel, PostgreSQL/Alembic, pytest, React, Vite, Tailwind CSS, lucide-react, axios.

---

### Task 1: Backend Contract Tests

**Files:**
- Create: `backend/tests/test_messenger.py`

- [ ] **Step 1: Write failing tests for the messenger boundary and core workflows**

```python
def test_messenger_staff_can_bootstrap_with_department_channel():
    token = get_token("ops@test.local")
    response = client.get("/api/messenger/bootstrap", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["policy"]["enabled"] is True
    assert any(item["type"] == "department" and item["title"] == "Operations" for item in response.json()["conversations"])

def test_messenger_custom_group_send_and_unread_count():
    owner_token = get_token("ops@test.local")
    member_token = get_token("credit@test.local")
    response = client.post(
        "/api/messenger/conversations/custom",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"title": "Loan Review", "member_ids": [2]},
    )
    assert response.status_code == 200
    conversation_id = response.json()["id"]
    send_response = client.post(
        f"/api/messenger/conversations/{conversation_id}/messages",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"content": "Please review the attached loan checklist."},
    )
    assert send_response.status_code == 200
    unread_response = client.get("/api/messenger/unread-count", headers={"Authorization": f"Bearer {member_token}"})
    assert unread_response.json()["unread_count"] == 1

def test_messenger_attachment_upload_is_isolated_from_documents_and_audited():
    token = get_token("ops@test.local")
    conversation_id = create_direct_conversation(token, 2)
    response = client.post(
        f"/api/messenger/conversations/{conversation_id}/attachments",
        headers={"Authorization": f"Bearer {token}"},
        data={"caption": "Screenshot for internal review"},
        files={"file": ("notice.png", b"image-bytes", "image/png")},
    )
    assert response.status_code == 200
    with Session(engine) as session:
        assert session.exec(select(Document)).all() == []
        assert session.exec(select(MessengerAuditEvent).where(MessengerAuditEvent.action == "attachment_upload")).first()

def test_messenger_has_no_rag_or_ai_routes():
    token = get_token("ops@test.local")
    response = client.post(
        "/api/messenger/conversations/1/send-to-ai",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404
```

- [ ] **Step 2: Run tests and verify they fail because `/api/messenger` does not exist**

Run: `JWT_SECRET=test-secret SUPER_ADMIN_PASSWORD=test-password pytest backend/tests/test_messenger.py -q`
Expected: failures with 404 responses or import errors for missing messenger models.

### Task 2: Backend Models, Schemas, Service, Router, And Migration

**Files:**
- Create: `backend/app/models/messenger.py`
- Create: `backend/app/schemas/messenger.py`
- Create: `backend/app/services/messenger_service.py`
- Create: `backend/app/api/messenger.py`
- Create: `backend/alembic/versions/006_secure_messenger_addon.py`
- Modify: `backend/app/core/config.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Implement messenger SQLModel tables**

Create messenger-specific policy, conversation, membership, message, attachment, and audit event tables. Keep table names prefixed with `messenger` and include `bank_id` on every persisted row.

- [ ] **Step 2: Implement schemas**

Add request/response schemas for bootstrap, policy, conversations, messages, attachments, unread count, custom group creation, direct conversation creation, and read marking.

- [ ] **Step 3: Implement service logic**

Implement:
- policy defaults,
- department channel reconciliation from `User.department`,
- membership checks,
- direct conversation lookup/create,
- custom group creation,
- announcement creation for admins,
- message send/list,
- unread counts,
- attachment validation/storage,
- messenger audit events.

- [ ] **Step 4: Implement API router**

Expose:
- `GET /api/messenger/bootstrap`
- `GET /api/messenger/unread-count`
- `GET /api/messenger/conversations`
- `POST /api/messenger/conversations/direct`
- `POST /api/messenger/conversations/custom`
- `POST /api/messenger/conversations/announcements`
- `GET /api/messenger/conversations/{conversation_id}/messages`
- `POST /api/messenger/conversations/{conversation_id}/messages`
- `POST /api/messenger/conversations/{conversation_id}/read`
- `POST /api/messenger/conversations/{conversation_id}/attachments`

- [ ] **Step 5: Wire router and migration**

Register the router under `/api/messenger`, add `MESSENGER_UPLOAD_DIR` to settings, and create Alembic revision `006`.

- [ ] **Step 6: Run backend tests**

Run: `JWT_SECRET=test-secret SUPER_ADMIN_PASSWORD=test-password pytest backend/tests/test_messenger.py -q`
Expected: all messenger tests pass.

### Task 3: Frontend Widget API And UI

**Files:**
- Create: `frontend/src/api/messenger.js`
- Create: `frontend/src/components/messenger/SecureMessengerWidget.jsx`
- Modify: `frontend/src/layouts/MainLayout.jsx`

- [ ] **Step 1: Add frontend API wrapper**

Use the existing axios client to call `/messenger/bootstrap`, `/messenger/unread-count`, conversation creation, message list/send, read marking, and attachment upload.

- [ ] **Step 2: Add Messenger-style widget**

Build a floating launcher with unread badge, compact panel, conversation list, active conversation view, message composer, file/image picker, group creation, department channels, DMs, announcements, loading/error states, and responsive mobile layout.

- [ ] **Step 3: Mount in LipiCore layout**

Render the widget inside `MainLayout` so it appears on all authenticated LipiCore screens without adding a full route.

- [ ] **Step 4: Run frontend checks**

Run: `npm run lint` and `npm run build` from `frontend`.
Expected: both exit 0.

### Task 4: Full Verification

**Files:**
- All changed backend/frontend files.

- [ ] **Step 1: Run focused backend tests**

Run: `JWT_SECRET=test-secret SUPER_ADMIN_PASSWORD=test-password pytest backend/tests/test_messenger.py backend/tests/test_main.py -q`
Expected: all selected tests pass.

- [ ] **Step 2: Run frontend build**

Run: `npm run build` from `frontend`.
Expected: Vite build exits 0.

- [ ] **Step 3: Run browser check**

Start the dev server, open the authenticated app path where possible, and visually inspect the widget for layout, overlap, and console errors.
