# LipiCore Bank Safe Capability Matrix

**Prepared:** May 21, 2026  
**Use for:** Bank replies, procurement discussions, demos, and pilot scoping

## One-Line Product Definition

LipiCore is an airgapped AI staff-assistance and knowledge-retrieval appliance for banks. It runs inside bank-controlled infrastructure and helps staff find answers from approved documents, analyze internal files, summarize, compare, and draft staff-ready responses without sending bank data to external AI providers.

## Standard Bank Reply

LipiCore is an airgapped AI assistant for bank staff. It runs inside the bank's own infrastructure and helps employees find answers from approved policies, circulars, SOPs, product documents, and uploaded internal files. It can also draft staff-ready responses, summarize documents, and assist customer-care, branch, operations, compliance, and product teams. It does not send bank data to external AI providers, and it does not make final business, lending, compliance, or regulatory decisions.

## Product Boundary

LipiCore is a decision-support and staff-productivity system. It is not an autonomous decision engine. Final decisions remain with authorized bank staff.

## What LipiCore Can Do Today

| Area | Current capability | Safe wording |
| --- | --- | --- |
| Approved knowledge Q&A | Answers from approved policies, circulars, SOPs, manuals, product documents, and uploaded files. | Source-backed answers from approved bank knowledge where matching sources exist. |
| Staff chat | General banking and customer-service assistance with source-backed answers when available. | Staff assistant for routine lookup, drafting, summarization, and internal guidance. |
| Document analysis | Upload supported files, summarize, ask questions, compare, and extract points. Heavy PDF/OCR/XLS review can be queued as a background long-document job. | Internal file analysis with citations where extracted text supports the answer; large files are processed asynchronously for staff review. |
| Drafting | Customer replies, internal memos, notices, scripts, FAQs, and escalation notes. | Staff-ready drafts for human review. |
| Bilingual usage | English and Nepali staff usage. | Bilingual support for staff workflows, subject to evaluation on the bank's documents. |
| Data control | Local deployment with private model runtime and self-hosted storage/vector database. | Bank data stays inside bank-controlled infrastructure. |
| Governance | Users, roles, audit logs, document approval lifecycle, and evaluation center. | Admin controls, source control, and auditability for AI use. |

## Controlled Future Capabilities

| Bank asks for | Safe response now | Required before stronger claim |
| --- | --- | --- |
| Lending decisions | LipiCore can support lending teams by summarizing loan files, checking required documents, extracting risk factors, and drafting credit memo notes. Final approval remains with authorized bank officers. | Loan file workspace, product checklists, policy citations, risk summary, missing-document detector, maker-checker workflow. |
| Compliance officer replacement | LipiCore reduces manual compliance lookup, circular summarization, and drafting work. Compliance officers remain responsible for review, interpretation, and approval. | Compliance workspace, circular impact review, policy gap notes, checklist generator, review queue, audit export. |
| Guaranteed regulatory correctness | LipiCore answers from approved bank knowledge and shows source citations. Regulatory correctness depends on the bank keeping approved documents current. | Effective dates, superseded documents, mandatory citation mode, citation verifier, compliance evaluation suite. |
| Scanned PDFs, tables, seals, signatures, handwriting | LipiCore supports OCR, table extraction, and queued long-document analysis. High-risk scanned or complex documents should be reviewed by staff, especially tables, stamps, handwritten notes, and signatures. | Full OCR benchmarks, layout-aware parsing, table extraction, confidence scores, low-confidence review queue, side-by-side source viewer. |
| Production HA/SLA | LipiCore can be deployed as pilot, department, or whole-bank architecture. SLA depends on the selected infrastructure tier and tested setup. | HA Postgres, Qdrant cluster, Redis HA, backend/frontend replicas, GPU model replicas, monitoring, failover and restore drills. |
| Better than GPT-4/GPT-5 | LipiCore is not positioned as a better general model. Its advantage is private deployment, bank-owned knowledge, source control, audit logs, and no external data exposure. | Side-by-side bank evaluation sets, citation accuracy metrics, latency tests, bilingual test sets, model benchmark records. |

## What Not To Claim

- It makes lending decisions.
- It replaces compliance officers.
- It guarantees regulatory correctness.
- It fully understands every scanned PDF, table, seal, signature, or handwritten note.
- It is production HA/SLA-ready for every bank without the required deployment architecture.
- It is generally better than GPT-4, GPT-5, Claude, Gemini, or other frontier public models.

## Approved Sales Language

- Secure internal AI for bank staff, powered by approved bank knowledge.
- Source-backed answers from approved documents.
- Airgapped or bank-controlled deployment.
- Staff-ready drafts for human review.
- Queued long-document analysis for large PDFs, Excel workbooks, and OCR-heavy files.
- Decision-support for customer care, branch, compliance, operations, and lending teams.
- Audit logs, role controls, document governance, and evaluation workflow.
- SLA and availability depend on deployment tier.

## Buyer Value

Banks are not buying "RAG." Banks are buying:

- Faster staff answers.
- Fewer wrong customer replies.
- Less dependency on senior staff for routine policy lookup.
- Better consistency across branches.
- Secure internal AI without data leaving the bank.
- Auditability and document-source control.

## Recommended First Use Case

Start with customer care and branch support:

- 20-50 staff users.
- 200-500 approved documents.
- Customer-care scripts, product FAQs, insurance docs, loan docs, circulars, SOPs.
- 30-day pilot.
- Measure answer accuracy, citation usefulness, response time, and escalation reduction.
