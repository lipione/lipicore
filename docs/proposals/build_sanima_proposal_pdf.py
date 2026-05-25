from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    BaseDocTemplate,
    Flowable,
    Frame,
    HRFlowable,
    KeepTogether,
    ListFlowable,
    ListItem,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parent
PDF_PATH = ROOT / "Sanima_Bank_LipiCore_Enterprise_Document_Intelligence_Platform_Proposal.pdf"

PAGE_WIDTH, PAGE_HEIGHT = letter
MARGIN = 0.75 * inch
CONTENT_WIDTH = PAGE_WIDTH - (2 * MARGIN)

INK = colors.HexColor("#0B1C30")
MUTED = colors.HexColor("#526071")
BLUE = colors.HexColor("#0051D5")
DARK_BLUE = colors.HexColor("#13233D")
LIGHT_BLUE = colors.HexColor("#EAF2FF")
PALE = colors.HexColor("#F6F8FC")
BORDER = colors.HexColor("#D7DEE8")
GREEN = colors.HexColor("#007A55")
GOLD = colors.HexColor("#8A6500")


class SectionMarker(Flowable):
    def __init__(self, title: str):
        super().__init__()
        self.title = title

    def wrap(self, availWidth, availHeight):
        return availWidth, 0

    def draw(self):
        self.canv._current_section_title = self.title


def p(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(text, style)


def escape(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def money(value: str) -> str:
    return value.replace("NPR", "<b>NPR</b>")


def build_styles():
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            "CoverKicker",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=13,
            textColor=BLUE,
            alignment=TA_CENTER,
            spaceAfter=14,
        )
    )
    styles.add(
        ParagraphStyle(
            "CoverTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=27,
            leading=32,
            textColor=INK,
            alignment=TA_CENTER,
            spaceAfter=10,
        )
    )
    styles.add(
        ParagraphStyle(
            "CoverSubtitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=13,
            leading=18,
            textColor=MUTED,
            alignment=TA_CENTER,
            spaceAfter=18,
        )
    )
    styles.add(
        ParagraphStyle(
            "Body",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9.8,
            leading=13.2,
            textColor=INK,
            alignment=TA_JUSTIFY,
            spaceAfter=7,
        )
    )
    styles.add(
        ParagraphStyle(
            "BodyLeft",
            parent=styles["Body"],
            alignment=TA_LEFT,
        )
    )
    styles.add(
        ParagraphStyle(
            "Small",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.2,
            leading=10.5,
            textColor=MUTED,
            alignment=TA_LEFT,
            spaceAfter=4,
        )
    )
    styles.add(
        ParagraphStyle(
            "H1",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=18,
            textColor=BLUE,
            spaceBefore=12,
            spaceAfter=7,
            keepWithNext=True,
        )
    )
    styles.add(
        ParagraphStyle(
            "H2",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=15,
            textColor=DARK_BLUE,
            spaceBefore=8,
            spaceAfter=5,
            keepWithNext=True,
        )
    )
    styles.add(
        ParagraphStyle(
            "H3",
            parent=styles["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=10.5,
            leading=13,
            textColor=INK,
            spaceBefore=6,
            spaceAfter=3,
            keepWithNext=True,
        )
    )
    styles.add(
        ParagraphStyle(
            "LipiBullet",
            parent=styles["BodyLeft"],
            leftIndent=14,
            firstLineIndent=-8,
            bulletIndent=3,
            spaceAfter=3,
        )
    )
    styles.add(
        ParagraphStyle(
            "LipiNumbered",
            parent=styles["BodyLeft"],
            leftIndent=18,
            firstLineIndent=-11,
            spaceAfter=3,
        )
    )
    styles.add(
        ParagraphStyle(
            "TableHead",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.3,
            leading=10,
            textColor=colors.white,
            alignment=TA_LEFT,
        )
    )
    styles.add(
        ParagraphStyle(
            "TableCell",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.1,
            leading=10.2,
            textColor=INK,
            alignment=TA_LEFT,
        )
    )
    styles.add(
        ParagraphStyle(
            "TableCellCenter",
            parent=styles["TableCell"],
            alignment=TA_CENTER,
        )
    )
    styles.add(
        ParagraphStyle(
            "Callout",
            parent=styles["BodyLeft"],
            fontName="Helvetica",
            fontSize=9.2,
            leading=12.5,
            textColor=INK,
            leftIndent=0,
            rightIndent=0,
            spaceBefore=3,
            spaceAfter=3,
        )
    )
    return styles


STYLES = build_styles()


def bullet_list(items: list[str]) -> ListFlowable:
    return ListFlowable(
        [ListItem(p(escape(item), STYLES["BodyLeft"]), leftIndent=8) for item in items],
        bulletType="bullet",
        start="circle",
        leftIndent=16,
        bulletFontName="Helvetica",
        bulletFontSize=7,
        bulletDedent=8,
        spaceBefore=0,
        spaceAfter=6,
    )


def numbered_list(items: list[str]) -> ListFlowable:
    return ListFlowable(
        [ListItem(p(escape(item), STYLES["BodyLeft"]), leftIndent=12) for item in items],
        bulletType="1",
        leftIndent=18,
        bulletFontName="Helvetica",
        bulletFontSize=9,
        bulletDedent=8,
        spaceBefore=0,
        spaceAfter=6,
    )


def table(rows, widths, header=True, repeat_rows=1):
    converted = []
    for idx, row in enumerate(rows):
        style = STYLES["TableHead"] if header and idx == 0 else STYLES["TableCell"]
        converted.append([p(str(cell), style) for cell in row])

    t = Table(converted, colWidths=widths, repeatRows=repeat_rows if header else 0, hAlign="LEFT")
    commands = [
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.35, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    if header:
        commands.extend(
            [
                ("BACKGROUND", (0, 0), (-1, 0), DARK_BLUE),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ]
        )
    for r in range(1 if header else 0, len(rows)):
        if r % 2 == 0:
            commands.append(("BACKGROUND", (0, r), (-1, r), PALE))
    t.setStyle(TableStyle(commands))
    return t


def callout(title: str, text: str):
    data = [[p(f"<b>{escape(title)}</b><br/>{escape(text)}", STYLES["Callout"])]]
    t = Table(data, colWidths=[CONTENT_WIDTH], hAlign="LEFT")
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BLUE),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#BFD6FF")),
                ("LEFTPADDING", (0, 0), (-1, -1), 9),
                ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return KeepTogether([t, Spacer(1, 8)])


def heading(title: str, level: int = 1):
    style = {1: "H1", 2: "H2", 3: "H3"}[level]
    return [SectionMarker(title if level == 1 else ""), p(escape(title), STYLES[style])]


def page_break(story):
    if story and not isinstance(story[-1], PageBreak):
        story.append(PageBreak())


def cover_page():
    meta_left = [
        ["Prepared for", "Sanima Bank"],
        ["Prepared by", "Lipi One Pvt. Ltd."],
        ["Hosting and server", "Silver Lining"],
    ]
    meta_right = [
        ["Product", "LipiCore Bank Staff AI Appliance and Document Intelligence Platform"],
        ["Proposal date", "May 23, 2026"],
        ["Validity", "30 days from proposal date"],
    ]

    left_table = table(meta_left, [1.15 * inch, 2.0 * inch], header=False, repeat_rows=0)
    right_table = table(meta_right, [1.15 * inch, 2.0 * inch], header=False, repeat_rows=0)

    wrapper = Table([[left_table, right_table]], colWidths=[3.2 * inch, 3.2 * inch], hAlign="CENTER")
    wrapper.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )

    return [
        Spacer(1, 1.05 * inch),
        p("CONFIDENTIAL COMMERCIAL PROPOSAL", STYLES["CoverKicker"]),
        p("Managed Hosted LipiCore Bank Staff AI Appliance", STYLES["CoverTitle"]),
        p("Proposal to Sanima Bank", STYLES["CoverSubtitle"]),
        HRFlowable(width="62%", thickness=1, color=BLUE, spaceBefore=2, spaceAfter=20, hAlign="CENTER"),
        wrapper,
        Spacer(1, 0.45 * inch),
        callout(
            "Commercial structure",
            "One-time setup fee, separate monthly hosting/server charge through Silver Lining, and separate monthly LipiCore software license and support charge through Lipi One Pvt. Ltd.",
        ),
        Spacer(1, 0.2 * inch),
        p(
            "This proposal is prepared for discussion, evaluation, procurement review, and commercial finalization. Final pricing and service commitments are subject to agreed usage sizing, storage requirements, support level, and contractual terms.",
            STYLES["Small"],
        ),
        PageBreak(),
    ]


def commercial_table():
    rows = [
        ["Package", "One-Time Setup", "Monthly Hosting / Server", "Monthly Software License + Support", "Total Monthly"],
        ["Starter", money("NPR 500,000"), money("NPR 175,000"), money("NPR 225,000"), money("NPR 400,000")],
        ["Standard", money("NPR 800,000"), money("NPR 350,000"), money("NPR 450,000"), money("NPR 800,000")],
        ["Enterprise", money("NPR 1,500,000"), money("NPR 750,000"), money("NPR 850,000"), money("NPR 1,600,000")],
    ]
    widths = [1.0 * inch, 1.05 * inch, 1.35 * inch, 1.55 * inch, 1.05 * inch]
    return table(rows, widths)


def package_fit_table():
    rows = [
        ["Package", "Recommended For", "Included Capacity"],
        ["Starter", "Department or focused bank rollout", "200-500 users, standard managed capacity, business-hours support"],
        ["Standard", "Bank-wide production use", "1,000-2,000 users, stronger managed capacity, priority queue during business hours"],
        ["Enterprise", "High-volume institution-wide deployment", "3,000-5,000 users, dedicated managed capacity, priority support and escalation"],
    ]
    return table(rows, [1.0 * inch, 2.45 * inch, 3.05 * inch])


def lipicore_per_user_table():
    rows = [
        ["Package", "User Band", "Total Monthly", "Effective Cost / User / Month"],
        ["Starter", "200-500 users", "NPR 400,000", "NPR 2,000 to NPR 800"],
        ["Standard", "1,000-2,000 users", "NPR 800,000", "NPR 800 to NPR 400"],
        ["Enterprise", "3,000-5,000 users", "NPR 1,600,000", "NPR 533 to NPR 320"],
    ]
    return table(rows, [1.25 * inch, 1.45 * inch, 1.45 * inch, 2.35 * inch])


def market_comparison_table():
    rows = [
        ["Option", "Indicative Public Cost", "What It Includes", "Bank Tradeoff"],
        [
            "LipiCore Standard",
            "NPR 800,000/month for 1,000-2,000 users",
            "Windows/macOS desktop client, hosted bank AI appliance, approved-knowledge Q&A, OCR extraction, RAG, audit logs, RBAC, internal chat, support, and managed infrastructure.",
            "Purpose-built for bank document intelligence; model choice and capacity are managed by Lipi One/Silver Lining.",
        ],
        [
            "ChatGPT Business",
            "USD 25/user/month monthly or USD 20/user/month annual equivalent",
            "General ChatGPT workspace with admin controls and business privacy terms.",
            "Seat cost scales linearly; API usage, custom RAG, bank document platform, hosting, and custom audit workflows are separate.",
        ],
        [
            "Claude Team",
            "Around USD 25/user/month monthly for standard seats, with annual discounts depending on current Claude plan terms; Team is listed for 5-150 users.",
            "General Claude team workspace with connectors and administration features.",
            "Larger banks need Enterprise; enterprise use may combine seat price and API usage. Banking-specific platform still needs to be built.",
        ],
        [
            "DIY API Build",
            "Token usage varies by model and workload; GPT-5.4/Sonnet-class models can become material at high document volume.",
            "Access to frontier model APIs.",
            "Bank must still build and operate document ingestion, vector search, citations, RBAC, audit logs, security review, support, and hosting.",
        ],
    ]
    return table(rows, [1.15 * inch, 1.55 * inch, 2.05 * inch, 1.75 * inch])


def bank_scale_cost_table():
    rows = [
        ["User Count", "ChatGPT / Claude @ USD 25/User/Month", "Approx. NPR / Month"],
        ["500 users", "USD 12,500/month", "Approx. NPR 19.1 lakh/month"],
        ["2,000 users", "USD 50,000/month", "Approx. NPR 76.5 lakh/month"],
        ["5,000 users", "USD 125,000/month", "Approx. NPR 1.91 crore/month"],
    ]
    return table(rows, [1.25 * inch, 2.7 * inch, 2.55 * inch])


def updated_workspaces_table():
    rows = [
        ["Workspace", "Current Included Capability", "Safe Boundary"],
        [
            "OCR Extraction",
            "Upload supported PDFs, Office files, spreadsheets, CSV/TXT, and images to extract text without adding them to approved knowledge.",
            "Extracted text is staff-reviewable and not a guarantee of perfect OCR.",
        ],
        [
            "Compliance Workspace",
            "Circular impact summaries, affected departments, obligations, review notes, and officer-review status.",
            "Supports compliance research and drafting; it is not regulator-approved compliance automation.",
        ],
        [
            "Model Lab",
            "Model route visibility, capability tags, status metrics, benchmark runner, candidate comparison, and claim-readiness indicators.",
            "Model recommendations must be backed by measured bank workload evidence.",
        ],
    ]
    return table(rows, [1.35 * inch, 3.15 * inch, 2.0 * inch])


def workflow_fit_table():
    rows = [
        ["Workflow", "Fit Today", "Commercial Positioning"],
        ["Customer-care and branch lookup", "Strong", "Recommended first use case with approved SOPs, product FAQs, and source-backed answer checks."],
        ["Compliance circular search", "Strong", "Works best with approved circulars, freshness metadata, and scheduled RAG evaluations."],
        ["Internal policy Q&A", "Strong", "Useful across operations, HR/admin, branch teams, product teams, and internal audit."],
        ["OCR text extraction", "Strong", "Extracts text from supported documents and images without indexing them into approved knowledge."],
        ["Large document analysis", "Good, queue-based", "Heavy OCR, large PDFs, and Excel workbooks run as background jobs with stored results."],
        ["Compliance review notes", "Controlled support", "Summarizes circular impact and obligations for officer review and sign-off."],
    ]
    return table(rows, [1.8 * inch, 1.2 * inch, 3.5 * inch])


def scope_phase_table():
    rows = [
        ["Phase", "Lipi One / Silver Lining Responsibilities", "Sanima Bank Responsibilities"],
        [
            "1. Initiation",
            "Kickoff, requirements confirmation, deployment plan, UAT criteria, role design.",
            "Nominate project owner, technical coordinator, UAT users, and document owners.",
        ],
        [
            "2. Hosted setup",
            "Provision managed environment, configure HTTPS, backend services, storage, database, model runtime, monitoring, backups.",
            "Confirm access preference, domain/subdomain requirements, and security contacts.",
        ],
        [
            "3. Application configuration",
            "Configure tenant, roles, branding, document categories, workflow modules, audit views, AI routing, and evaluation settings.",
            "Provide role matrix, user list, document category structure, workflow owners, and pilot use cases.",
        ],
        [
            "4. Initial onboarding",
            "Upload and index initial documents, validate retrieval, citations, parsing, long-document jobs, and workflow draft behavior.",
            "Provide sample and initial production documents plus OCR samples, compliance circulars, and evaluation questions approved for onboarding.",
        ],
        [
            "5. Training and UAT",
            "Train administrators and staff users, support UAT, resolve go-live blockers.",
            "Complete UAT within agreed timeline and sign off go-live readiness.",
        ],
        [
            "6. Go-live and support",
            "Move environment to production, monitor early usage, provide support and health checks.",
            "Coordinate production communication and user adoption.",
        ],
    ]
    return table(rows, [1.0 * inch, 3.05 * inch, 2.45 * inch])


def simple_table(headers, body, widths):
    return table([headers] + body, widths)


def build_story():
    story = []
    story.extend(cover_page())

    story.extend(heading("1. Executive Summary"))
    story.append(
        p(
            "Lipi One Pvt. Ltd. proposes to provide Sanima Bank with the updated LipiCore Bank Staff AI Appliance and Document Intelligence Platform as a managed hosted service delivered through dedicated Windows and macOS desktop software. The platform is designed for banking teams that need approved-knowledge Q&A, secure document analysis, OCR text extraction, compliance research, model evaluation, and AI-assisted drafting without relying on public AI services for confidential banking material.",
            STYLES["Body"],
        )
    )
    story.append(
        p(
            "The solution will be hosted on server infrastructure provided and managed through Silver Lining. Lipi One Pvt. Ltd. will provide the LipiCore software platform, desktop client packaging, implementation, configuration, support, and ongoing maintenance. Sanima Bank will receive a secured bank environment with role-based access, document upload and indexing, AI chat over approved documents, source citations, OCR Extraction, Compliance Workspace, Model Lab, activity logging, analytics, administrative controls, and the internal staff chat module included as a bonus.",
            STYLES["Body"],
        )
    )
    story.append(
        callout(
            "Recommended approach",
            "Adopt the Standard hosted package for a 1,000-2,000 user production rollout after a measured department pilot. Final capacity should be confirmed after active-user concurrency, monthly query volume, document volume, open-source OCR needs, optional vision needs, storage volume, workflow mix, and support requirements are reviewed.",
        )
    )

    story.extend(heading("2. Understanding of Sanima Bank's Requirement"))
    story.append(
        p(
            "The bank requires a full proposal covering platform capability, commercial terms, pricing, implementation scope, responsibilities, timeline, support model, security controls, acceptance criteria, exclusions, and next steps.",
            STYLES["Body"],
        )
    )
    story.append(
        bullet_list(
            [
                "Securely upload, process, search, and analyze internal banking documents.",
                "Ask natural language questions over policies, circulars, reports, manuals, SOPs, and operational documents.",
                "Receive source-grounded AI answers with document references and citations.",
                "Extract text from supported PDFs, Office files, spreadsheets, CSV/TXT, and images without indexing them.",
                "Prepare compliance circular impact notes and obligation summaries for officer review.",
                "Track model routes, status, and benchmark evidence before making model or capacity claims.",
                "Maintain audit records for user activity, uploads, queries, and assistant responses.",
                "Apply role-based access for administrators, bank admins, and staff users.",
                "Use a managed hosted environment without Sanima Bank needing to operate AI servers or model infrastructure.",
                "Deploy staff access through approved Windows and macOS desktop software rather than a general webapp workflow.",
                "Include internal staff chat as a bonus module for bank-scoped communication.",
                "Apply additional storage pricing transparently at NPR 10,000 per TB per month where required.",
                "Separate commercial charges for setup, hosting/server, and LipiCore software license/support.",
            ]
        )
    )

    page_break(story)
    story.extend(heading("3. Proposed Solution"))
    story.append(
        p(
            "LipiCore Bank Staff AI Appliance and Document Intelligence Platform will be deployed as a secure managed hosted service for Sanima Bank. Users will access the platform through LipiCore Desktop software for Windows and macOS, connected only to the approved hosted LipiCore environment. This provides the bank with a controlled application surface instead of ordinary browser access, while keeping the backend services, documents, database, vector index, queues, and model runtime in the managed hosted environment.",
            STYLES["Body"],
        )
    )
    story.append(
        p(
            "The system uses retrieval-augmented generation. Documents are uploaded, stored, parsed, embedded, indexed, and searched through a bank-partitioned retrieval pipeline. When a user asks a question, LipiCore retrieves relevant document context, sends that context to the private model runtime, and returns a response with source references where available. AI output is positioned as staff assistance and must remain subject to authorized bank review for regulatory, credit, legal, customer-facing, or final decision use.",
            STYLES["Body"],
        )
    )
    story.extend(heading("Core Capabilities", 2))
    story.append(
        bullet_list(
            [
                "Secure document upload and enterprise document library.",
                "Windows and macOS desktop software access.",
                "AI chat over uploaded documents and approved knowledge sources with streaming responses and conversation history.",
                "Local private model routes for text/analyst work and optional vision/image analysis, sized according to package capacity. OCR extraction uses open-source Tesseract plus direct parsers by default.",
                "Queued long-document analysis for large PDFs, scanned documents, and Excel workbooks.",
                "OCR Extraction, Compliance Workspace, and Model Lab modules.",
                "Session-bound document isolation for temporary analysis.",
                "Bank-level data partitioning for hosted environments.",
                "Source citations, source passage review, and document attribution for generated answers.",
                "Document lifecycle controls for draft, approved, superseded, archived, and disabled documents.",
                "Hybrid retrieval with vector search, keyword search, reranking, and citation verification.",
                "RAG evaluation tools for testing answer quality on agreed document sets.",
                "Audit logs for governance and internal review.",
                "Role-based access control and user management.",
                "Dashboard, analytics, activity, document, and administrative views.",
                "Private model execution on managed infrastructure.",
                "Configurable fast and deep AI response modes, subject to selected package capacity.",
            ]
        )
    )

    page_break(story)
    story.extend(heading("Updated Product Modules", 2))
    story.append(
        p(
            "The current LipiCore product is broader than a basic document chatbot. It now includes focused staff tools for approved knowledge, OCR extraction, compliance support, model evaluation, and long-document analysis while keeping final decisions with authorized bank staff.",
            STYLES["Body"],
        )
    )
    story.append(updated_workspaces_table())
    story.append(Spacer(1, 8))
    story.append(
        callout(
            "Product boundary",
            "LipiCore is a staff-assistance and decision-support appliance. It does not autonomously approve loans, replace compliance officers, guarantee regulatory correctness, or certify scanned signatures/seals. High-risk outputs require Sanima Bank review and sign-off.",
        )
    )

    page_break(story)
    story.extend(heading("4. Deployment and Hosting Model"))
    story.append(
        p(
            "The platform will be hosted on Silver Lining server infrastructure and operated as a managed service for Sanima Bank. Sanima Bank users will access the system through the LipiCore Desktop client for Windows and macOS over HTTPS. Lipi One Pvt. Ltd. will configure and maintain the LipiCore platform layer, while the hosting/server component will be commercially separated for procurement clarity.",
            STYLES["Body"],
        )
    )
    story.extend(heading("Hosted Stack", 2))
    story.append(
        bullet_list(
            [
                "LipiCore Desktop client interface.",
                "Python FastAPI backend.",
                "PostgreSQL database.",
                "Qdrant vector database.",
                "MinIO object storage.",
                "Redis queue and admission control.",
                "Redis/RQ ingestion and long-document worker.",
                "vLLM/private model runtime for text/analyst routes.",
                "Optional vision/image model route for image-heavy workflows where enabled; OCR text extraction uses open-source Tesseract.",
                "Nginx reverse proxy with HTTPS/TLS.",
                "Model Lab, RAG Evaluation Center, and audit dashboards.",
                "Monitoring, backups, and operational tooling.",
            ]
        )
    )
    story.extend(heading("Data Isolation", 2))
    story.append(
        p(
            "Each bank environment is logically isolated using bank-level partitioning across application records, vector search metadata, document records, and audit data. Documents uploaded for Sanima Bank will not be visible to other bank environments. Where required by the final package and contract, Sanima Bank may be assigned dedicated server capacity.",
            STYLES["Body"],
        )
    )
    story.extend(heading("Desktop Access Security", 2))
    story.append(
        bullet_list(
            [
                "Dedicated Windows and macOS desktop software access instead of a general browser workflow.",
                "Desktop client connects only to approved LipiCore HTTPS origins.",
                "Backend authorization remains the source of truth for documents, uploads, downloads, chat, and user permissions.",
                "Desktop app lock behavior hides visible content and clears local web session storage.",
                "Unknown app-window navigations are blocked or opened externally rather than loaded inside the LipiCore window.",
                "Bank documents and AI data remain inside the managed hosted environment, not on staff machines.",
            ]
        )
    )

    page_break(story)
    story.extend(heading("5. Scope of Work"))
    story.append(scope_phase_table())
    story.append(Spacer(1, 8))
    story.append(
        p(
            "Initial onboarding includes up to 10 GB of documents or 1,000 files, whichever comes first. Additional migration, scanned document processing, large historical archives, or manual cleanup can be quoted separately.",
            STYLES["Small"],
        )
    )

    page_break(story)
    story.extend(heading("6. Functional Scope"))
    modules = [
        ["Secure Login", "Authentication, session handling, password security, and authenticated API access."],
        ["Desktop Software Access", "Windows and macOS LipiCore Desktop client connected to approved hosted LipiCore origins."],
        ["User Management", "Administrator, bank admin, and staff user roles."],
        ["Document Library", "Upload, organize, process, lifecycle-manage, and search bank documents."],
        ["Approved Knowledge Q&A", "Ask questions over approved documents with source references and citations where available."],
        ["Queued Long-Document Analysis", "Background processing for large PDFs, OCR-heavy files, and detailed Excel workbook review."],
        ["OCR Extraction", "Upload supported documents and images to extract text without adding them to approved knowledge."],
        ["Compliance Workspace", "Circular impact summaries, obligations, affected departments, review notes, and officer-review workflow."],
        ["Model Lab", "Model route visibility, status metrics, benchmark runner, and claim-readiness comparison."],
        ["Internal Chat (Bonus)", "Bank-scoped staff messenger module included as a bonus module and kept separate from AI/RAG context."],
        ["Session Uploads", "Upload temporary documents into a chat session for isolated analysis."],
        ["Source Evidence", "Assistant answers include source document references and passage evidence where available."],
        ["RAG Evaluation", "Evaluation center for testing retrieval and answer quality on agreed question sets."],
        ["Audit Logs", "Activity records for uploads, queries, users, and assistant responses."],
        ["Analytics Dashboard", "Usage, document, and activity-level reporting."],
        ["Compliance Support", "Policy comparison, document analysis, and risk analysis assistance."],
        ["Model Modes", "Fast response and deeper analysis modes, subject to package capacity."],
    ]
    story.append(simple_table(["Module", "Included Scope"], modules, [1.65 * inch, 4.85 * inch]))
    story.extend(heading("Supported File Types", 2))
    story.append(bullet_list(["PDF", "DOCX", "XLSX/XLS", "PPTX", "TXT", "CSV", "Image-based documents where OCR is enabled and document quality permits"]))
    story.extend(heading("Supported Staff Workflows", 2))
    story.append(workflow_fit_table())

    page_break(story)
    story.extend(heading("7. Security and Compliance Controls"))
    story.append(
        bullet_list(
            [
                "HTTPS/TLS encrypted access.",
                "Windows and macOS desktop client access instead of general browser-based usage.",
                "Approved LipiCore origin restrictions inside the desktop client.",
                "Desktop app lock behavior with local session clearing.",
                "Bank-level data isolation.",
                "Session-level document isolation.",
                "Role-based access control.",
                "Password hashing using bcrypt.",
                "JWT-based authenticated API access.",
                "Prompt guardrails for document-grounded responses.",
                "Source verification and retrieval evaluation controls for reducing unsupported answers.",
                "Document lifecycle states to control approved, superseded, archived, and disabled content.",
                "Document freshness and review metadata for approved knowledge where configured.",
                "PII masking controls for sensitive information.",
                "Audit logging for major system activity.",
                "OCR Extraction, Compliance Workspace, Model Lab, and RAG Evaluation activity remain role-scoped and auditable.",
                "Internal messenger data is kept separate from AI document chat and is not embedded into the RAG index by default.",
                "Restricted operational access to hosted infrastructure.",
                "Database, object storage, and vector store access controlled through backend services.",
            ]
        )
    )
    story.extend(heading("Data Use Commitment", 2))
    story.append(
        bullet_list(
            [
                "Sanima Bank documents remain within the managed hosted environment.",
                "Sanima Bank documents are not used to train public AI models.",
                "Sanima Bank data is not shared with other banks or third parties except where explicitly approved by the bank.",
                "On termination, bank data can be exported and removed according to the agreed retention and exit process.",
            ]
        )
    )
    story.append(
        callout(
            "Compliance note",
            "LipiCore provides controls that support banking governance, auditability, and internal compliance. Final regulatory approval, internal policy approval, and third-party certification requirements remain the responsibility of Sanima Bank unless separately contracted.",
        )
    )

    page_break(story)
    story.extend(heading("8. Implementation Timeline"))
    story.append(
        p(
            "The standard implementation timeline is 4 to 6 weeks from purchase order and receipt of required Sanima Bank inputs. Timeline depends on document volume, bank-side approvals, integration needs, and UAT response time.",
            STYLES["Body"],
        )
    )
    timeline_rows = [
        ["Kickoff and requirements", "3-5 business days", "Confirmed scope, project plan, roles, and access requirements"],
        ["Environment provisioning", "5-7 business days", "Hosted Sanima Bank environment ready"],
        ["Configuration and documents", "5-10 business days", "Tenant configured and initial documents indexed"],
        ["Training and UAT", "5-10 business days", "Users trained and UAT completed"],
        ["Go-live", "2-3 business days", "Production access and go-live support"],
    ]
    story.append(simple_table(["Phase", "Duration", "Output"], timeline_rows, [2.0 * inch, 1.25 * inch, 3.25 * inch]))

    story.extend(heading("9. Deliverables"))
    story.append(
        bullet_list(
            [
                "Hosted production environment for Sanima Bank.",
                "Windows and macOS LipiCore Desktop access package.",
                "Configured Sanima Bank tenant and administrator accounts.",
                "Role-based user access structure.",
                "Document library and AI assistant modules.",
                "OCR Extraction, Compliance Workspace, Model Lab, and RAG Evaluation modules configured for agreed pilot scope.",
                "Internal chat system bonus module.",
                "Initial document ingestion as defined in scope.",
                "Audit logging and analytics views.",
                "Administrator and staff training.",
                "User handover material.",
                "Production go-live support.",
                "Monthly support and maintenance under the selected subscription plan.",
            ]
        )
    )

    page_break(story)
    story.extend(heading("10. Pricing"))
    story.append(
        p(
            "Pricing is separated into one-time setup, monthly hosting/server, and monthly software license/support charges. All prices below are indicative in NPR and exclusive of applicable VAT, taxes, withholding, bank charges, and government duties. Final pricing will be confirmed after usage sizing, storage requirements, support level, and server capacity are finalized.",
            STYLES["Body"],
        )
    )
    story.append(commercial_table())
    story.append(Spacer(1, 8))
    story.append(package_fit_table())
    story.append(Spacer(1, 8))
    storage_rows = [
        ["Storage Item", "Commercial Treatment"],
        ["Included storage", "Confirmed during final package sizing based on document volume and retention requirement."],
        ["Additional storage", "NPR 10,000 per TB per month beyond the agreed included allocation."],
    ]
    story.append(simple_table(["Storage", "Pricing"], storage_rows[1:], [1.65 * inch, 4.85 * inch]))

    page_break(story)
    story.extend(heading("Market Comparison and Tradeoffs", 2))
    story.append(
        p(
            "Public ChatGPT and Claude prices are useful benchmarks, but they are not direct substitutes for LipiCore. ChatGPT Business and Claude Team are general-purpose AI workspaces. LipiCore is a managed bank staff AI appliance with desktop delivery, hosted infrastructure, document ingestion, OCR extraction, retrieval, source citations, role-based access, audit records, internal staff chat, model evaluation tooling, and support included in one package.",
            STYLES["Body"],
        )
    )
    story.append(lipicore_per_user_table())
    story.append(Spacer(1, 8))
    story.append(bank_scale_cost_table())
    story.append(
        p(
            "For reference, these comparisons use an indicative USD/NPR rate of approximately NPR 153.07 per USD as of May 23, 2026. Actual foreign exchange, taxes, procurement terms, data residency, enterprise contract terms, and usage limits may vary.",
            STYLES["Small"],
        )
    )
    story.append(Spacer(1, 8))
    story.append(market_comparison_table())
    story.append(
        p(
            "Market pricing references: OpenAI ChatGPT Business public pricing, Anthropic Claude pricing, and public USD/NPR exchange-rate sources checked on May 23, 2026.",
            STYLES["Small"],
        )
    )

    page_break(story)
    story.extend(heading("What the One-Time Setup Fee Covers", 2))
    story.append(
        bullet_list(
            [
                "Project kickoff and requirements confirmation.",
                "Hosted environment provisioning.",
                "Sanima Bank tenant setup.",
                "Security and access configuration.",
                "Initial admin/user role configuration.",
                "Initial workflow configuration for OCR Extraction, Compliance Workspace, Model Lab, and RAG Evaluation.",
                "Initial document onboarding up to 10 GB or 1,000 files.",
                "Representative queued long-document and OCR extraction testing on agreed sample files.",
                "UAT support.",
                "One administrator training session.",
                "One staff training session.",
                "Go-live support.",
            ]
        )
    )
    story.extend(heading("What the Monthly Hosting / Server Charge Covers", 2))
    story.append(
        bullet_list(
            [
                "Managed server compute provided through Silver Lining.",
                "AI model runtime capacity.",
                "Storage allocation.",
                "Additional storage expansion at NPR 10,000 per TB per month where required.",
                "Database and vector database hosting.",
                "Object storage.",
                "Backup storage.",
                "Monitoring and operational maintenance.",
                "Network, TLS, and hosting operations.",
            ]
        )
    )
    story.extend(heading("What the Monthly Software License + Support Charge Covers", 2))
    story.append(
        bullet_list(
            [
                "LipiCore Bank Staff AI Appliance and Document Intelligence Platform software license.",
                "Windows and macOS LipiCore Desktop software access.",
                "AI document analysis modules.",
                "OCR Extraction, Compliance Workspace, Model Lab, and RAG Evaluation modules.",
                "RAG retrieval, source citation, and audit logging features.",
                "User management and role-based access control.",
                "Maintenance updates, security patches, and helpdesk support under the selected support plan.",
            ]
        )
    )

    page_break(story)
    story.extend(heading("Internal Chat System Bonus Module", 2))
    story.append(
        p(
            "Lipi One Pvt. Ltd. will include the internal chat system as a bonus module with the hosted LipiCore package for Sanima Bank. The internal chat system is separate from the AI document chat. It is intended for staff-to-staff communication inside the LipiCore environment, so teams can coordinate around document analysis, compliance queries, operational follow-ups, and internal decisions without leaving the secured platform.",
            STYLES["Body"],
        )
    )
    story.append(
        callout(
            "Messenger boundary",
            "The internal chat system is a communication module, not an AI training source. Chat messages and shared files are not embedded into the document intelligence index, not used as AI context, and not used to train public AI models unless a future written scope explicitly changes that boundary.",
        )
    )
    chat_features = [
        ["Direct messages", "Secure one-to-one staff conversations inside the Sanima Bank LipiCore environment."],
        ["Department channels", "Automatic or configured channels for departments such as compliance, credit, operations, risk, audit, and administration."],
        ["Custom groups", "Project, branch, committee, and working-group conversations for internal coordination."],
        ["Announcements", "Controlled announcement channels for bank-wide or department-level notices."],
        ["File and image sharing", "Secure sharing of internal files and images inside messenger, subject to retention and attachment policy."],
        ["Unread and read status", "Unread counters, delivery status, and read status for practical staff follow-up."],
        ["Bank-scoped directory", "Users are drawn from the configured Sanima Bank user base and remain isolated from other tenants."],
        ["Searchable history", "Local keyword search over permitted conversations for follow-up and continuity."],
        ["Audit and retention", "Administrative audit events, retention policy, and attachment policy support for governance."],
        ["Commercial treatment", "Included at no additional software license charge within the selected hosted package."],
    ]
    story.append(simple_table(["Feature", "Included Detail"], chat_features, [2.0 * inch, 4.5 * inch]))

    page_break(story)
    story.extend(heading("11. Payment Terms"))
    story.append(
        bullet_list(
            [
                "One-time setup fee: 50% upon purchase order and 50% before production go-live.",
                "Monthly hosting/server charge: billed monthly in advance.",
                "Monthly software subscription: billed monthly in advance.",
                "Minimum contract term: 12 months.",
                "Taxes: VAT and applicable taxes charged separately.",
                "Price validity: 30 days from proposal date.",
                "Annual prepayment discounts can be discussed for bank procurement preference.",
            ]
        )
    )

    story.extend(heading("12. Support and SLA"))
    support_rows = [
        ["Standard Support", "Starter", "Email and remote support, business-hours support window, 4 business-hour critical acknowledgement, monthly health check, security and software patches."],
        ["Priority Queue", "Standard", "Business-hours support with priority queue over Starter, critical acknowledgement target agreed in final support schedule, monthly health check, security and software patches."],
        ["Priority Support", "Enterprise or upgrade", "Priority remote support, extended support window, 1-hour critical acknowledgement target where commercially agreed, dedicated escalation contact, quarterly service review."],
    ]
    story.append(simple_table(["Support Level", "Applies To", "Coverage"], support_rows, [1.35 * inch, 1.35 * inch, 3.8 * inch]))
    sla_rows = [
        ["Starter", "Pilot availability target defined after infrastructure review"],
        ["Standard", "Department availability target defined after infrastructure review"],
        ["Enterprise", "HA/SLA target available only with agreed whole-bank HA architecture"],
    ]
    story.append(Spacer(1, 8))
    story.append(simple_table(["Package", "Availability Target"], sla_rows, [1.4 * inch, 5.1 * inch]))
    story.append(
        p(
            "Formal SLA commitments depend on final infrastructure, monitoring, backup and restore procedure, failover design, support terms, and successful operational drills. Availability excludes planned maintenance, bank network issues, force majeure, third-party internet disruption, and bank-side access problems.",
            STYLES["Small"],
        )
    )
    story.extend(heading("Capacity Posture", 2))
    capacity_rows = [
        ["Evidence Area", "Current Position"],
        ["Production profile", "Private text/analyst model route, open-source OCR, and optional separate vision/image route; final model mix and replicas depend on selected capacity."],
        ["Load evidence", "Current test-server evidence supports normal internal use patterns; whole-bank rollout requires bank-specific concurrency and document tests."],
        ["Large-file work", "Heavy OCR/PDF/XLS jobs use queues and worker capacity, not unlimited instant processing."],
    ]
    story.append(simple_table(["Area", "Position"], capacity_rows[1:], [1.45 * inch, 5.05 * inch]))

    page_break(story)
    story.extend(heading("13. Acceptance Criteria"))
    story.append(
        bullet_list(
            [
                "Sanima Bank can securely log in to the hosted environment.",
                "Admin users can create and manage bank users.",
                "Users can upload supported documents.",
                "Uploaded documents can be processed and queried.",
                "AI responses show source references where source documents are available.",
                "Role-based permissions work according to agreed configuration.",
                "Audit logs capture key user and system activity.",
                "Representative queued long-document analysis jobs complete successfully on agreed sample files.",
                "OCR Extraction can extract text from agreed sample files without indexing them into approved knowledge.",
                "Compliance Workspace can create a circular review and save an impact summary marked for officer review.",
                "Model Lab and RAG Evaluation Center are accessible to authorized roles for route visibility and evaluation evidence.",
                "Windows and macOS desktop access packages connect only to approved LipiCore hosted origins.",
                "Internal chat module supports direct messages, group/channel conversations, and administrative user control.",
                "Training has been completed.",
                "UAT issues classified as go-live blockers have been resolved or formally deferred.",
            ]
        )
    )

    story.extend(heading("14. Sanima Bank Responsibilities"))
    story.append(
        bullet_list(
            [
                "Nominate project owner and decision maker.",
                "Nominate technical/security contact.",
                "Provide user list and role matrix.",
                "Provide sample and initial production documents.",
                "Provide sample documents, compliance circulars, OCR samples, and evaluation questions for UAT.",
                "Nominate workflow owners for OCR Extraction, Compliance, Model Lab, and RAG Evaluation.",
                "Review configuration and UAT findings on time.",
                "Provide internal approvals for staff access and production use.",
                "Complete required compliance review and procurement approvals.",
                "Provide bank-owned domain/subdomain or access preference, if required.",
            ]
        )
    )

    page_break(story)
    story.extend(heading("15. Exclusions"))
    story.append(
        bullet_list(
            [
                "On-premise hardware procurement for Sanima Bank.",
                "Core banking system integration unless separately contracted.",
                "DMS, SharePoint, email, or intranet integration unless separately contracted.",
                "Custom AI model fine-tuning.",
                "Full document digitization or manual data cleanup.",
                "Large-scale historical document migration beyond included limits.",
                "Unlimited heavy OCR, PDF, or Excel processing without additional capacity sizing.",
                "Perfect OCR, handwriting, seal, signature, or complex-table verification.",
                "Automatic credit, risk, legal, regulatory, or customer decisions without authorized bank review.",
                "Using internal messenger messages as AI/RAG context unless separately scoped and approved in writing.",
                "Policy gap detection, maker-checker lending approval, regulatory filing automation, and audit export workflows beyond the implemented pilot scope unless separately contracted.",
                "A 50-case lending evaluation pack, full compliance evaluation pack, or OCR benchmark report unless included in final UAT scope.",
                "Legal, regulatory, or audit certification.",
                "Third-party VAPT charges.",
                "Bank-side network, device, or endpoint management.",
                "Custom workflows not listed in the agreed scope.",
            ]
        )
    )

    page_break(story)
    story.extend(heading("16. Assumptions"))
    story.append(
        bullet_list(
            [
                "Sanima Bank will use the hosted LipiCore environment operated by Lipi One Pvt. Ltd. and hosted through Silver Lining infrastructure.",
                "The selected package will be sized before final contract signing.",
                "Documents provided by Sanima Bank are legally permitted to be processed in the hosted environment.",
                "Sanima Bank will appoint users for UAT within the agreed project timeline.",
                "AI output is an assistance tool and does not replace authorized bank decision-making.",
                "Queued long-document analysis turnaround depends on document quality, OCR requirement, worker capacity, model queue load, and selected package sizing.",
                "OCR Extraction, Compliance Workspace, and Model Lab are staff-assistance and evaluation modules; final business interpretation remains with Sanima Bank.",
                "Model recommendations and stronger capacity claims require measured Sanima Bank workload evidence.",
                "Desktop software does not run the backend, database, vector database, object store, RAG pipeline, or model services locally.",
                "Sanima Bank will validate AI-assisted outputs before using them for final regulatory, credit, legal, or customer-facing decisions.",
            ]
        )
    )

    page_break(story)
    story.extend(heading("17. Change Management"))
    story.append(
        p(
            "Any work outside the agreed scope will be handled through a written change request. Each change request will include scope, effort, timeline, and commercial impact before execution.",
            STYLES["Body"],
        )
    )
    story.append(
        bullet_list(
            [
                "New modules or workflows.",
                "Additional integrations.",
                "Higher storage or AI capacity.",
                "Custom approval flows.",
                "New report formats.",
                "Additional training.",
                "Custom security architecture.",
            ]
        )
    )

    story.extend(heading("18. Termination and Exit"))
    story.append(
        bullet_list(
            [
                "Upon termination, subject to payment clearance and agreed data retention policies, Sanima Bank may request export of its documents and available system records.",
                "Lipi One Pvt. Ltd. will provide a reasonable data export in agreed format.",
                "Bank data will be deleted from active systems after the agreed retention period.",
                "Backup deletion will follow the backup retention schedule unless legally restricted.",
            ]
        )
    )

    story.extend(heading("19. Why LipiCore"))
    story.append(
        bullet_list(
            [
                "Banking-focused document intelligence workflows.",
                "Focused bank staff workflows for approved knowledge, OCR extraction, compliance support, long-document analysis, and model evaluation.",
                "Managed hosted model that separates hosting/server and software charges.",
                "Private model execution on controlled infrastructure.",
                "Document-grounded answers with source citations.",
                "Session and bank-level data isolation.",
                "Audit logs for governance.",
                "Lower operational burden for Sanima Bank compared with managing AI infrastructure internally.",
            ]
        )
    )

    page_break(story)
    story.extend(heading("20. Next Steps"))
    story.append(
        numbered_list(
            [
                "Sanima Bank reviews the proposal and selects preferred package.",
                "Lipi One Pvt. Ltd., Silver Lining, and Sanima Bank complete usage sizing.",
                "Commercial terms and final scope are confirmed.",
                "Purchase order or agreement is issued.",
                "Project kickoff is scheduled.",
                "Hosted environment is provisioned.",
                "UAT and training are completed.",
                "Production go-live begins.",
            ]
        )
    )

    page_break(story)
    story.extend(heading("Appendix A: Technical Overview"))
    tech_rows = [
        ["Desktop client", "LipiCore Desktop for Windows and macOS connected to hosted LipiCore services"],
        ["Backend", "Python FastAPI"],
        ["Database", "PostgreSQL"],
        ["Vector database", "Qdrant"],
        ["Object storage", "MinIO"],
        ["Queue/admission control", "Redis and RQ workers"],
        ["AI runtime", "vLLM/private model routes for text, analyst, long-document, and optional vision/image workloads where enabled; OCR text extraction uses open-source Tesseract"],
        ["Reverse proxy", "Nginx with TLS"],
        ["Retrieval", "Hybrid vector and keyword search with reranking and source verification"],
        ["Workspaces", "OCR Extraction, Compliance Workspace, Model Lab, and RAG Evaluation Center"],
        ["Messenger", "Separate internal chat service boundary; not part of AI/RAG context by default"],
    ]
    story.append(simple_table(["Component", "Technology"], tech_rows, [2.0 * inch, 4.5 * inch]))
    story.append(Spacer(1, 8))
    story.append(
        numbered_list(
            [
                "User uploads documents.",
                "Documents are stored securely.",
                "Text is extracted and divided into searchable chunks.",
                "Embeddings are created and stored in a vector database.",
                "User questions are matched against relevant document chunks.",
                "Hybrid retrieval and reranking prioritize relevant approved sources.",
                "The AI model generates a response using retrieved context.",
                "The response includes source references where applicable.",
                "Workflow modules store reviewable outputs, source ids where applicable, status, and audit metadata.",
                "Model Lab and RAG Evaluation Center provide evidence before route, model, or retrieval changes.",
                "User actions and responses are logged for audit.",
            ]
        )
    )

    page_break(story)
    story.extend(heading("Appendix B: Department Use Cases"))
    use_cases = [
        ["Credit", "Loan policy search, document summarization, open-question extraction"],
        ["Compliance", "Circular interpretation, impact summaries, obligation notes, review queue"],
        ["Operations", "SOP lookup, internal process guidance, OCR extraction for operational documents"],
        ["Risk", "Risk policy review, portfolio documentation analysis"],
        ["Legal", "Contract clause search, document comparison, regulatory reference lookup with review boundary"],
        ["Internal Audit", "Audit trail review, document evidence search, control testing support"],
        ["HR/Admin", "Policy FAQ, staff manual search, onboarding document support"],
    ]
    story.append(simple_table(["Department", "Example Use Cases"], use_cases, [1.45 * inch, 5.05 * inch]))

    return story


def draw_header_footer(canvas, doc):
    canvas.saveState()
    page = canvas.getPageNumber()
    width, height = letter

    if page == 1:
        canvas.restoreState()
        return

    canvas.setStrokeColor(BORDER)
    canvas.setLineWidth(0.5)
    canvas.line(MARGIN, height - 0.52 * inch, width - MARGIN, height - 0.52 * inch)
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawString(MARGIN, height - 0.42 * inch, "LipiCore Bank Staff AI Appliance")
    canvas.drawRightString(width - MARGIN, height - 0.42 * inch, "Proposal to Sanima Bank")

    canvas.setStrokeColor(BORDER)
    canvas.line(MARGIN, 0.52 * inch, width - MARGIN, 0.52 * inch)
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawString(MARGIN, 0.36 * inch, "Prepared by Lipi One Pvt. Ltd. | Hosting and server: Silver Lining")
    canvas.drawRightString(width - MARGIN, 0.36 * inch, f"Page {page}")

    canvas.restoreState()


def build_pdf():
    frame = Frame(MARGIN, 0.7 * inch, CONTENT_WIDTH, PAGE_HEIGHT - 1.4 * inch, id="normal")
    doc = BaseDocTemplate(
        str(PDF_PATH),
        pagesize=letter,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=0.72 * inch,
        bottomMargin=0.72 * inch,
        title="Proposal to Sanima Bank - LipiCore Bank Staff AI Appliance",
        author="Lipi One Pvt. Ltd.",
        subject="Managed hosted document intelligence platform proposal",
    )
    doc.addPageTemplates([PageTemplate(id="Proposal", frames=[frame], onPage=draw_header_footer)])
    doc.build(build_story())


if __name__ == "__main__":
    build_pdf()
    print(PDF_PATH)
