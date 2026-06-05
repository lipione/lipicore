# BankAi Session-Aware RAG E2E Test Guide

## Overview

This document describes the end-to-end testing setup for verifying that the BankAi system correctly implements **session-aware Retrieval-Augmented Generation (RAG)** where documents uploaded in a chat session are prioritized in responses and properly attributed as sources.

Queued long-document analysis is a separate workflow and is not yet covered by this E2E guide. It should get its own fixture set for large PDFs, scanned PDFs, and Excel workbooks because it depends on background RQ jobs and longer worker/model timing.

## Test Objectives

1. **Verify document upload workflow**: Users can upload documents to a chat session
2. **Verify session-scoped RAG**: Uploaded documents are prioritized in RAG searches over global knowledge
3. **Verify source attribution**: Generated responses correctly cite source documents and expose source metadata
4. **Verify session persistence**: Follow-up questions maintain context with previously uploaded documents
5. **Verify trust metadata**: Source panels and badges show citation verification, and policy-like answers show heading/clause/page metadata when available

## Test Infrastructure

### Setup

```bash
cd /e/BankAi/frontend
npm install --save-dev @playwright/test
npx playwright install chromium
```

### Test Files

- **Tests**: `tests/e2e/session-rag-working.spec.js` - Primary test suite with 3 scenarios
- **Diagnostic**: `tests/e2e/diagnostic.spec.js` - Utility test to inspect page structure  
- **Test Document**: `tests/e2e/fixtures/Loan_Policy.txt` - Sample banking document for testing

### Running Tests

```bash
# Run all E2E tests
npm run test:e2e

# Run tests with UI (interactive mode)
npm run test:e2e:ui

# Run tests in debug mode
npm run test:e2e:debug

# Run specific test file
npx playwright test tests/e2e/session-rag-working.spec.js

# Run with verbose output
npx playwright test --verbose
```

## Test Scenarios

### Scenario 1: Document Upload and RAG Response with Attribution

**What it tests:**
- Navigate to chat interface
- Upload a test document (Loan_Policy.txt) containing banking agreement information
- Ask a question that should be answered from the uploaded document
- Verify the response contains the expected information
- Verify source attribution shows the uploaded document

**Key assertions:**
- Document name "Loan_Policy" appears in the UI after upload
- "Ready for questions" badge appears when document is processed
- Response contains loan amount ($5,000,000) from the document
- Source chip correctly attributes the response to the uploaded document
- Source evidence panel exposes document title, passage, relevance, citation verification, and available page/section/heading/clause metadata

**Pass criteria:** ✓ All assertions pass

### Scenario 2: Multi-Turn Question Answering with Session Context

**What it tests:**
- Upload document to a session
- Ask multiple follow-up questions
- Verify each response uses the same uploaded document as source
- Verify session context is maintained across questions

**Questions tested:**
1. "What is the interest rate?" (Answer: 8.5%)
2. "What are the monthly payments?" (Answer: NRP 157,500)

**Pass criteria:** ✓ Both follow-up questions answered correctly with document source

### Scenario 3: Document Content Extraction and Compliance

**What it tests:**
- Upload document
- Ask about compliance requirements
- Verify LLM extracts and cites specific document sections
- Verify proper handling of structured information from documents

**Key assertions:**
- Response mentions "compliance" and "financial" (from document)
- Source attribution maintained
- Information is accurately extracted

**Pass criteria:** ✓ Compliance requirements correctly cited

## Manual Testing Procedure

If automated tests fail, perform these manual steps to verify functionality:

### Prerequisites

1. Backend running: `curl http://127.0.0.1:18000/health` returns `{"status":"ok"}`
2. Frontend running: `curl http://127.0.0.1:13000` returns 200
3. Admin user exists: `admin@bankai.io` / `admin123`

### Manual Test Steps

1. **Navigate to Application**
   ```
   Open: http://127.0.0.1:13000/login
   ```

2. **Log In**
   ```
   Email: admin@bankai.io
   Password: admin123
   Click: Sign In
   ```

3. **Access Chat**
   ```
   Navigate to: http://127.0.0.1:13000/chat
   Or click "Chat" in sidebar
   ```

4. **Upload Test Document**
   ```
   Click: Upload Document button (paperclip icon)
   Select: /e/BankAi/frontend/tests/e2e/fixtures/Loan_Policy.txt
   Wait: Document card appears showing progress
   Wait: Badge changes to "Ready for questions" (green checkmark)
   ```

5. **Test Question 1: Loan Amount**
   ```
   Input: "What is the loan amount in the agreement?"
   Expected Response:
     - Contains "5,000,000" or "5 million"
     - Shows source attribution: "Loan_Policy"
     - Includes relevance score
   ```

6. **Test Question 2: Interest Rate**
   ```
   Input: "What is the interest rate?"
   Expected Response:
     - Contains "8.5%"
     - Same document source
     - Professional formatting
   ```

7. **Test Question 3: Payments**
   ```
   Input: "What are the monthly payments?"
   Expected Response:
     - Contains "157,500"
     - Same document source
     - Properly formatted number
   ```

8. **Test Question 4: Compliance**
   ```
   Input: "List the compliance requirements."
   Expected Response:
     - Mentions "quarterly financial statements"
     - Mentions "annual audit"
     - Source: Loan_Policy
   ```

### Expected Behavior

- ✓ Document uploads successfully
- ✓ Status changes from "Uploading" → "Processing" → "Ready for questions"
- ✓ All questions are answered with information from the uploaded document
- ✓ Source chips appear below each response showing document name
- ✓ Source evidence panel opens and shows passage, relevance, citation verification, and available page/section/heading/clause metadata
- ✓ Questions maintain session context (subsequent questions use same document)
- ✓ No external knowledge is used (only uploaded document is referenced)

### Troubleshooting

| Issue | Solution |
|-------|----------|
| Upload fails | Check backend API connectivity: `curl http://127.0.0.1:18000/api/documents` |
| "Ready for questions" doesn't appear | Check document processing: Backend embedding service may be slow |
| Response doesn't contain expected data | Verify test document contains the data at `/e/BankAi/frontend/tests/e2e/fixtures/Loan_Policy.txt` |
| Source not attributed | Check Qdrant service running: Document vectors may not be indexed |
| Citation metadata missing | Confirm the fixture/document has page, heading, or clause markers and inspect ingestion chunk metadata |
| Follow-up questions use global knowledge | Check session-aware RAG implementation in `backend/app/api/chat.py` line 160-168 |

## Architecture Verification

The E2E tests verify these critical backend components:

### 1. Session Document Tracking
**File:** `backend/app/api/chat.py` lines 23-46
- `_session_active_document_ids()`: Merges stored and requested document IDs
- `_track_session_document()`: Persists uploaded document ID to session

### 2. Session-Aware RAG
**File:** `backend/app/services/rag_service.py` lines 70-100
- Priority 1: Search documents uploaded to current session
- Priority 2: Search global knowledge (limited by remaining limit)
- De-duplication: Prevents same document appearing in both tiers

### 3. Document Source Attribution
**File:** `backend/app/services/rag_service.py` lines 42-49
- `_build_source()`: Normalizes source dict with document_title and title fields
- Includes document_id, file_name, and relevance_score
- Current source payloads may also include pdf_page_number, printed_page_number, document_heading, clause_number, citation_confidence, and citation_incomplete_reasons

### 4. Stream Response Flow
**File:** `backend/app/api/chat.py` lines 198-370
- Emits "Searching documents..." status event
- Performs session-aware RAG search inside generator
- Emits "Generating response..." status event
- Streams LLM tokens
- Generates follow-up suggestions
- Persists ChatMessage with sources and suggestions

## Performance Expectations

- **Document Upload**: 2-5 seconds
- **Document Processing**: 5-30 seconds (depends on file size and embedding model)
- **RAG Search**: < 500ms
- **LLM Inference**: 2-10 seconds on local vLLM, depending on model tier and GPU load
- **Complete Round-trip**: 20-50 seconds

## CI/CD Integration

To run these tests in CI:

```yaml
# Example GitHub Actions workflow
- name: Run E2E Tests
  run: |
    npm install --save-dev @playwright/test
    npx playwright install chromium
    npm run test:e2e
  
- name: Upload Test Results
  if: always()
  uses: actions/upload-artifact@v3
  with:
    name: playwright-report
    path: playwright-report/
```

## Test Coverage

| Component | Coverage | Status |
|-----------|----------|--------|
| Document Upload | ✓ | Implemented |
| Session Tracking | ✓ | Implemented |
| RAG Priority Search | ✓ | Implemented |
| Source Attribution | ✓ | Implemented |
| Source Metadata Panel | ✓ | Implemented |
| Multi-turn Context | ✓ | Implemented |
| Follow-up Suggestions | ✓ | Implemented |
| Error Handling | ✓ | Implemented |

## Known Limitations

1. **File Upload State**: Test relies on UI text matching which may vary with design changes
2. **Local LLM Latency**: LLM responses depend on vLLM model tier, GPU load, and queue depth.
3. **Vector DB Indexing**: Qdrant indexing adds processing time before documents are searchable
4. **Session Cleanup**: Tests don't clean up sessions between runs; consider adding cleanup step

## Future Enhancements

- [ ] Add tests for error cases (invalid files, oversized uploads)
- [ ] Test document deletion and re-upload
- [ ] Test switching between multiple sessions
- [ ] Test concurrent document uploads
- [ ] Test queued long-document analysis create/poll/result flow
- [ ] Performance benchmarking tests
- [ ] Add visual regression tests with screenshots
- [ ] Test multi-language support (English and Nepali)

## References

- **Session-Aware RAG Design**: `backend/app/services/rag_service.py`
- **Chat Streaming**: `backend/app/api/chat.py`
- **Document Embedding**: `backend/app/services/embedding_service.py`
- **PII Masking**: `backend/app/services/guardrail_service.py`
- **Frontend Chat Component**: `frontend/src/pages/ChatAssistant.jsx`
