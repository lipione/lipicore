# LipiCore Bank Pilot Scope Template

**Prepared:** May 21, 2026  
**Pilot name:** Bank Staff AI Helpdesk  
**Recommended duration:** 30 days

## Pilot Objective

Validate LipiCore as a secure internal AI assistant for bank staff. The pilot should prove whether staff can find approved policy/product/SOP answers faster, draft better customer-care responses, and reduce routine escalations while keeping all bank data inside bank-controlled infrastructure.

## Pilot Scope

| Area | Recommended scope |
| --- | --- |
| Users | 20-50 named staff users |
| Departments | Customer care, branch support, operations, compliance/helpdesk, product/policy |
| Documents | 200-500 approved documents |
| Document types | Customer-care scripts, product FAQs, loan docs, deposit docs, insurance docs, SOPs, circulars, escalation manuals |
| Large-file sample | 5-10 representative large PDFs, scanned PDFs, and Excel workbooks for queued analysis testing |
| Duration | 30 calendar days after document approval and user onboarding |
| Deployment | Pilot server or controlled bank environment; not a whole-bank HA claim |
| Languages | English and Nepali staff usage, evaluated on pilot questions |

## Pilot Modes

### 1. Ask BankAi

General staff chat. Uses approved bank knowledge when available, cites sources, and otherwise gives clearly marked general guidance.

### 2. Ask Approved Knowledge

Strict source-backed answers only from approved bank documents. If no approved source supports the answer, LipiCore should refuse and guide staff to a supervisor or policy owner.

### 3. Analyze Internal File

Staff upload a document and ask questions, summarize, extract key points, compare, or draft responses. Outputs are for staff review.

### 4. Queue Long-Document Analysis

Staff queue large PDFs, OCR-heavy files, or detailed Excel workbooks for background analysis. Results are stored for later review and should cite page, section, sheet, or cell labels where extraction supports them.

## Demo Flow

Use this sequence for bank demos:

1. **Ask BankAi:** Ask a customer-care or branch support question. Show source cards when approved knowledge matches, and show clearly marked general guidance when no source matches.
2. **Ask Approved Knowledge:** Ask a policy/compliance question. Open the source evidence panel and show the exact document passage. Then ask an unsupported question and show source-backed refusal.
3. **Analyze Internal File:** Upload a policy, circular, FAQ, or case note. Show ingestion progress, ask for summary or draft response, and review the cited source evidence.
4. **Queue Long-Document Analysis:** Open a ready large file in Document Library, queue a detailed analysis prompt, show job status, and open the completed result.

## Success Metrics

| Metric | Target evidence |
| --- | --- |
| Answer accuracy | Pass rate on bank-approved evaluation questions |
| Citation usefulness | Staff can open source passages and verify key claims |
| Response time | Measured p50/p95 response time for pilot server |
| Long-document turnaround | Measured job duration and success rate for large PDF/OCR/XLS samples |
| Escalation reduction | Fewer routine policy/product questions escalated to senior staff |
| Staff acceptance | Staff mark answers useful or edit drafts less frequently |
| Safety | Unsupported policy questions produce source-backed refusal |
| Governance | Audit logs capture questions, sources, output type, and staff actions |

## Bank Inputs Required

- Pilot owner and technical contact.
- Staff user list with departments and roles.
- Approved document bundle.
- Document freshness owner for policy/circular updates.
- 50-100 real staff questions for evaluation.
- UAT participants and review schedule.
- Network, server, access, and security requirements.

## LipiCore Deliverables

- Pilot deployment.
- User/role setup.
- Document ingestion and approval workflow.
- Staff onboarding session.
- Admin orientation.
- Evaluation Center setup with pilot questions.
- Weekly pilot review.
- End-of-pilot report with usage, accuracy, citation, latency, and escalation findings.

## Out Of Scope Unless Contracted

- Autonomous lending decisions.
- Replacement of compliance officers.
- Final regulatory interpretation or guarantee.
- Core banking transaction execution.
- Production HA/SLA deployment.
- Perfect OCR for every scanned, handwritten, stamped, signed, or complex-layout document.
- Unlimited large-file analysis without queue limits, worker sizing, and model-capacity evidence.
- Integration with CBS, CRM, LOS, AML, or ticketing systems.

## Pilot Exit Decision

At the end of the pilot, decide one of three paths:

- Continue customer care and branch rollout.
- Expand to compliance and lending decision-support workflows.
- Pause until document quality, governance, model quality, or infrastructure requirements are addressed.
