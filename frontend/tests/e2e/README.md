# BankAi E2E Tests

End-to-end tests for the BankAi session-aware Retrieval-Augmented Generation (RAG) system.

These tests do not yet cover queued long-document analysis. Large PDF/OCR/XLS workflows need a separate E2E fixture because they rely on background jobs and longer worker/model timing.

These tests also do not yet fully cover the policy citation-fidelity gate. Manual verification should inspect source panels for document heading, clause number, PDF page, printed page where available, citation verification, and `citation_incomplete` behavior for policy-like answers.

## Quick Start

```bash
# Install dependencies (one time)
npm install --save-dev @playwright/test
npx playwright install chromium

# Run tests
npm run test:e2e

# Run with interactive UI
npm run test:e2e:ui
```

## Test Files

- **session-rag-working.spec.js** - Primary test suite (3 scenarios)
- **diagnostic.spec.js** - Utility for inspecting page structure
- **fixtures/Loan_Policy.txt** - Test document with banking content

## Test Scenarios

### 1. Upload & RAG Response (default)
- Upload document
- Ask "What is the loan amount?"
- Verify response contains "5,000,000"
- Verify source attribution
- Inspect source metadata where available

### 2. Multi-Turn Questions  
- Upload document
- Ask multiple questions
- Verify session context maintained
- Confirm source consistency

### 3. Content Extraction
- Upload document
- Ask about compliance requirements
- Verify accurate extraction
- Confirm proper citation
- Confirm source panel metadata and trust badge state

## Requirements

- Node.js with npm
- Backend running: `http://127.0.0.1:18000` (health check OK)
- Frontend running: `http://127.0.0.1:13000` (HTTP 200)
- Test user: `admin@bankai.io` / `admin123`

## Manual Testing

If automated tests fail, verify manually:

```bash
# 1. Check services
curl http://127.0.0.1:18000/health
curl http://127.0.0.1:13000

# 2. Open in browser
http://127.0.0.1:13000/login

# 3. Login with credentials
email: admin@bankai.io
password: admin123

# 4. Navigate to Chat
# 5. Upload: tests/e2e/fixtures/Loan_Policy.txt
# 6. Ask question about loan amount
# 7. Verify response and source attribution
```

## Test Results

Test execution captures:
- ✓ Screenshots on failure
- ✓ Video recordings on failure
- ✓ Browser console output
- ✓ Network traces

Results stored in: `test-results/` directory

## Troubleshooting

| Problem | Check |
|---------|-------|
| Tests timeout | Backend service health, network connectivity |
| Element not found | Use diagnostic.spec.js to inspect page |
| Upload fails | Check /api/documents endpoint |
| Response missing data | Verify test document contains expected content |
| Source not showing | Check Qdrant vector database status |
| Citation metadata missing | Confirm the fixture contains heading/clause/page markers and inspect chunk metadata |

## Documentation

See `../../E2E_TEST_GUIDE.md` for comprehensive testing guide including:
- Detailed manual procedures
- Architecture verification
- Performance expectations
- CI/CD integration
- Known limitations

## Key Features Tested

✓ Session-aware document upload  
✓ RAG priority search (session docs first)  
✓ Source attribution  
✓ Source metadata panel smoke coverage
✓ Multi-turn question answering  
✓ Context persistence across questions  
✓ Document status tracking (Uploading → Processing → Ready)  

Not yet covered:

- Queueing `/api/long-document-analysis`.
- Polling long-document job status.
- Viewing stored large-file analysis results.
- Policy citation-incomplete refusal fixtures.
- Internal workspace feature-flag flows.

## Performance Notes

- Document upload: 2-5 seconds
- Processing: 10-30 seconds (until "Ready")
- LLM response: 2-10 seconds
- Full round-trip: 20-50 seconds

*Timing depends on local vLLM model tier, GPU load, queue depth, and document size*

## CI/CD Integration

```bash
# In your CI pipeline:
npm install --save-dev @playwright/test
npx playwright install chromium
npm run test:e2e
```

Results can be uploaded as artifacts for review.

---

For full details, see E2E_TEST_GUIDE.md
