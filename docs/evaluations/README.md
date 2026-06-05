# RAG Evaluation Sets

RAG evaluation sets are JSON payloads for `POST /api/evaluations/rag`. The same workflow is available in the frontend at `/evaluations` for analytics-capable roles.

Use evaluations before demos, pilots, ingestion changes, embedding changes, chunk-profile changes, prompt changes, reranker changes, model route changes, and buyer-facing claims about answer quality.

## Who Can Run Evaluations

Allowed roles:

- `super_admin`
- `bank_admin`
- `auditor`
- `data_auditor`

Non-super-admin users can evaluate only their own bank.

## What Evaluations Measure

The evaluator checks:

- expected source recall;
- citation term recall;
- answer term recall;
- expected location recall (document heading, clause number, PDF page, and printed page where available);
- expected document heading recall;
- expected clause number recall;
- expected printed page recall;
- expected jurisdiction recall;
- expected source-status recall;
- expected not-found behavior;
- no-general-policy-advice behavior for unsupported questions;
- per-case pass/fail and aggregate summary.

Evaluations prove only the tested workflow and document set. They do not prove OCR quality, table extraction accuracy, long-file turnaround, or regulatory correctness.

## Minimal Payload

```json
{
  "cases": [
    {
      "id": "unsupported-product",
      "question": "What is the policy for a product the bank does not offer?",
      "expected_not_found": true,
      "no_general_policy_advice": true
    },
    {
      "id": "complaint-escalation",
      "question": "When should a customer complaint be escalated?",
      "expected_source_titles": ["Customer Care SOP"],
      "expected_document_headings": ["Section 4: Complaint Handling"],
      "expected_clause_numbers": ["Clause 4.2"],
      "expected_page_numbers": [12],
      "expected_printed_page_numbers": ["10"],
      "required_citation_terms": ["complaint", "escalation"],
      "required_answer_terms": ["supervisor"]
    }
  ]
}
```

## Release Gate

Run `bank-ready-rag-gate.json` before:

- bank demos;
- bank pilots;
- production go-live;
- embedding or chunk-profile changes;
- prompt or model route changes;
- retrieval/reranker changes;
- major ingestion or OCR changes.

Minimum pass rules:

- Source recall average >= 0.85.
- Citation term recall average >= 0.80.
- Location recall average >= 0.75.
- Policy-like cases must cite required location metadata: PDF page, document heading, and clause number. Printed page is scored when expected but remains optional for answer generation.
- Not-found cases must pass.
- No case may return general bank-policy advice when `no_general_policy_advice` is true.

Treat failures as product issues or document-set issues, not demo variance.

## Starter Packs

Available seed packs:

- `customer-care-rag-seed.json`
- `branch-operations-rag-seed.json`
- `compliance-circular-rag-seed.json`
- `product-faq-rag-seed.json`
- `lending-policy-rag-seed.json`
- `bank-ready-rag-gate.json`
- `legal-citation-hardening-seed.json`

Fixtures:

- `fixtures/customer-care-policy.md`
- `fixtures/compliance-circular.md`
- `fixtures/spreadsheet-policy-summary.md`

These packs are not finished bank-specific release gates. They are templates that must be aligned to the bank's actual approved documents.

## Preparing A Bank-Specific Gate

1. Upload the bank's real policies, SOPs, circulars, customer-care guides, product FAQs, and compliance documents.
2. Approve the documents that should be searchable as global knowledge.
3. Replace `expected_source_titles` with exact document titles from that bank.
4. Add expected PDF pages with `expected_page_numbers`, printed pages, document headings, clause numbers, section labels, or chunk labels where the answer must cite a known location.
5. Add `expected_jurisdictions` where regulator/domain filtering matters (for example `NRB`, `MHA`, `Central Bank`).
6. Add `expected_source_statuses` when the answer must come from live policy material (for example `approved/approved`).
7. Use required citation terms from the actual policy language.
8. Add citation-incomplete checks for policy documents that are missing heading, clause, or PDF page metadata after ingestion.
9. Add not-found cases for unsupported products, stale circulars, or intentionally absent policies.
10. Run the payload in `/evaluations`.
11. Save the output with the release evidence.

## Failure Handling

If an evaluation fails:

- Check whether the expected document was uploaded and approved.
- Check whether document titles match exactly.
- Inspect source passages and relevance scores.
- Check whether the chunk profile split the answer away from the required citation terms.
- Check whether citation metadata was extracted: `document_heading`, `clause_number`, `pdf_page_number`, and optional `printed_page_number`.
- Run `POST /api/documents/{document_id}/citation-backfill` for older approved policy-like documents and re-run the gate.
- Check whether the answer used general knowledge where source-required behavior was expected.
- Re-run only after the document set, expectations, or retrieval behavior is corrected.

For queued long-document analysis, pair RAG evaluations with representative large-file checks: clean PDF, scanned PDF, Excel workbook, SOP/circular with tables, and bilingual/Nepali documents where needed.
