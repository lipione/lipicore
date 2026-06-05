from __future__ import annotations

import re
from html import escape as html_escape
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    Image as RLImage,
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
SOURCE_MD = ROOT / "lipicore-sanima-two-product-proposal.md"
PDF_PATH = ROOT / "Sanima_Bank_LipiCore_Two_Product_Proposal.pdf"
ASSETS_DIR = ROOT / "assets"
COMPANY_LOCKUP_LOGO_PATH = ASSETS_DIR / "lipi_company_lockup.png"
PRODUCT_LOCKUP_LOGO_PATH = ASSETS_DIR / "lipicore_lockup.png"

PAGE_WIDTH, PAGE_HEIGHT = letter
MARGIN_X = 0.68 * inch
MARGIN_TOP = 0.68 * inch
MARGIN_BOTTOM = 0.62 * inch
CONTENT_WIDTH = PAGE_WIDTH - (2 * MARGIN_X)

INK = colors.HexColor("#0B1C30")
MUTED = colors.HexColor("#526071")
BLUE = colors.HexColor("#0051D5")
DARK_BLUE = colors.HexColor("#13233D")
LIGHT_BLUE = colors.HexColor("#EAF2FF")
PALE = colors.HexColor("#F6F8FC")
BORDER = colors.HexColor("#D7DEE8")
GREEN = colors.HexColor("#007A55")
GOLD = colors.HexColor("#8A6500")


def build_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    styles: dict[str, ParagraphStyle] = {}

    def add(name: str, parent: str, **kwargs) -> None:
        styles[name] = ParagraphStyle(name, parent=base[parent], **kwargs)

    add(
        "CoverKicker",
        "Normal",
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=BLUE,
        alignment=TA_CENTER,
        spaceAfter=10,
    )
    add(
        "CoverTitle",
        "Title",
        fontName="Helvetica-Bold",
        fontSize=28,
        leading=33,
        textColor=INK,
        alignment=TA_CENTER,
        spaceAfter=9,
    )
    add(
        "CoverSubtitle",
        "Normal",
        fontName="Helvetica",
        fontSize=13,
        leading=18,
        textColor=MUTED,
        alignment=TA_CENTER,
        spaceAfter=16,
    )
    add(
        "Body",
        "Normal",
        fontName="Helvetica",
        fontSize=9.35,
        leading=12.8,
        textColor=INK,
        alignment=TA_JUSTIFY,
        spaceAfter=6,
    )
    styles["BodyLeft"] = ParagraphStyle("BodyLeft", parent=styles["Body"], alignment=TA_LEFT)
    add(
        "Small",
        "Normal",
        fontName="Helvetica",
        fontSize=7.7,
        leading=9.9,
        textColor=MUTED,
        alignment=TA_LEFT,
        spaceAfter=3,
    )
    add(
        "H1",
        "Heading1",
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=17,
        textColor=BLUE,
        spaceBefore=10,
        spaceAfter=6,
        keepWithNext=True,
    )
    add(
        "H2",
        "Heading2",
        fontName="Helvetica-Bold",
        fontSize=11.4,
        leading=14,
        textColor=DARK_BLUE,
        spaceBefore=7,
        spaceAfter=4,
        keepWithNext=True,
    )
    add(
        "H3",
        "Heading3",
        fontName="Helvetica-Bold",
        fontSize=10.1,
        leading=12.5,
        textColor=INK,
        spaceBefore=5,
        spaceAfter=3,
        keepWithNext=True,
    )
    add(
        "TableHead",
        "Normal",
        fontName="Helvetica-Bold",
        fontSize=7.25,
        leading=8.7,
        textColor=colors.white,
        alignment=TA_LEFT,
    )
    add(
        "TableCell",
        "Normal",
        fontName="Helvetica",
        fontSize=7.15,
        leading=8.8,
        textColor=INK,
        alignment=TA_LEFT,
    )
    add(
        "TableSmall",
        "Normal",
        fontName="Helvetica",
        fontSize=6.7,
        leading=8.2,
        textColor=INK,
        alignment=TA_LEFT,
    )
    add(
        "MetaCell",
        "Normal",
        fontName="Helvetica",
        fontSize=8.2,
        leading=10.4,
        textColor=INK,
        alignment=TA_LEFT,
    )
    add(
        "MetaLabel",
        "Normal",
        fontName="Helvetica-Bold",
        fontSize=8.0,
        leading=10.2,
        textColor=MUTED,
        alignment=TA_LEFT,
    )
    add(
        "Callout",
        "Normal",
        fontName="Helvetica",
        fontSize=8.65,
        leading=11.2,
        textColor=INK,
        alignment=TA_LEFT,
        spaceAfter=0,
    )
    return styles


STYLES = build_styles()


def inline_markup(text: str) -> str:
    escaped = html_escape(text.strip(), quote=False)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", escaped)
    escaped = re.sub(r"`(.+?)`", r"<font name=\"Courier\">\1</font>", escaped)
    return escaped


def para(text: str, style: ParagraphStyle = STYLES["Body"]) -> Paragraph:
    return Paragraph(inline_markup(text), style)


def logo_image(path: Path, width: float, h_align: str = "CENTER"):
    if not path.exists():
        return Spacer(1, 0)
    image = RLImage(str(path))
    ratio = image.imageHeight / float(image.imageWidth)
    image.drawWidth = width
    image.drawHeight = width * ratio
    image.hAlign = h_align
    return image


def table_widths(column_count: int) -> list[float]:
    width_map = {
        2: [1.95 * inch, 4.85 * inch],
        3: [1.35 * inch, 2.55 * inch, 2.90 * inch],
        4: [1.15 * inch, 1.45 * inch, 2.15 * inch, 2.05 * inch],
        5: [1.20 * inch, 1.05 * inch, 1.45 * inch, 1.65 * inch, 1.45 * inch],
        6: [1.30 * inch, 0.85 * inch, 1.02 * inch, 1.12 * inch, 1.43 * inch, 1.08 * inch],
    }
    if column_count in width_map:
        return width_map[column_count]
    return [CONTENT_WIDTH / column_count] * column_count


def make_table(rows: list[list[str]], has_header: bool = True) -> Table:
    col_count = max(len(row) for row in rows)
    widths = table_widths(col_count)
    if abs(sum(widths) - CONTENT_WIDTH) > 1:
        scale = CONTENT_WIDTH / sum(widths)
        widths = [w * scale for w in widths]

    compact = col_count >= 5 or len(rows) > 15
    cell_style = STYLES["TableSmall"] if compact else STYLES["TableCell"]
    converted = []
    for row_index, row in enumerate(rows):
        padded = row + [""] * (col_count - len(row))
        style = STYLES["TableHead"] if has_header and row_index == 0 else cell_style
        converted.append([Paragraph(inline_markup(cell), style) for cell in padded])

    table = Table(
        converted,
        colWidths=widths,
        repeatRows=1 if has_header else 0,
        hAlign="LEFT",
        splitByRow=1,
    )
    commands = [
        ("BOX", (0, 0), (-1, -1), 0.45, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    if has_header:
        commands.extend(
            [
                ("BACKGROUND", (0, 0), (-1, 0), DARK_BLUE),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ]
        )
    for row_index in range(1 if has_header else 0, len(rows)):
        if row_index % 2 == 0:
            commands.append(("BACKGROUND", (0, row_index), (-1, row_index), PALE))
    table.setStyle(TableStyle(commands))
    return table


def make_bullets(items: list[str]) -> ListFlowable:
    return ListFlowable(
        [ListItem(para(item, STYLES["BodyLeft"]), leftIndent=8) for item in items],
        bulletType="bullet",
        start="circle",
        leftIndent=15,
        bulletFontName="Helvetica",
        bulletFontSize=6,
        bulletDedent=8,
        spaceBefore=0,
        spaceAfter=5,
    )


def make_numbers(items: list[str]) -> ListFlowable:
    return ListFlowable(
        [ListItem(para(item, STYLES["BodyLeft"]), leftIndent=10) for item in items],
        bulletType="1",
        bulletFormat="%s.",
        leftIndent=17,
        bulletFontName="Helvetica",
        bulletFontSize=8,
        bulletDedent=8,
        spaceBefore=0,
        spaceAfter=5,
    )


def callout(title: str, text: str):
    body = Paragraph(f"<b>{inline_markup(title)}</b><br/>{inline_markup(text)}", STYLES["Callout"])
    box = Table([[body]], colWidths=[CONTENT_WIDTH], hAlign="LEFT")
    box.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BLUE),
                ("BOX", (0, 0), (-1, -1), 0.45, colors.HexColor("#BFD6FF")),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    return KeepTogether([box, Spacer(1, 7)])


def parse_table_line(line: str) -> list[str]:
    parts = line.strip().strip("|").split("|")
    return [part.strip() for part in parts]


def is_separator_row(line: str) -> bool:
    content = line.strip().strip("|").strip()
    if not content:
        return False
    cells = [cell.strip() for cell in content.split("|")]
    return all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)


def flush_paragraph(buffer: list[str], story: list) -> None:
    if buffer:
        story.append(para(" ".join(buffer)))
        buffer.clear()


def flush_list(items: list[str], story: list, numbered: bool = False) -> None:
    if items:
        story.append(make_numbers(items) if numbered else make_bullets(items))
        items.clear()


def markdown_to_story(markdown: str) -> list:
    lines = markdown.splitlines()
    story: list = []
    paragraph_buffer: list[str] = []
    bullet_items: list[str] = []
    number_items: list[str] = []
    table_rows: list[list[str]] = []
    seen_first_h1 = False

    def flush_table() -> None:
        nonlocal table_rows
        if table_rows:
            table_block = [make_table(table_rows), Spacer(1, 7)]
            if len(table_rows) <= 8:
                story.append(KeepTogether(table_block))
            else:
                story.extend(table_block)
            table_rows = []

    for raw_line in lines:
        line = raw_line.rstrip()

        if line.startswith("# "):
            continue

        if line.startswith("- **Prepared") or line.startswith("- **Company") or line.startswith("- **Infrastructure") or line.startswith("- **Product") or line.startswith("- **Proposal") or line.startswith("- **Commercial"):
            continue

        if line.strip() == "---":
            flush_paragraph(paragraph_buffer, story)
            flush_list(bullet_items, story)
            flush_list(number_items, story, numbered=True)
            flush_table()
            continue

        if line.startswith("|"):
            flush_paragraph(paragraph_buffer, story)
            flush_list(bullet_items, story)
            flush_list(number_items, story, numbered=True)
            if not is_separator_row(line):
                table_rows.append(parse_table_line(line))
            continue

        flush_table()

        if not line.strip():
            flush_paragraph(paragraph_buffer, story)
            flush_list(bullet_items, story)
            flush_list(number_items, story, numbered=True)
            continue

        if line.strip() == "Key tradeoffs:" and story:
            flush_paragraph(paragraph_buffer, story)
            flush_list(bullet_items, story)
            flush_list(number_items, story, numbered=True)
            story.append(PageBreak())
            paragraph_buffer.append(line.strip())
            continue

        heading_match = re.match(r"^(#{2,4})\s+(.+)$", line)
        if heading_match:
            flush_paragraph(paragraph_buffer, story)
            flush_list(bullet_items, story)
            flush_list(number_items, story, numbered=True)
            level = len(heading_match.group(1))
            title = heading_match.group(2).strip()
            if title.startswith("10.6 Market Comparison") and story:
                story.append(PageBreak())
            if level == 2 and seen_first_h1 and re.match(r"^\d+\.\s+", title):
                story.append(Spacer(1, 4))
            if level == 2:
                seen_first_h1 = True
            style = {2: STYLES["H1"], 3: STYLES["H2"], 4: STYLES["H3"]}.get(level, STYLES["H3"])
            story.append(Paragraph(inline_markup(title), style))
            continue

        bullet_match = re.match(r"^-\s+(.+)$", line)
        if bullet_match:
            flush_paragraph(paragraph_buffer, story)
            flush_list(number_items, story, numbered=True)
            bullet_items.append(bullet_match.group(1).strip())
            continue

        number_match = re.match(r"^\d+\.\s+(.+)$", line)
        if number_match:
            flush_paragraph(paragraph_buffer, story)
            flush_list(bullet_items, story)
            number_items.append(number_match.group(1).strip())
            continue

        flush_list(bullet_items, story)
        flush_list(number_items, story, numbered=True)
        paragraph_buffer.append(line.strip())

    flush_paragraph(paragraph_buffer, story)
    flush_list(bullet_items, story)
    flush_list(number_items, story, numbered=True)
    flush_table()
    return story


def meta_table() -> Table:
    left = [
        ["Prepared for", "Sanima Bank Limited"],
        ["Prepared by", "Lipi One Pvt. Ltd."],
        ["Website", "www.lipi.one"],
        ["Infrastructure partner", "Silver Lining Pvt. Ltd."],
    ]
    right = [
        ["Product", "LipiCore powered by LipiLLM"],
        ["Proposal date", "June 5, 2026"],
        ["Commercial model", "One-time setup + monthly infrastructure + monthly software subscription"],
        ["Validity", "30 days from proposal date"],
    ]

    def small_table(rows):
        data = [[Paragraph(inline_markup(k), STYLES["MetaLabel"]), Paragraph(inline_markup(v), STYLES["MetaCell"])] for k, v in rows]
        table = Table(data, colWidths=[1.25 * inch, 2.05 * inch], hAlign="LEFT")
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

    wrapper = Table([[small_table(left), small_table(right)]], colWidths=[3.35 * inch, 3.35 * inch], hAlign="CENTER")
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


def cover_page() -> list:
    return [
        Spacer(1, 0.22 * inch),
        Table(
            [[logo_image(COMPANY_LOCKUP_LOGO_PATH, 1.55 * inch), logo_image(PRODUCT_LOCKUP_LOGO_PATH, 2.0 * inch)]],
            colWidths=[CONTENT_WIDTH / 2, CONTENT_WIDTH / 2],
            hAlign="CENTER",
            style=TableStyle(
                [
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ]
            ),
        ),
        Spacer(1, 0.26 * inch),
        Paragraph("CONFIDENTIAL COMMERCIAL PROPOSAL", STYLES["CoverKicker"]),
        Paragraph("LipiCore Proposal for Sanima Bank Limited", STYLES["CoverTitle"]),
        Paragraph("Private Institutional Knowledge and Document Intelligence Platform", STYLES["CoverSubtitle"]),
        HRFlowable(width="64%", thickness=1.1, color=BLUE, spaceBefore=2, spaceAfter=18, hAlign="CENTER"),
        meta_table(),
        Spacer(1, 0.35 * inch),
        callout(
            "Proposal structure",
            "This proposal separates LipiCore into two products: LipiCore Policy Assistant for lower-cost policy retrieval and staff assistance, and LipiCore Enterprise Intelligence for the full analyst/deep model and document intelligence platform.",
        ),
        Spacer(1, 0.12 * inch),
        Paragraph(
            "Sanima Bank documents remain within the approved managed hosted environment. They are not used to train public AI models or fine-tune LipiLLM unless separately approved in writing.",
            STYLES["Small"],
        ),
        PageBreak(),
    ]


def draw_page_frame(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(BORDER)
    canvas.setLineWidth(0.4)
    canvas.line(MARGIN_X, PAGE_HEIGHT - 0.46 * inch, PAGE_WIDTH - MARGIN_X, PAGE_HEIGHT - 0.46 * inch)
    canvas.setFont("Helvetica", 7.3)
    canvas.setFillColor(MUTED)
    canvas.drawString(MARGIN_X, PAGE_HEIGHT - 0.35 * inch, "LipiCore Proposal for Sanima Bank Limited")
    canvas.drawRightString(PAGE_WIDTH - MARGIN_X, 0.35 * inch, f"Page {doc.page}")
    canvas.drawString(MARGIN_X, 0.35 * inch, "Lipi One Pvt. Ltd. | www.lipi.one")
    canvas.restoreState()


def build_pdf() -> None:
    markdown = SOURCE_MD.read_text(encoding="utf-8")
    story = cover_page()
    story.extend(markdown_to_story(markdown))

    doc = BaseDocTemplate(
        str(PDF_PATH),
        pagesize=letter,
        rightMargin=MARGIN_X,
        leftMargin=MARGIN_X,
        topMargin=MARGIN_TOP,
        bottomMargin=MARGIN_BOTTOM,
        title="LipiCore Proposal for Sanima Bank Limited",
        author="Lipi One Pvt. Ltd.",
        subject="LipiCore Policy Assistant and Enterprise Intelligence Proposal",
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
