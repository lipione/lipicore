# LipiCore Proposal for Sanima Bank Limited

## Private Institutional Knowledge and Document Intelligence Platform

- **Prepared for:** Sanima Bank Limited
- **Prepared by:** Lipi One Pvt. Ltd.
- **Company website:** www.lipi.one
- **Infrastructure partner:** Silver Lining Pvt. Ltd.
- **Product:** LipiCore powered by LipiLLM
- **Proposal date:** June 5, 2026
- **Commercial model:** One-time implementation fee + monthly infrastructure fee + monthly software subscription

---

## 1. Executive Summary

Banks operate with a large and continuously growing body of institutional knowledge, including internal policies, circulars, SOPs, operational manuals, regulatory notices, compliance documents, and departmental procedures.

In most institutions, this knowledge is distributed across shared folders, email trails, departmental repositories, staff memory, and historical archives. Staff often spend significant time searching for the right document, confirming whether a circular is still valid, or depending on senior staff and subject matter experts for routine operational answers.

Lipi One Pvt. Ltd. proposes **LipiCore**, a private institutional knowledge and document intelligence platform designed for banking operations. LipiCore allows authorized bank staff to ask operational and policy-related questions in natural language and receive responses based on approved institutional documents. Answers are supported by source references so staff can verify responses against the original documents.

LipiCore is powered by **LipiLLM**, Lipi One's private Nepal-context AI model layer for Nepali/English banking language, local terminology, policy phrasing, and staff-assistance workflows. Sanima Bank documents are not used to train public AI models and are not used to fine-tune LipiLLM unless Sanima Bank separately approves that scope in writing.

This proposal separates LipiCore into two product options:

1. **LipiCore Policy Assistant:** a lighter policy retrieval and staff assistance package for approved-document Q&A, SOP/circular search, light summaries, and email/reply drafting.
2. **LipiCore Enterprise Intelligence:** the full platform with Policy Assistant plus analyst model capabilities, advanced OCR/document intelligence, compliance workspace, long-document analysis, model evaluation, and bank-readiness controls.

This structure allows Sanima Bank to adopt LipiCore at the right level: start with a lower-cost policy knowledge assistant, or deploy the full enterprise intelligence platform if deeper analysis and document automation are required from the beginning.

---

## 2. Current Banking Knowledge Challenges

Financial institutions commonly face the following operational challenges:

- Policies, SOPs, circulars, and manuals are scattered across multiple systems.
- Staff spend unnecessary time searching for internal documents.
- Historical policies and updated circulars are difficult to track together.
- Employees often depend on senior staff for routine clarification.
- Compliance and regulatory obligations continue to increase.
- Manual document review slows down operational response.
- Public AI tools cannot be used safely for sensitive institutional information.
- Internal knowledge is not always available in a structured, searchable, auditable format.
- Bank-wide AI use requires governance, access control, traceability, and clear human-review boundaries.

These challenges create delays, inconsistency, operational dependency, and increased compliance risk.

---

## 3. Proposed Solution

LipiCore provides a controlled internal knowledge layer for banking operations. Staff can ask natural-language questions such as:

- "What is the latest requirement for corporate account opening?"
- "Which documents are required for this customer category?"
- "Which internal policy governs this workflow?"
- "What does the latest circular say about this procedure?"
- "Is there an updated SOP for this department?"
- "Draft a response to a branch query using the approved policy."

LipiCore retrieves relevant content from approved documents and generates a structured, staff-reviewable response with source references. The system is designed to support faster information discovery, not to replace official policy interpretation, compliance approval, credit decisions, legal review, or management decision-making.

Sanima Bank users will access LipiCore through dedicated Windows and macOS desktop software connected to an approved managed hosted environment. The backend services, documents, database, vector index, queues, and model runtime remain inside the managed hosted environment operated by Lipi One and hosted through Silver Lining infrastructure.

---

## 4. Product Options

### 4.1 LipiCore Policy Assistant

**Purpose:** Fast policy retrieval and lightweight staff assistance.

LipiCore Policy Assistant is designed for banks that need a controlled internal knowledge assistant for policies, circulars, SOPs, manuals, staff FAQs, and light drafting tasks. It uses the policy retrieval / lightweight assistant route of LipiLLM and focuses on fast answers over approved institutional documents.

Best-fit workflows:

- Policy and SOP lookup.
- NRB circular search.
- Internal process guidance.
- Staff FAQ assistance.
- Light document summaries.
- Small email and reply drafting.
- Internal operational guidance based on approved documents.
- Source-backed answers for routine staff queries.

Policy Assistant is intentionally scoped as a lower-cost package. It does not include the analyst/deep model route or heavy document intelligence workflows unless separately upgraded.

### 4.2 LipiCore Enterprise Intelligence

**Purpose:** Full document intelligence and deeper AI-assisted analysis.

LipiCore Enterprise Intelligence includes all Policy Assistant features plus the analyst/deep model route and advanced document intelligence capabilities. It is designed for banks that need deeper analysis over large PDFs, scanned documents, Excel files, compliance circulars, multi-document questions, and audit/compliance support workflows.

Best-fit workflows:

- Large PDF and manual analysis.
- OCR-heavy document review.
- Excel workbook and detailed PDF review.
- Compliance circular impact summaries.
- Policy comparison and obligation notes.
- Long-document summarization and exception extraction.
- Model Lab route visibility and benchmark evidence.
- RAG Evaluation Center for bank-specific testing.
- Bank-readiness checks before pilots, model changes, prompt changes, ingestion changes, or production rollout claims.

Enterprise Intelligence is the recommended package if Sanima Bank expects heavy document workloads, compliance review workflows, Excel/PDF analysis, or wider production deployment with stronger evaluation evidence.

---

## 5. Feature Comparison

| Capability | LipiCore Policy Assistant | LipiCore Enterprise Intelligence |
|---|---|---|
| Windows and macOS desktop software | Included | Included |
| Managed hosted environment | Included | Included |
| LipiLLM Nepal-context model layer | Policy retrieval / lightweight assistant route | Policy route + analyst/deep model route |
| Approved-document Q&A | Included | Included |
| Policy, SOP, circular, and manual search | Included | Included |
| Source-backed answers | Included | Included |
| Basic source references | Included | Included |
| Advanced source passage viewer with clause/page metadata | Limited | Included |
| Light summaries | Included | Included |
| Small email/reply drafting | Included | Included |
| Document lifecycle states | Basic | Advanced |
| Role-based access control | Included | Included |
| Audit logs | Included | Included |
| Basic usage analytics | Included | Included |
| Basic document upload and indexing | Included | Included |
| Basic text extraction from supported files | Included | Included |
| OCR for scanned/image-heavy files | Not included by default | Included subject to capacity and document quality |
| Degraded Nepali PDF text-layer repair | Not included by default | Included where enabled |
| Capped Vision Review notes for image/PDF review | Not included | Included where enabled in agreed enterprise capacity |
| Queued long-document analysis | Not included | Included subject to package capacity |
| Detailed Excel/PDF analysis | Not included | Included subject to package capacity |
| Compliance Workspace | Not included | Included |
| Model Lab | Not included | Included |
| RAG Evaluation Center | Basic setup checks only | Included |
| Bank-readiness checks | Basic go-live checklist | Included |
| Internal staff chat bonus module | Included | Included |
| Advanced internal banking workspaces | Not included in Phase 1 Policy Assistant | Included where enabled by Super Admin after scope confirmation |
| Priority support | Package dependent | Package dependent |

---

## 6. Core Platform Capabilities

### 6.1 Centralized Knowledge Repository

LipiCore provides a structured repository for approved institutional documents, including:

- Internal policies.
- SOPs.
- Circulars.
- Operational manuals.
- Regulatory documents.
- NRB circulars and directives.
- Departmental procedures.
- Reference materials.
- Training documents.

Documents can be organized by department, document type, year, policy category, and access level.

### 6.2 Policy Intelligence

LipiCore enables intelligent retrieval from approved documents using:

- Natural-language search.
- Semantic retrieval.
- Keyword and hybrid search.
- Contextual answer generation.
- Source-backed responses.
- Document references and citations.
- Relevant section extraction.

This allows staff to search by meaning rather than relying only on exact keywords.

### 6.3 Source-Backed Answers

Every official answer should be grounded in uploaded and approved institutional documents where the workflow requires bank knowledge.

The system can provide:

- Relevant document title.
- Policy or circular reference.
- Extracted supporting content.
- Source link or file reference.
- Document date and version metadata where available.
- Clause, heading, PDF page, or printed-page metadata where configured and available.

This keeps responses verifiable and traceable.

### 6.4 Governance and Security

LipiCore is designed with institutional governance at the center:

- Role-based access control.
- User-level permissions.
- Department-based access.
- Controlled document visibility.
- Audit logging.
- User activity tracking.
- Query history.
- Document lifecycle management.
- Admin approval for document uploads.
- Source verification workflow.
- Bank-level data partitioning.
- Session-level document isolation.

### 6.5 Document Lifecycle Management

LipiCore supports document governance across the lifecycle:

- Upload.
- Classification.
- Metadata tagging.
- Approval.
- Versioning.
- Replacement.
- Superseded status.
- Archiving.
- Disabled state.
- Access control.
- Retrieval monitoring.

This is especially important in banking, where circulars and policy updates may change the applicability of older documents.

---

## 7. Handling Updated Policies and Circulars

Banking policy documents often evolve over time. A circular issued later may revise, override, clarify, or replace an earlier policy.

LipiCore can be configured to manage this through:

- Document version metadata.
- Effective dates.
- Circular-to-policy mapping.
- Superseded document tagging.
- Approved-document ranking.
- Archived document separation.
- Source date visibility in responses.
- Document freshness and review metadata where configured.

This allows the system to prioritize approved and current guidance while preserving older documents for reference and audit history.

---

## 8. Deployment Model

### 8.1 Infrastructure Layer

**Managed by Silver Lining Pvt. Ltd.**

The infrastructure layer includes:

- Hosting infrastructure.
- Compute resources.
- Storage resources.
- Monitoring.
- Backup support.
- Infrastructure maintenance.
- Network and server-level support.

### 8.2 Application Layer

**Managed by Lipi One Pvt. Ltd.**

The application layer includes:

- LipiCore knowledge platform.
- LipiLLM model layer configuration.
- Retrieval engine.
- Document indexing.
- User management.
- Admin dashboard.
- Governance controls.
- Repository management.
- Product updates.
- Technical support.
- Continuous platform enhancement.

### 8.3 Desktop Access Model

Sanima Bank users will access LipiCore through Windows and macOS desktop software rather than a general browser workflow. The desktop client connects only to approved LipiCore HTTPS origins and does not run the backend, database, vector database, object store, RAG pipeline, or model services locally.

Bank documents and AI data remain inside the managed hosted environment.

---

## 9. Phase 1 Implementation Scope

The proposed Phase 1 implementation includes:

- Project kickoff and requirements confirmation.
- Hosted environment provisioning.
- Bank tenant setup.
- Repository configuration.
- Initial document onboarding.
- User role configuration.
- Admin setup.
- Basic document structure setup.
- Security and access configuration.
- Policy retrieval setup.
- User training.
- UAT support.
- Go-live support.

Initial onboarding includes up to **10 GB of documents or 1,000 files**, whichever comes first. Additional migration, scanned archive processing, large historical archives, or manual cleanup can be quoted separately.

---

## 10. Pricing

All prices below are indicative in **NPR** and exclusive of VAT, withholding, applicable taxes, bank charges, and government duties. Final pricing will be confirmed after usage sizing, storage requirements, support level, server capacity, and selected product package are finalized.

### 10.1 LipiCore Policy Assistant Packages

| Package | User Band | One-Time Setup | Monthly Infrastructure | Monthly Software + Support | Total Monthly |
|---|---:|---:|---:|---:|---:|
| Policy Assistant Starter | 200-500 users | NPR 500,000 | NPR 75,000 | NPR 125,000 | NPR 200,000 |
| Policy Assistant Standard | 1,000-2,000 users | NPR 700,000 | NPR 175,000 | NPR 325,000 | NPR 500,000 |
| Policy Assistant Enterprise | 3,000-5,000 users | NPR 1,000,000 | NPR 325,000 | NPR 625,000 | NPR 950,000 |

### 10.2 LipiCore Enterprise Intelligence Packages

| Package | User Band | One-Time Setup | Monthly Infrastructure | Monthly Software + Support | Total Monthly |
|---|---:|---:|---:|---:|---:|
| Enterprise Intelligence Starter | 200-500 users | NPR 500,000 | NPR 175,000 | NPR 225,000 | NPR 400,000 |
| Enterprise Intelligence Standard | 1,000-2,000 users | NPR 800,000 | NPR 350,000 | NPR 450,000 | NPR 800,000 |
| Enterprise Intelligence Enterprise | 3,000-5,000 users | NPR 1,500,000 | NPR 750,000 | NPR 850,000 | NPR 1,600,000 |

### 10.3 Storage Pricing

| Storage Item | Commercial Treatment |
|---|---|
| Included storage | Confirmed during final package sizing based on document volume and retention requirement |
| Additional storage | NPR 10,000 per TB per month beyond the agreed included allocation |

### 10.4 Recommended Option

If Sanima Bank wants a lower-risk starting point, Lipi One recommends **LipiCore Policy Assistant Standard** for a 1,000-2,000 user internal knowledge rollout.

If Sanima Bank expects heavy PDF/OCR/Excel workloads, compliance review workflows, long-document analysis, or model evaluation requirements from the beginning, Lipi One recommends **LipiCore Enterprise Intelligence Standard**.

### 10.5 Effective Per-User Cost

| Package | User Band | Total Monthly | Effective Cost per User per Month |
|---|---:|---:|---:|
| Policy Assistant Starter | 200-500 users | NPR 200,000 | NPR 1,000 to NPR 400 |
| Policy Assistant Standard | 1,000-2,000 users | NPR 500,000 | NPR 500 to NPR 250 |
| Policy Assistant Enterprise | 3,000-5,000 users | NPR 950,000 | NPR 317 to NPR 190 |
| Enterprise Intelligence Starter | 200-500 users | NPR 400,000 | NPR 2,000 to NPR 800 |
| Enterprise Intelligence Standard | 1,000-2,000 users | NPR 800,000 | NPR 800 to NPR 400 |
| Enterprise Intelligence Enterprise | 3,000-5,000 users | NPR 1,600,000 | NPR 533 to NPR 320 |

### 10.6 Market Comparison and Tradeoffs

Public AI workspace pricing is useful as a market benchmark, but it is not a direct substitute for LipiCore. ChatGPT Business and Claude Team are general AI collaboration products. LipiCore is a managed banking knowledge and document intelligence platform with hosted infrastructure, desktop software access, approved-document retrieval, LipiLLM, citation controls, audit logs, bank-scoped document governance, internal chat, implementation, and support included.

Assumptions checked on **June 5, 2026**:

- OpenAI Help Center lists ChatGPT Business standard seats at **USD 25 per user per month** when billed monthly, and **USD 20 per user per month** when billed annually for most countries.
- OpenAI Help Center also notes a self-serve upper limit of 1,000 seats per purchase; larger institutions may need ChatGPT Enterprise discussion.
- Anthropic Help Center lists Claude Team Standard seats at **USD 25 per member per month** when billed monthly, and **USD 20 per member per month** when billed annually. Claude Team also states support up to 150 seats; larger institutions typically require Enterprise discussions.
- Nepal Rastra Bank listed the USD sell rate at **NPR 153.56 per USD** for June 5, 2026.

Indicative standard-seat cost at USD 25/user/month. The 2,000-user and 5,000-user figures are scale illustrations, not confirmation that the public self-serve product can be purchased at those seat counts without Enterprise procurement.

| User Count | USD Cost / Month | Approx. NPR / Month at NPR 153.56/USD |
|---:|---:|---:|
| 500 users | USD 12,500 | NPR 1,919,500 |
| 2,000 users | USD 50,000 | NPR 7,678,000 |
| 5,000 users | USD 125,000 | NPR 19,195,000 |

Indicative annual-billing equivalent at USD 20/user/month. The same bank-scale procurement caveat applies.

| User Count | USD Cost / Month Equivalent | Approx. NPR / Month Equivalent at NPR 153.56/USD |
|---:|---:|---:|
| 500 users | USD 10,000 | NPR 1,535,600 |
| 2,000 users | USD 40,000 | NPR 6,142,400 |
| 5,000 users | USD 100,000 | NPR 15,356,000 |

Key tradeoffs:

| Option | Strength | Tradeoff for a Bank |
|---|---|---|
| ChatGPT Business | Mature general AI workspace with admin controls and broad model access. | Self-serve seat purchase is not the same as a bank-scale Enterprise contract. API usage, custom banking RAG, local hosting, desktop deployment, bank-specific document lifecycle, source citation workflow, OCR pipeline, internal chat, implementation, and support are separate. |
| Claude Team | Strong general assistant experience and long-context workflows for supported team sizes. | Team plan is published up to 150 seats; larger bank deployment requires Enterprise discussion. Custom banking RAG, local hosting, desktop deployment, audit workflow, OCR/document intelligence, and support still need separate implementation. |
| DIY API build | Direct access to frontier model APIs and full engineering flexibility. | The bank or vendor must still build ingestion, vector search, citations, RBAC, audit logs, document governance, desktop software, hosting, support, evaluation, and operational monitoring. Token usage can vary heavily with large documents. |
| LipiCore Policy Assistant | Lower-cost controlled policy retrieval, staff Q&A, light summaries, email drafting, audit logs, document governance, hosted infrastructure, and desktop software. | Does not include the analyst/deep model, heavy OCR, long-document analysis, or compliance intelligence workflows. |
| LipiCore Enterprise Intelligence | Full platform with Policy Assistant plus analyst/deep model, OCR/document intelligence, compliance workspace, Model Lab, RAG Evaluation Center, readiness checks, and stronger large-document workflows. | Higher monthly cost than Policy Assistant because it includes deeper model capacity, advanced workflow modules, and broader support scope. |

Sources: OpenAI ChatGPT Business Help Center, Anthropic Claude Team Help Center, and Nepal Rastra Bank foreign exchange rate page checked on June 5, 2026.

---

## 11. Commercial Inclusions

### 11.1 One-Time Setup Includes

- Environment setup.
- Platform configuration.
- Repository structuring.
- Initial document onboarding.
- User role configuration.
- Admin setup.
- Security and access configuration.
- Training.
- User acceptance testing support.
- Production deployment support.

For Enterprise Intelligence packages, setup also includes:

- Analyst/deep model route configuration.
- OCR workflow configuration.
- Long-document analysis configuration.
- Compliance Workspace configuration.
- Model Lab and RAG Evaluation Center configuration.
- Representative large-file, OCR, Excel/PDF, and compliance workflow testing.

### 11.2 Monthly Infrastructure Includes

- Managed server compute through Silver Lining.
- Storage allocation.
- Database, vector database, and object storage hosting.
- Backup storage.
- Monitoring and operational maintenance.
- Network, TLS, and hosting operations.
- AI runtime capacity according to selected package.

### 11.3 Monthly Software + Support Includes

- LipiCore software license.
- LipiLLM model layer access under selected package.
- Windows and macOS desktop software access.
- Product updates.
- Security patches.
- Support and maintenance.
- Role-based access control.
- Audit logging.
- Document repository and retrieval features.
- Internal staff chat bonus module.

---

## 12. Internal Chat Bonus Module

Lipi One will include the internal chat system as a bonus module with the selected LipiCore hosted package.

The internal chat system is separate from the AI document chat. It is intended for staff-to-staff communication inside the LipiCore environment, so teams can coordinate around document analysis, compliance queries, operational follow-ups, and internal decisions without leaving the secured platform.

Included features:

- Direct staff conversations.
- Department channels.
- Custom group conversations.
- Announcement channels.
- Secure file and image sharing subject to retention and attachment policy.
- Unread counters and read status.
- Bank-scoped user directory.
- Local keyword search over permitted conversation history.
- Administrative user control.
- Activity records suitable for administrative review.

Messenger boundary: chat messages and shared files are not embedded into the document intelligence index, not used as AI context, and not used to train public AI models unless a future written scope explicitly changes that boundary.

---

## 13. Phase 1 Exclusions

The following items are excluded unless separately agreed:

- Core banking system integration.
- DMS, SharePoint, email, or intranet integration.
- Large-scale physical file scanning.
- Bulk OCR of historical archives.
- Custom AI model fine-tuning.
- Fine-tuning LipiLLM on Sanima Bank data unless separately scoped, approved, and contracted.
- Automated regulatory monitoring.
- Custom report generation.
- Department-specific AI agents.
- API integrations with third-party systems.
- Automatic credit, risk, legal, regulatory, or customer decisions without authorized bank review.
- Perfect OCR, handwriting, seal, signature, or complex-table verification.
- Legal, regulatory, audit, ISO, SOC, PCI, or NRB certification.
- Bank-side network, device, endpoint, or user adoption management.

---

## 14. Implementation Timeline

The estimated implementation duration is **4 to 6 weeks** from purchase order and receipt of required Sanima Bank inputs.

| Week | Activity | Output |
|---:|---|---|
| Week 1 | Project kickoff and planning | Confirmed scope, stakeholders, document categories, access roles, deployment plan |
| Week 2 | Environment setup | Infrastructure provisioned, application configured, admin setup, security access ready |
| Week 3 | Document onboarding | Initial documents uploaded, repository structured, metadata applied, retrieval tested |
| Week 4 | Training and UAT | Admin training, user training, UAT sessions, feedback collection |
| Week 5 | Production deployment | Final configuration, go-live support, monitoring, post-deployment review |
| Week 6 if required | Refinement and additional UAT | Remaining UAT items resolved or formally deferred |

Timeline depends on document volume, bank-side approvals, UAT response time, package selection, and additional workflow scope.

---

## 15. Security and Data Governance

LipiCore is designed with enterprise security principles including:

- Controlled access management.
- Role-based permissions.
- Department-based access controls.
- Audit logging.
- User activity tracking.
- Query history.
- Document lifecycle management.
- Bank-level data isolation.
- Secure hosted infrastructure environment.
- Institutional data governance controls.
- Desktop access through approved LipiCore origins.

Data-use commitments:

- Sanima Bank documents remain within the approved managed hosted environment.
- Sanima Bank documents are not used to train public AI models.
- Sanima Bank documents are not used to train or fine-tune LipiLLM unless separately approved by Sanima Bank in writing.
- Sanima Bank data is not shared with other banks or third parties except where explicitly approved by the bank.
- On termination, bank data can be exported and removed according to the agreed retention and exit process.

---

## 16. Acceptance Criteria

The implementation will be considered accepted when:

- Sanima Bank can securely log in to the hosted environment.
- Admin users can create and manage bank users.
- Users can upload supported documents.
- Uploaded documents can be processed and queried.
- Staff can ask approved-document questions and receive source-backed answers.
- Role-based permissions work according to agreed configuration.
- Audit logs capture key user and system activity.
- Windows and macOS desktop access packages connect only to approved LipiCore hosted origins.
- Internal chat supports direct messages, group/channel conversations, and administrative user control.
- Training has been completed.
- UAT issues classified as go-live blockers have been resolved or formally deferred.

For Enterprise Intelligence packages, acceptance also includes:

- Representative long-document analysis jobs complete on agreed sample files.
- OCR extraction can extract text from agreed sample files without indexing them into approved knowledge.
- Compliance Workspace can create a circular review and save an impact summary marked for officer review.
- Model Lab and RAG Evaluation Center are accessible to authorized roles.
- Bank-readiness checklist items are reviewed before production go-live.

---

## 17. Bank Responsibilities

Sanima Bank will provide:

- Project owner and decision maker.
- Technical/security contact.
- Initial user list and role matrix.
- Sample and initial production documents.
- Document categories and repository structure input.
- UAT participants.
- Timely review of configuration and UAT findings.
- Internal approvals for staff access and production use.
- Required compliance review and procurement approvals.
- Bank-owned domain/subdomain or access preference, if required.

For Enterprise Intelligence packages, Sanima Bank will also provide:

- OCR samples.
- Compliance circular samples.
- Representative large PDF and Excel samples.
- Evaluation questions and expected source examples.
- Workflow owners for OCR, Compliance Workspace, Model Lab, and RAG Evaluation.

---

## 18. Payment Terms

- One-time setup fee: 50% upon purchase order and 50% before production go-live.
- Monthly infrastructure charge: billed monthly in advance.
- Monthly software subscription: billed monthly in advance.
- Minimum contract term: 12 months.
- Taxes: VAT and applicable taxes charged separately.
- Price validity: 30 days from proposal date.
- Annual prepayment discounts can be discussed for bank procurement preference.

---

## 19. Upgrade Path

Sanima Bank may begin with LipiCore Policy Assistant and later upgrade to LipiCore Enterprise Intelligence.

Upgrade modules may include:

- Analyst/deep model route.
- OCR and document intelligence.
- Long-document analysis.
- Compliance Intelligence Workspace.
- Model Lab.
- RAG Evaluation Center.
- Bank-readiness checks.
- Capped Vision Review notes where enabled in the agreed enterprise capacity.
- Detailed Excel/PDF analysis.
- Advanced source passage and citation-verification metadata.
- Department-specific workflow helpers.

Commercial models for future modules may be discussed separately based on business requirements, scope, data volume, and deployment model.

---

## 20. Why Lipi One

Lipi One is building AI products focused on institutional knowledge, language intelligence, and enterprise-grade retrieval systems.

For LipiCore, Lipi One brings:

- Banking-focused knowledge platform development.
- Secure institutional architecture.
- Nepal-context LipiLLM model layer.
- Local implementation capability.
- Local technical support.
- Product enhancement roadmap.
- Governance and audit-first design.
- Partnership with Silver Lining for infrastructure delivery.

Together, Lipi One and Silver Lining provide a combined application and infrastructure delivery model suitable for enterprise banking deployment.

---

## 21. Expected Benefits for Sanima Bank

LipiCore can help Sanima Bank achieve:

- Faster internal information retrieval.
- Reduced dependency on manual document search.
- Improved staff productivity.
- Better access to policy and SOP knowledge.
- Stronger document governance.
- Improved auditability.
- Better institutional knowledge preservation.
- Controlled foundation for enterprise AI adoption.
- Clear upgrade path from policy retrieval to full document intelligence.

---

## 22. Next Steps

1. Sanima Bank reviews the proposal.
2. Sanima Bank selects preferred product package.
3. Lipi One, Silver Lining, and Sanima Bank confirm user count, capacity, and document scope.
4. Commercial terms and final scope are confirmed.
5. Purchase order or agreement is issued.
6. Project kickoff is scheduled.
7. Hosted environment is provisioned.
8. UAT and training are completed.
9. Production go-live begins.

Lipi One looks forward to partnering with Sanima Bank Limited to build a secure, efficient, and future-ready institutional knowledge and document intelligence platform for banking operations.
