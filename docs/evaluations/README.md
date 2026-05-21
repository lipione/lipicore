# RAG Evaluation Sets

RAG evaluation sets are JSON payloads for `POST /api/evaluations/rag`. The same workflow is available in the frontend at `/evaluations` for analytics-capable roles.

Use them before demos, pilots, ingestion changes, embedding changes, prompt changes, or model changes. A bank-facing claim about citation quality is not credible unless it passes an evaluation set built from that bank's approved documents.

For queued long-document analysis, use these RAG sets together with representative large-file checks. RAG evaluation proves source-backed answer discipline; it does not prove OCR quality, table extraction accuracy, or large-file turnaround.

Allowed roles:

- `super_admin`
- `bank_admin`
- `auditor`
- `data_auditor`

Minimal payload shape:

```json
{
  "cases": [
    {
      "id": "kyc-not-found",
      "question": "What is the policy for a product the bank does not offer?",
      "expected_not_found": true
    },
    {
      "id": "complaint-escalation",
      "question": "When should a customer complaint be escalated?",
      "expected_source_titles": ["Customer Care SOP"],
      "required_citation_terms": ["complaint", "escalation"],
      "required_answer_terms": ["time", "supervisor"]
    }
  ]
}
```

Evaluation output includes pass/fail, source recall, citation term recall, answer term recall, and failed case details. Failed cases should be treated as release blockers for the affected customer workflow.

## Seed Packs

Available starter packs:

- `customer-care-rag-seed.json`
- `branch-operations-rag-seed.json`
- `compliance-circular-rag-seed.json`
- `product-faq-rag-seed.json`
- `lending-policy-rag-seed.json`

These are not workflow modules. They are evaluation assets for the core appliance: retrieval, citations, not-found behavior, and source-backed answer discipline.

Before using any pack as a release gate:

1. Upload and approve the bank's actual customer-care, complaint, card dispute, KYC, and account-servicing documents.
2. Replace `expected_source_titles` with the exact approved document titles in that bank.
3. Adjust `required_citation_terms` to match real section names, page labels, or policy terms.
4. Run the payload through `/evaluations` or the evaluation endpoint.
5. For large-file demos, also queue a clean PDF, scanned PDF, and Excel workbook through Document Library and record result usefulness.
6. Treat failures as product issues, not demo noise.

Each seed file intentionally includes a not-found or no-general-policy-advice case to catch hallucinated answers for unsupported bank products, stale circulars, or autonomous decision claims.
