from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from build_sanima_two_product_proposal_pdf import (
    BORDER,
    BLUE,
    COMPANY_LOCKUP_LOGO_PATH,
    CONTENT_WIDTH,
    DARK_BLUE,
    MARGIN_BOTTOM,
    MARGIN_TOP,
    MARGIN_X,
    MUTED,
    PALE,
    PRODUCT_LOCKUP_LOGO_PATH,
    STYLES,
    callout,
    draw_page_frame,
    inline_markup,
    logo_image,
    markdown_to_story,
)


ROOT = Path(__file__).resolve().parent
SOURCE_MD = ROOT / "lipicore-sanima-policy-chat-simple-proposal.md"
PDF_PATH = ROOT / "Sanima_Bank_LipiCore_Policy_Assistant_Phase_1_Proposal.pdf"
PAGE_WIDTH, PAGE_HEIGHT = letter
LIGHT_GREEN = colors.HexColor("#EAF8F1")
GREEN = colors.HexColor("#057A55")


def paragraph(text: str, style_name: str = "BodyLeft") -> Paragraph:
    return Paragraph(inline_markup(text), STYLES[style_name])


def small_meta_table(rows: list[list[str]]) -> Table:
    data = [
        [
            Paragraph(inline_markup(label), STYLES["MetaLabel"]),
            Paragraph(inline_markup(value), STYLES["MetaCell"]),
        ]
        for label, value in rows
    ]
    table = Table(data, colWidths=[1.26 * inch, 2.02 * inch], hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.45, BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, BORDER),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("BACKGROUND", (0, 0), (0, -1), PALE),
            ]
        )
    )
    return table


def meta_table() -> Table:
    left = [
        ["Prepared for", "Sanima Bank Limited"],
        ["Prepared by", "Lipi One Pvt. Ltd."],
        ["Website", "www.lipi.one"],
        ["Infrastructure", "Silver Lining Pvt. Ltd."],
    ]
    right = [
        ["Product", "LipiCore Policy Assistant"],
        ["Model layer", "LipiLLM"],
        ["Offer", "Policy retrieval + internal chat"],
        ["Monthly price", "NPR 250,000 + VAT"],
    ]
    wrapper = Table(
        [[small_meta_table(left), small_meta_table(right)]],
        colWidths=[CONTENT_WIDTH / 2, CONTENT_WIDTH / 2],
        hAlign="CENTER",
    )
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
    return wrapper


def at_a_glance_table() -> Table:
    rows = [
        ["Phase 1 focus", "Advanced policy retrieval and internal staff chat"],
        ["Monthly price", "NPR 250,000 per month + VAT"],
        ["Access", "Windows and macOS desktop software connected to managed hosted environment"],
        ["Included RAG", "Natural English/Nepali questions, hybrid retrieval, source passages, page/heading/clause references where available"],
        ["Included chat", "Direct messages, department channels, groups, announcements, file/image sharing subject to policy"],
        ["Future upgrades", "OCR-heavy workflows, compliance automation, integrations, long-document analytics, advanced reports"],
    ]
    data = [
        [
            Paragraph(inline_markup(label), STYLES["MetaLabel"]),
            Paragraph(inline_markup(value), STYLES["MetaCell"]),
        ]
        for label, value in rows
    ]
    table = Table(data, colWidths=[1.65 * inch, CONTENT_WIDTH - 1.65 * inch], hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.65, colors.HexColor("#BFD6FF")),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#DDE9FF")),
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F7FAFF")),
                ("BACKGROUND", (0, 1), (-1, 1), LIGHT_GREEN),
                ("TEXTCOLOR", (0, 1), (-1, 1), GREEN),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


def cover_page() -> list:
    logo_row = Table(
        [[logo_image(COMPANY_LOCKUP_LOGO_PATH, 1.55 * inch), logo_image(PRODUCT_LOCKUP_LOGO_PATH, 2.0 * inch)]],
        colWidths=[CONTENT_WIDTH / 2, CONTENT_WIDTH / 2],
        hAlign="CENTER",
    )
    logo_row.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    return [
        Spacer(1, 0.28 * inch),
        logo_row,
        Spacer(1, 0.28 * inch),
        Paragraph("SIMPLIFIED PHASE 1 PROPOSAL", STYLES["CoverKicker"]),
        Paragraph("LipiCore Policy Assistant", STYLES["CoverTitle"]),
        Paragraph("Advanced Policy Retrieval and Internal Chat for Sanima Bank", STYLES["CoverSubtitle"]),
        HRFlowable(width="62%", thickness=1.1, color=BLUE, spaceBefore=2, spaceAfter=18, hAlign="CENTER"),
        meta_table(),
        Spacer(1, 0.30 * inch),
        callout(
            "Simple onboarding package",
            "This proposal keeps Phase 1 focused on the practical starting point: approved-document policy retrieval with strong RAG citations, plus internal staff chat. Advanced enterprise modules are listed only as future upgrades.",
        ),
        Spacer(1, 0.10 * inch),
        KeepTogether(
            [
                Paragraph("At a Glance", STYLES["H2"]),
                at_a_glance_table(),
            ]
        ),
        Spacer(1, 0.12 * inch),
        Paragraph(
            inline_markup(
                "Prepared by Lipi One Pvt. Ltd. | Proposal date: June 5, 2026 | Data is not used to train public AI models or fine-tune LipiLLM unless separately approved in writing."
            ),
            STYLES["Small"],
        ),
        PageBreak(),
    ]


def transform_markdown(markdown: str) -> str:
    # The cover already carries the title, metadata, and offer summary.
    lines = []
    page_break_before = {
        "## 4. Deployment Model",
        "## 5. Security and Governance",
        "## 6. Phase 1 Implementation Scope",
        "## 7. Commercial Offer",
        "## 8. Implementation Timeline",
        "## 10. Future Upgrade Path",
        "## 8. Next Steps",
    }
    for line in markdown.splitlines():
        if line.startswith("# "):
            continue
        if line.startswith("## Phase 1:"):
            continue
        if (
            line.startswith("- **Prepared")
            or line.startswith("- **Company")
            or line.startswith("- **Website")
            or line.startswith("- **Infrastructure")
            or line.startswith("- **Product")
            or line.startswith("- **Proposal")
            or line.startswith("- **Commercial")
            or line.startswith("- **Date")
            or line.startswith("- **Offer")
        ):
            continue
        if line in page_break_before:
            lines.append("<!-- PAGE_BREAK -->")
        lines.append(line)
    return "\n".join(lines)


def build_pdf() -> None:
    markdown = transform_markdown(SOURCE_MD.read_text(encoding="utf-8"))
    story = cover_page()
    for index, section in enumerate(markdown.split("<!-- PAGE_BREAK -->")):
        if index > 0 and story and not isinstance(story[-1], PageBreak):
            story.append(PageBreak())
        story.extend(markdown_to_story(section.strip()))

    doc = BaseDocTemplate(
        str(PDF_PATH),
        pagesize=letter,
        rightMargin=MARGIN_X,
        leftMargin=MARGIN_X,
        topMargin=MARGIN_TOP,
        bottomMargin=MARGIN_BOTTOM,
        title="LipiCore Policy Assistant Phase 1 Proposal for Sanima Bank",
        author="Lipi One Pvt. Ltd.",
        subject="Advanced policy retrieval and internal chat proposal",
    )
    frame = Frame(
        MARGIN_X,
        MARGIN_BOTTOM + 0.16 * inch,
        CONTENT_WIDTH,
        PAGE_HEIGHT - MARGIN_TOP - MARGIN_BOTTOM - 0.26 * inch,
        id="normal",
    )
    doc.addPageTemplates([PageTemplate(id="main", frames=[frame], onPage=draw_page_frame)])
    doc.build(story)


if __name__ == "__main__":
    build_pdf()
    print(PDF_PATH)
