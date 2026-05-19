# White-Label Bank GPT Appliance Design

## Verdict

The first viable product should be a simple ChatGPT-style assistant for all bank staff, not a department-specific workflow suite. Department workflows are a later expansion after the core chat, RAG, permissions, source citations, audit logs, and appliance operations are reliable.

The product should be sold as a dedicated, white-label, airgapped bank AI appliance. Each bank gets its own deployment, branding, local models, document corpus, users, audit logs, backups, and support process.

## Product Name

Internal product name: **Bank GPT Appliance**

Client-facing product name: configurable per bank.

Examples:
- `NabilGPT`
- `Everest Bank AI`
- `Bank Knowledge Assistant`
- `PolicyGPT`

The UI must never hardcode BankAi/LipiCore as the product name in client deployments.

## Product Promise

Every bank employee gets a private ChatGPT-like assistant, but official bank answers come from approved internal knowledge with citations, permissions, and audit logs.

## Target Users

V1 is for internal bank staff only:
- branch staff
- customer care staff
- credit staff
- operations staff
- compliance staff
- risk staff
- treasury staff
- HR staff
- IT staff
- managers and supervisors

V1 is not a customer-facing chatbot.

## Buyer

Primary buyer:
- CIO / Head of IT
- COO / Operations leadership
- Head of Compliance
- Head of Risk

Secondary buyer:
- HR / Training leadership
- Customer care leadership
- Digital banking leadership

## MVP Scope

### Keep In V1

- ChatGPT-style staff assistant
- white-label branding
- bank-approved knowledge base
- session document upload and analysis
- RAG with source citations
- role-aware document access
- answer modes
- conversation history
- saved answers
- export to PDF/DOCX/TXT
- admin document approval
- audit logs
- appliance health page
- offline deployment model

### Exclude From V1

- department-specific custom apps
- customer-facing chatbot
- autonomous decisions
- credit decision automation
- regulatory filing automation
- fake fine-tuning claims
- unsupported compliance certification claims
- multi-tenant SaaS

## Core UX

The default screen is chat.

Staff should see:
- bank logo and product name
- new chat button
- chat history
- upload button
- mode selector
- simple prompt input
- source/evidence panel
- answer actions: copy, save, export, regenerate

Admin users should also see:
- knowledge library
- document approval queue
- users and roles
- audit logs
- usage metrics
- appliance health
- white-label settings

## Chat Modes

Modes live inside the same chat UI. They are not separate apps.

### Ask Bank Knowledge

Uses approved knowledge base documents. Official answers must cite sources or return not found.

### Analyze Uploaded File

Uses session-uploaded files. Sources should identify uploaded files and pages/chunks.

### Summarize

Summarizes selected documents, uploaded files, or pasted text.

### Draft

Drafts internal emails, memos, call scripts, notices, and process notes. Drafts must be labeled as drafts.

### Translate

Supports English and Nepali. Translation should preserve banking terms where possible.

### Compare Documents

Compares policies, circulars, SOPs, or uploaded files and returns differences with citations.

## Answer Trust Model

Every answer must have a visible trust state:

- `Official source-backed`: answer grounded in approved bank documents.
- `Uploaded-file answer`: answer grounded in user-selected session files.
- `General answer`: answer uses model knowledge and is not official bank policy.
- `Not found`: approved sources do not support an answer.
- `Escalate`: the question should go to a supervisor, compliance, or another authority.

Official bank policy answers cannot be source-free.

## RAG Requirements

The product advantage is not “chat.” The advantage is RAG quality.

V1 RAG must support:
- bank-level document partitioning
- role/document access filtering
- approved-only official corpus
- session upload isolation
- page/section/chunk citations
- not-found behavior
- query rewriting for follow-ups
- source snippets
- retrieval audit metadata
- evaluation set support

## Fine-Tuning Position

Do not claim fine-tuning in V1 unless actual fine-tuning is implemented, documented, evaluated, and repeatable per bank.

Approved wording:

> Powered by private local models and bank-specific retrieval.

Future wording after real implementation:

> Optional bank-specific fine-tuning is available after evaluation and approval.

## White-Label Configuration

Create a white-label settings layer with:
- product name
- bank legal name
- short bank name
- logo
- favicon
- primary color
- accent color
- login background
- welcome message
- example prompts
- language defaults
- support contact
- disclaimer text
- allowed modes
- domain/base URL

White-label config must be stored in the database and exposed through an admin UI. The frontend should load it at startup.

## Information Architecture

Primary navigation:
- Chat
- Knowledge Library
- History
- Saved Answers

Admin navigation:
- Documents
- Approval Queue
- Users and Roles
- Audit Logs
- Usage and Quality
- Appliance Health
- White-Label Settings

Future navigation:
- Department Workflows
- Integrations
- Evaluation Center
- Model Governance

## Security And Governance

V1 must fix the obvious trust gaps before client demos:
- no hardcoded invite password
- no hardcoded bank ID
- upload limits on every upload path
- all request-time LLM paths go through one security gateway
- prompt-injection screening applies to chat, file analysis, and tasks
- PII masking policy is consistent
- auth redirects handle both 401 and 403
- OpenAPI docs can be disabled in production
- Google Fonts and external assets are removed for airgapped mode
- model/debug ports are not publicly exposed

## Appliance Requirements

Each client deployment is dedicated.

V1 appliance requirements:
- Docker Compose deployment
- local Postgres
- local Qdrant
- local Redis
- local MinIO or local object storage
- local vLLM
- offline model files
- offline frontend assets
- backup and restore scripts
- health check page
- diagnostic export
- upgrade and rollback procedure

## Success Metrics

MVP success is not “it has chat.”

Measure:
- daily active staff users
- questions per user
- percentage of answers with sources
- citation click-through
- not-found rate
- upload-to-ready time
- p95 response latency
- failed upload rate
- retrieval/citation accuracy on test set
- admin document approval time
- customer care staff response consistency, measured in pilot

## V1 Acceptance Criteria

The product is V1-ready when:
- any staff member can log in and ask questions without training
- official answers show sources or refuse
- uploaded documents are session-isolated
- admin can approve knowledge documents
- audit logs capture every AI interaction
- white-label settings change branding without code edits
- frontend runs without internet assets
- backend tests run on Python 3.11
- build/lint/tests have documented commands
- one clean appliance install can be reproduced

## Future Expansion

After usage data proves demand, add department workflows:
- Customer Care
- Credit
- Operations
- Compliance
- HR onboarding
- Risk
- Treasury
- IT support

These should be built as templates on top of the same chat/RAG engine, not as separate products.

## Self-Review

- No department-specific apps in V1.
- No customer-facing chatbot in V1.
- No fine-tuning claim without implementation.
- White-labeling is a core system layer, not a theme hack.
- Appliance delivery is dedicated per client, not multi-tenant SaaS.
