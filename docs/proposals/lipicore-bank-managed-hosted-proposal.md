# Proposal for Managed Hosted LipiCore Enterprise Document Intelligence Platform

- **Prepared for:** Sanima Bank
- **Prepared by:** Lipi One Pvt. Ltd.
- **Hosting and server:** Silver Lining
- **Product:** LipiCore Enterprise Document Intelligence Platform
- **Proposal date:** May 23, 2026
- **Validity:** 30 days from proposal date
- **Commercial model:** One-time setup fee + monthly managed server charge + monthly software subscription

---

## 1. Executive Summary

LipiCore Enterprise Document Intelligence Platform is a secure, enterprise-grade AI platform designed for banks and financial institutions that need private document analysis, policy search, regulatory review, and staff-facing AI assistance without sending confidential banking data to public AI services.

The proposed model is a managed hosted package operated for Sanima Bank on Silver Lining server infrastructure, with Lipi One Pvt. Ltd. providing the LipiCore software, desktop client packaging, implementation, and support. Sanima Bank receives Windows and macOS desktop software connected to the approved hosted environment, role-based access, secure document upload, AI-powered analysis, source citations, audit logging, the internal chat module as a bonus, and ongoing managed support. Pricing is separated into:

1. A one-time setup and onboarding charge.
2. A monthly managed server and infrastructure charge.
3. A monthly software license, support, and maintenance charge.

This model gives Sanima Bank the operational convenience of a hosted system while preserving banking-grade controls around data isolation, access management, auditability, controlled desktop access, and private model execution.

---

## 2. Understanding of Sanima Bank's Requirement

Sanima Bank has requested a complete proposal covering solution capability, scope of work, pricing, implementation, support, and commercial terms.

The expected system should help bank staff:

- Search and analyze internal banking documents securely.
- Ask natural language questions over uploaded documents and approved knowledge bases.
- Queue large PDF, OCR-heavy, and Excel workbook analysis without blocking normal staff chat.
- Receive answers with source references and document attribution.
- Maintain audit logs for user activity, queries, uploads, and AI responses.
- Enforce access controls for administrators, bank admins, and staff users.
- Support confidential deployment where bank documents remain within controlled hosted infrastructure.
- Provide Windows and macOS desktop software instead of a general webapp workflow.
- Include the internal chat system as a bonus module for bank-scoped staff communication.
- Apply additional storage pricing transparently at **NPR 10,000 per TB per month** where required.
- Reduce time spent reviewing policies, loan documents, compliance circulars, reports, and operational manuals.

---

## 3. Proposed Solution

We propose deploying LipiCore Enterprise Document Intelligence Platform as a managed hosted service on Silver Lining server infrastructure.

Sanima Bank will access the platform through LipiCore Desktop software for Windows and macOS, connected only to the approved hosted LipiCore environment. Lipi One Pvt. Ltd. and Silver Lining will host, operate, monitor, maintain, and update the platform. Sanima Bank will not need to procure or maintain AI servers, GPUs, databases, vector databases, or model runtime infrastructure.

AI output is positioned as staff assistance and does not replace authorized Sanima Bank review for regulatory, credit, legal, customer-facing, or final decision use.

### Core Capabilities

- Secure document upload and analysis.
- Queued long-document analysis for large PDFs, OCR-heavy files, and detailed Excel/PDF review.
- Windows and macOS desktop software access.
- AI chat over bank documents.
- Approved knowledge Q&A with source evidence.
- Document lifecycle controls for draft, approved, superseded, archived, and disabled documents.
- Hybrid retrieval with vector search, keyword search, reranking, and citation verification.
- RAG evaluation tools for testing answer quality on agreed document sets.
- Session-bound document isolation.
- Bank-level data partitioning.
- Source citations for generated answers.
- Audit logs for compliance and internal review.
- Role-based access control.
- User and admin management.
- Dashboard, document library, analytics, and activity views.
- Private model execution on LipiCore-hosted infrastructure.
- English and Nepali document support where document quality permits.
- Configurable AI model modes, sized to the selected hosted capacity profile.

---

## 4. Deployment Model

### Managed Hosted Architecture

The platform will be hosted on LipiCore-managed servers and accessed by the bank through LipiCore Desktop software over HTTPS.

The hosted stack includes:

- LipiCore Desktop client interface.
- FastAPI backend.
- PostgreSQL database.
- Qdrant vector database.
- MinIO object storage.
- Redis queue and admission control.
- vLLM/private LLM runtime.
- Nginx reverse proxy with TLS.
- Monitoring, backup, and operational tooling.

### Desktop Software Access Model

Sanima Bank users will access LipiCore through a Windows and macOS desktop client rather than a general-purpose browser workflow. The desktop client connects only to approved LipiCore HTTPS origins and does not run the backend, database, vector database, object store, RAG pipeline, or model services locally.

This improves operational control by giving the bank a dedicated approved application surface, app-level lock behavior, controlled navigation, and reduced exposure to general browser tabs, extensions, and accidental navigation outside the approved LipiCore environment. Bank documents and AI data remain inside the managed hosted environment.

### Data Isolation

Each bank environment is logically isolated using bank-level partitioning across application data, database records, and vector search metadata. Documents uploaded within one bank environment are not visible to another bank environment.

Where the selected package requires it, the bank can be assigned dedicated server resources instead of shared managed infrastructure.

---

## 5. Scope of Work

### Phase 1: Project Initiation and Requirements

LipiCore will:

- Conduct a kickoff meeting with the bank's project team.
- Confirm users, departments, document categories, expected usage, and access roles.
- Confirm deployment URL, branding, access restrictions, and support contacts.
- Define user acceptance testing criteria.
- Finalize the implementation schedule.

Bank will:

- Nominate a project owner and technical coordinator.
- Provide initial user list and role mapping.
- Provide sample documents for testing.
- Confirm internal approval and UAT participants.

### Phase 2: Hosted Environment Setup

LipiCore will:

- Provision the managed server environment.
- Configure secure application access over HTTPS.
- Configure backend services, database, object storage, vector search, and model runtime.
- Configure bank tenant, admin accounts, roles, and access controls.
- Configure backup, monitoring, logs, and operational alerts.

### Phase 3: Application Configuration

LipiCore will:

- Configure bank-specific branding where applicable.
- Configure document categories and initial knowledge library structure.
- Configure role permissions for administrators, bank admins, and staff users.
- Configure AI model routing for fast and deep responses.
- Configure audit logging and administrative views.

### Phase 4: Initial Data Onboarding

LipiCore will:

- Upload and index initial documents provided by the bank.
- Validate document parsing, chunking, and retrieval quality.
- Validate queued long-document analysis on representative large PDFs, scanned files, and Excel workbooks.
- Verify source citation behavior.
- Tune retrieval settings where needed for the bank's document types.

Initial onboarding includes up to **10 GB** of documents or **1,000 files**, whichever comes first. Additional migration or large-scale document digitization can be quoted separately.

### Phase 5: Training and UAT

LipiCore will:

- Conduct administrator training.
- Conduct staff user training.
- Support bank UAT sessions.
- Resolve agreed UAT issues before production go-live.
- Provide user guidance material and administrator handover notes.

### Phase 6: Go-Live and Support

LipiCore will:

- Move the bank environment to production use.
- Monitor initial go-live activity.
- Provide post-go-live support.
- Provide monthly health checks and support reporting where required.

---

## 6. Functional Scope

### Included Modules

| Module | Included Scope |
|---|---|
| Secure Login | User authentication, session handling, password security, JWT-based access |
| Desktop Software Access | Windows and macOS LipiCore Desktop client connected to approved LipiCore hosted origins |
| User Management | Admin, bank admin, and staff user roles |
| Document Library | Upload, organize, process, lifecycle-manage, and search bank documents |
| Queued Long-Document Analysis | Background analysis for large PDFs, scanned/OCR-heavy files, and detailed Excel workbooks |
| Approved Knowledge Q&A | Ask questions over uploaded and approved documents with source references where available |
| Internal Chat System (Bonus) | Bank-scoped staff messenger module included as a bonus module and kept separate from AI/RAG context |
| Session Uploads | Upload temporary documents into a chat session for isolated analysis |
| Source Evidence | Assistant answers include source document references and passage evidence where available |
| RAG Evaluation | Evaluation center for testing retrieval and answer quality on agreed question sets |
| Audit Logs | Activity records for uploads, queries, users, and assistant responses |
| Analytics Dashboard | Usage, document, and activity-level reporting |
| Compliance Workflow Support | Policy comparison, document review, risk analysis support |
| Model Modes | Fast response mode and deeper analysis mode, subject to package capacity |
| Admin Settings | Tenant configuration, roles, system preferences, and security views |

### Supported File Types

- PDF
- DOCX
- XLSX/XLS
- PPTX
- TXT
- CSV
- Image-based documents where OCR is enabled and document quality permits

### Typical Use Cases

- Credit and loan policy review.
- Compliance circular search.
- Internal SOP and manual lookup.
- Loan agreement review.
- Financial report analysis.
- Multi-document comparison.
- Queued large-file summarization and exception extraction.
- Staff query assistance.
- Audit support and investigation.
- Regulatory policy interpretation support.

---

## 7. Security and Compliance Controls

The platform is designed for confidential banking workflows.

### Security Controls

- HTTPS/TLS encrypted access.
- Windows and macOS desktop client access instead of general browser-based usage.
- Approved LipiCore origin restrictions inside the desktop client.
- Desktop app lock behavior with local session clearing.
- Bank-level data isolation.
- Session-level document isolation.
- Role-based access control.
- Password hashing using bcrypt.
- JWT-based authenticated API access.
- Prompt guardrails for document-grounded responses.
- Source verification and retrieval evaluation controls for reducing unsupported answers.
- Document lifecycle states to control approved, superseded, archived, and disabled content.
- PII masking controls for sensitive information.
- Audit logging for major system activity.
- Internal messenger data is kept separate from AI document chat and is not embedded into the RAG index by default.
- Restricted operational access to hosted infrastructure.
- Database, object storage, and vector store access controlled through backend services.

### Data Use Commitment

- Bank documents remain within the LipiCore managed environment.
- Bank documents are not used to train public AI models.
- Bank data is not shared with other banks or third parties except where explicitly approved by the bank.
- On termination, bank data can be exported and removed according to the agreed retention and exit process.

### Compliance Note

LipiCore provides controls that support banking governance, auditability, and internal compliance. Final regulatory approval, internal policy approval, and third-party certification requirements remain the responsibility of the bank unless separately contracted.

---

## 8. Implementation Timeline

The standard implementation timeline is **4 to 6 weeks** from purchase order and receipt of required bank inputs.

| Phase | Duration | Output |
|---|---:|---|
| Kickoff and requirements | 3-5 business days | Confirmed scope, project plan, roles, access requirements |
| Environment provisioning | 5-7 business days | Hosted bank environment ready |
| Configuration and initial documents | 5-10 business days | Tenant configured, initial documents indexed |
| Training and UAT | 5-10 business days | Bank users trained, UAT completed |
| Go-live | 2-3 business days | Production access and go-live support |

Timeline depends on document volume, bank-side approvals, integration needs, and UAT response time.

---

## 9. Deliverables

LipiCore will deliver:

- Hosted production environment for the bank.
- Windows and macOS LipiCore Desktop access package.
- Configured bank tenant and administrator accounts.
- Role-based user access structure.
- Document library and chat assistant modules.
- Internal chat system bonus module.
- Initial document ingestion as defined in scope.
- Audit logging and analytics views.
- Administrator and staff training.
- User handover material.
- Production go-live support.
- Monthly support and maintenance under the selected subscription plan.

---

## 10. Pricing

Pricing is separated into setup, server/infrastructure, and software subscription charges as requested.

All prices below are indicative in **NPR and exclusive of applicable VAT, taxes, withholding, bank charges, and government duties**. Final pricing will be confirmed after usage sizing, storage requirements, support level, and server capacity are finalized.

### Recommended Hosted Packages

| Package | One-Time Setup | Monthly Server / Infrastructure | Monthly Software License + Support | Total Monthly |
|---|---:|---:|---:|---:|
| Starter | NPR 500,000 | NPR 175,000 | NPR 225,000 | NPR 400,000 |
| Standard | NPR 800,000 | NPR 350,000 | NPR 450,000 | NPR 800,000 |
| Enterprise | NPR 1,500,000 | NPR 750,000 | NPR 850,000 | NPR 1,600,000 |

### Package Sizing

| Package | Recommended For | Included Capacity |
|---|---|---|
| Starter | Department or focused bank rollout | 200-500 users, standard managed capacity, business-hours support |
| Standard | Bank-wide production use | 1,000-2,000 users, stronger managed capacity, priority queue during business hours |
| Enterprise | High-volume institution-wide deployment | 3,000-5,000 users, dedicated managed capacity, priority support and escalation |

### Storage Pricing

| Storage Item | Commercial Treatment |
|---|---|
| Included storage | Confirmed during final package sizing based on document volume and retention requirement |
| Additional storage | NPR 10,000 per TB per month beyond the agreed included allocation |

### Market Comparison and Tradeoffs

Public ChatGPT and Claude prices are useful benchmarks, but they are not direct substitutes for LipiCore. ChatGPT Business and Claude Team are general-purpose AI workspaces. LipiCore is a managed banking document intelligence platform with hosted infrastructure, document ingestion, retrieval, source citations, role-based access, audit records, internal staff chat, and support included in one package.

#### LipiCore Effective Per-User Cost

| Package | User Band | Total Monthly | Effective Cost / User / Month |
|---|---:|---:|---:|
| Starter | 200-500 users | NPR 400,000 | NPR 2,000 to NPR 800 |
| Standard | 1,000-2,000 users | NPR 800,000 | NPR 800 to NPR 400 |
| Enterprise | 3,000-5,000 users | NPR 1,600,000 | NPR 533 to NPR 320 |

#### Public AI Workspace Benchmark

Assuming approximately NPR 154 per USD:

| User Count | ChatGPT / Claude at USD 25/User/Month | Approx. NPR / Month |
|---:|---:|---:|
| 500 users | USD 12,500/month | Approx. NPR 19.2 lakh/month |
| 2,000 users | USD 50,000/month | Approx. NPR 76.8 lakh/month |
| 5,000 users | USD 125,000/month | Approx. NPR 1.92 crore/month |

#### Practical Tradeoffs

| Option | Indicative Public Cost | What It Includes | Bank Tradeoff |
|---|---|---|---|
| LipiCore Standard | NPR 800,000/month for 1,000-2,000 users | Hosted banking document platform, RAG, audit logs, RBAC, internal chat, support, and managed infrastructure | Purpose-built for bank document intelligence; model choice and capacity are managed by Lipi One/Silver Lining |
| ChatGPT Business | USD 25/user/month monthly or USD 20/user/month annual equivalent | General ChatGPT workspace with admin controls and business privacy terms | Seat cost scales linearly; API usage, custom RAG, bank document platform, hosting, and custom audit workflows are separate |
| Claude Team | USD 25/user/month monthly or USD 20/user/month annual equivalent for standard seats; Team is listed for 5-150 users | General Claude team workspace with connectors and administration features | Larger banks need Enterprise; enterprise use may combine seat price and API usage. Banking-specific platform still needs to be built |
| DIY API Build | Token usage varies by model and workload; GPT-5.4/Sonnet-class models can become material at high document volume | Access to frontier model APIs | Bank must still build and operate document ingestion, vector search, citations, RBAC, audit logs, security review, support, and hosting |

Market pricing references: OpenAI ChatGPT Business public pricing, OpenAI API pricing, Anthropic Claude pricing, and public USD/NPR exchange-rate sources as of May 2026.

### What the One-Time Setup Fee Covers

- Project kickoff and requirements confirmation.
- Hosted environment provisioning.
- Bank tenant setup.
- Security and access configuration.
- Initial admin/user role configuration.
- Initial document onboarding up to 10 GB or 1,000 files.
- Representative queued long-document testing for selected large PDFs, scanned PDFs, and Excel workbooks.
- UAT support.
- One administrator training session.
- One staff training session.
- Go-live support.

### What the Monthly Server / Infrastructure Charge Covers

- Managed server compute.
- AI model runtime capacity.
- Storage allocation.
- Additional storage expansion at NPR 10,000 per TB per month where required.
- Database and vector database hosting.
- Object storage.
- Backup storage.
- Monitoring and operational maintenance.
- Network, TLS, and hosting operations.

### What the Monthly Software License + Support Charge Covers

- LipiCore Enterprise Document Intelligence Platform software license.
- Windows and macOS LipiCore Desktop software access.
- AI document analysis modules.
- Queued long-document analysis module for large PDF/OCR/XLS work, subject to package capacity.
- RAG retrieval, source citation, and audit logging features.
- User management and RBAC.
- Product maintenance updates.
- Security patches.
- Helpdesk and technical support under the selected support plan.

### Internal Chat System Bonus Module

Lipi One Pvt. Ltd. will include the internal chat system as a bonus module with the hosted LipiCore package for Sanima Bank.

The internal chat system is separate from the AI document chat. It is intended for staff-to-staff communication inside the LipiCore environment, so teams can coordinate around document review, compliance queries, operational follow-ups, and internal decisions without leaving the secured platform.

Messenger boundary: chat messages and shared files are not embedded into the document intelligence index, not used as AI context, and not used to train public AI models unless a future written scope explicitly changes that boundary.

Included internal chat features:

- Direct staff-to-staff conversations.
- Department channels and custom group conversations.
- Announcement channels.
- Secure file and image sharing, subject to retention and attachment policy.
- Unread counters, delivery status, and read status.
- Bank-scoped user directory using the same LipiCore user base.
- Role-aware access aligned with configured bank users and permissions.
- Local keyword search over permitted message history for internal follow-up.
- Conversation context alongside document intelligence workflows.
- Administrative user control through the existing user management module.
- Activity records suitable for administrative review and governance.
- Hosted storage and backup under the same managed environment.

Commercial treatment: the internal chat system is included as a bonus module at no additional software license charge within the selected LipiCore hosted package.

---

## 11. Payment Terms

Recommended payment structure:

- **One-time setup fee:** 50% upon purchase order, 50% before production go-live.
- **Monthly server/infrastructure charge:** Billed monthly in advance.
- **Monthly software subscription:** Billed monthly in advance.
- **Minimum contract term:** 12 months.
- **Taxes:** VAT and applicable taxes charged separately.
- **Price validity:** 30 days from proposal date.

Annual prepayment discounts can be discussed for banks that prefer yearly procurement.

---

## 12. Support and SLA

| Support Level | Applies To | Coverage |
|---|---|---|
| Standard Support | Starter | Email and remote support, business-hours support window, 4 business-hour critical acknowledgement, monthly health check, security and software patches |
| Priority Queue | Standard | Business-hours support with priority queue over Starter, critical acknowledgement target agreed in final support schedule, monthly health check, security and software patches |
| Priority Support | Enterprise or upgrade | Priority remote support, extended support window, 1-hour critical acknowledgement target where commercially agreed, dedicated escalation contact, quarterly service review |

### Availability Target

| Package | Availability Target |
|---|---:|
| Starter | Pilot availability target defined after infrastructure review |
| Standard | Department availability target defined after infrastructure review |
| Enterprise | HA/SLA target available only with agreed whole-bank HA architecture |

Formal SLA commitments depend on final infrastructure, monitoring, backup and restore procedure, failover design, support terms, and successful operational drills. Availability excludes planned maintenance, bank network issues, force majeure, third-party internet disruption, and bank-side access problems.

---

## 13. Acceptance Criteria

The implementation will be considered accepted when:

- Sanima Bank can securely log in to the hosted environment.
- Admin users can create and manage bank users.
- Users can upload supported documents.
- Uploaded documents can be processed and queried.
- AI responses show source references where source documents are available.
- Role-based permissions work according to agreed configuration.
- Audit logs capture key user and system activity.
- Representative queued long-document analysis jobs complete successfully on agreed sample files.
- Windows and macOS desktop access packages connect only to approved LipiCore hosted origins.
- Internal chat module supports direct messages, group/channel conversations, and administrative user control.
- Training has been completed.
- UAT issues classified as go-live blockers have been resolved or formally deferred.

---

## 14. Bank Responsibilities

Sanima Bank will provide:

- Project owner and decision maker.
- Technical/security contact.
- User list and role matrix.
- Sample and initial production documents.
- Timely review of configuration and UAT findings.
- Internal approvals for staff access and production use.
- Required compliance review and procurement approvals.
- Bank-owned domain/subdomain or access preference, if required.

---

## 15. Exclusions

The following are excluded unless separately agreed:

- On-premise hardware procurement for the bank.
- Core banking system integration.
- DMS, SharePoint, email, or intranet integration.
- Custom AI model fine-tuning.
- Full document digitization or manual data cleanup.
- Large-scale historical document migration beyond included limits.
- Unlimited heavy OCR/PDF/XLS processing without additional capacity sizing.
- Perfect OCR, handwriting, seal, signature, or complex-table verification.
- Automatic credit, risk, legal, regulatory, or customer decisions without authorized bank review.
- Using internal messenger messages as AI/RAG context unless separately scoped and approved in writing.
- Legal, regulatory, or audit certification.
- Third-party VAPT charges.
- Bank-side network, device, or endpoint management.
- Custom workflows not listed in the agreed scope.

---

## 16. Assumptions

- Sanima Bank will use the hosted LipiCore environment operated by Lipi One Pvt. Ltd. and hosted through Silver Lining infrastructure.
- The selected package will be sized before final contract signing.
- Documents provided by the bank are legally permitted to be processed in the hosted environment.
- Sanima Bank will appoint users for UAT within the agreed project timeline.
- AI output is an assistance tool and does not replace authorized bank decision-making.
- Desktop software does not run the backend, database, vector database, object store, RAG pipeline, or model services locally.
- Queued long-document analysis turnaround depends on document quality, OCR requirements, worker capacity, and model queue load.
- Sanima Bank will validate AI-assisted outputs before using them for final regulatory, credit, legal, or customer-facing decisions.

---

## 17. Change Management

Any work outside the agreed scope will be handled through a change request.

Change requests may include:

- New modules.
- Additional integrations.
- Higher storage or AI capacity.
- Custom approval workflows.
- New report formats.
- Additional training.
- Custom security architecture.

Each change request will include scope, effort, timeline, and commercial impact before execution.

---

## 18. Termination and Exit

Upon termination, subject to payment clearance and agreed data retention policies:

- Sanima Bank may request export of its documents and available system records.
- LipiCore will provide a reasonable data export in agreed format.
- Bank data will be deleted from active systems after the agreed retention period.
- Backup deletion will follow the backup retention schedule unless legally restricted.

---

## 19. Why LipiCore

LipiCore Enterprise Document Intelligence Platform is built specifically for financial institutions that require secure document intelligence, controlled AI usage, and operational auditability.

Key advantages:

- Banking-focused AI workflows.
- Private hosted model execution.
- Document-grounded answers with citations.
- Session and bank-level data isolation.
- Audit logs for governance.
- Flexible managed hosting model.
- Separate server and software pricing for procurement clarity.
- Lower operational burden for the bank compared with managing AI infrastructure internally.

---

## 20. Next Steps

1. Bank reviews proposal and selects preferred package.
2. LipiCore and bank complete usage sizing.
3. Commercial terms and final scope are confirmed.
4. Purchase order or agreement is issued.
5. Project kickoff is scheduled.
6. Hosted environment is provisioned.
7. UAT and training are completed.
8. Production go-live begins.

---

## Appendix A: Technical Overview

The platform uses a retrieval-augmented generation architecture:

1. User uploads documents.
2. Documents are stored securely.
3. Text is extracted and divided into searchable chunks.
4. Embeddings are created and stored in a vector database.
5. User questions are matched against relevant document chunks.
6. The AI model generates a response using retrieved context.
7. The response includes source references where applicable.
8. User actions and responses are logged for audit.

Core components:

- Desktop client: LipiCore Desktop for Windows and macOS connected to the hosted LipiCore interface.
- Backend: Python FastAPI.
- Database: PostgreSQL.
- Vector database: Qdrant.
- Object storage: MinIO.
- Queue/admission control: Redis.
- AI runtime: vLLM/private LLM.
- Reverse proxy: Nginx with TLS.

---

## Appendix B: Sample Use Cases for Bank Departments

| Department | Example Use Cases |
|---|---|
| Credit | Loan policy search, agreement review, collateral document checks |
| Compliance | Circular interpretation, policy comparison, audit evidence lookup |
| Operations | SOP lookup, internal process guidance, exception handling support |
| Risk | Risk policy review, portfolio documentation analysis |
| Legal | Contract clause search, document comparison, regulatory reference lookup |
| Internal Audit | Audit trail review, document evidence search, control testing support |
| HR/Admin | Policy FAQ, staff manual search, onboarding document support |

---

## Appendix C: Commercial Summary

| Charge Type | Billing | Purpose |
|---|---|---|
| One-time setup | One-time | Implementation, configuration, onboarding, training |
| Server / infrastructure | Monthly | Hosting, compute, storage, AI runtime, monitoring, backup |
| Software license + support | Monthly | LipiCore Enterprise Document Intelligence Platform, updates, patches, support |
