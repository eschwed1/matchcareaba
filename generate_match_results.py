"""
Match Care ABA — Match Results PDF Generator
Generates a professional branded PDF: match-results-template.pdf
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer,
    Table, TableStyle, Image, HRFlowable, KeepTogether
)
from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing, Rect, String, Circle
from reportlab.graphics import renderPDF
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
import datetime

# ─── Brand Colors ────────────────────────────────────────────────────────────
NAVY        = colors.HexColor("#1B3A6B")
NAVY_MID    = colors.HexColor("#2A5298")
GOLD        = colors.HexColor("#D4A843")
GOLD_LIGHT  = colors.HexColor("#F5E6C0")
SKY         = colors.HexColor("#EEF6FF")
WHITE       = colors.white
LIGHT_GRAY  = colors.HexColor("#F5F7FA")
MID_GRAY    = colors.HexColor("#8898A8")
DARK_TEXT   = colors.HexColor("#1A2B3C")
GREEN_CHECK = colors.HexColor("#27AE60")

PAGE_W, PAGE_H = letter
MARGIN = 0.65 * inch
CONTENT_W = PAGE_W - 2 * MARGIN

LOGO_PATH = os.path.join(os.path.dirname(__file__), "logo.jpeg")

# ═══════════════════════════════════════════════════════════════════════════════
# FILL IN THESE VARIABLES FOR EACH FAMILY — then run the script
# ═══════════════════════════════════════════════════════════════════════════════

NUMBER_OF_PROVIDERS = 3  # Set to 1, 2, or 3 to control how many providers appear in the PDF

FAMILY_NAME = "jones"
REPORT_DATE = datetime.date.today().strftime("%B %d, %Y")

# ── Provider 1 ────────────────────────────────────────────────────────────────
PROVIDER_1_NAME         = "ashford"
PROVIDER_1_ADDRESS      = "sunny lane"
PROVIDER_1_DISTANCE     = "1 mile"
PROVIDER_1_INSURANCE    = "Accepts medicaid"
PROVIDER_1_SETTING      = ""
PROVIDER_1_AVAILABILITY = ""
PROVIDER_1_NOTE         = ""

# ── Provider 2 ────────────────────────────────────────────────────────────────
PROVIDER_2_NAME         = "cbcbc"
PROVIDER_2_ADDRESS      = ""
PROVIDER_2_DISTANCE     = ""
PROVIDER_2_INSURANCE    = ""
PROVIDER_2_SETTING      = "clinic"
PROVIDER_2_AVAILABILITY = ""
PROVIDER_2_NOTE         = ""

# ── Provider 3 ────────────────────────────────────────────────────────────────
PROVIDER_3_NAME         = "sashes"
PROVIDER_3_ADDRESS      = ""
PROVIDER_3_DISTANCE     = ""
PROVIDER_3_INSURANCE    = ""
PROVIDER_3_SETTING      = ""
PROVIDER_3_AVAILABILITY = "now"
PROVIDER_3_NOTE         = ""

# ═══════════════════════════════════════════════════════════════════════════════

PROVIDERS = [
    {
        "name":         PROVIDER_1_NAME,
        "address":      PROVIDER_1_ADDRESS,
        "distance":     PROVIDER_1_DISTANCE,
        "insurance":    PROVIDER_1_INSURANCE,
        "setting":      PROVIDER_1_SETTING,
        "availability": PROVIDER_1_AVAILABILITY,
        "note":         PROVIDER_1_NOTE,
    },
    {
        "name":         PROVIDER_2_NAME,
        "address":      PROVIDER_2_ADDRESS,
        "distance":     PROVIDER_2_DISTANCE,
        "insurance":    PROVIDER_2_INSURANCE,
        "setting":      PROVIDER_2_SETTING,
        "availability": PROVIDER_2_AVAILABILITY,
        "note":         PROVIDER_2_NOTE,
    },
    {
        "name":         PROVIDER_3_NAME,
        "address":      PROVIDER_3_ADDRESS,
        "distance":     PROVIDER_3_DISTANCE,
        "insurance":    PROVIDER_3_INSURANCE,
        "setting":      PROVIDER_3_SETTING,
        "availability": PROVIDER_3_AVAILABILITY,
        "note":         PROVIDER_3_NOTE,
    },
]

# ─── Page Canvas Decorator ────────────────────────────────────────────────────

def draw_page(canv: canvas.Canvas, doc):
    """Draws the header band and footer on every page."""
    canv.saveState()

    # ── Top header band ──────────────────────────────────────────────
    band_h = 0.85 * inch
    canv.setFillColor(NAVY)
    canv.rect(0, PAGE_H - band_h, PAGE_W, band_h, fill=1, stroke=0)

    # Gold accent stripe at very top
    canv.setFillColor(GOLD)
    canv.rect(0, PAGE_H - 4, PAGE_W, 4, fill=1, stroke=0)

    # Logo in header (if available)
    logo_w, logo_h = 1.1 * inch, 0.55 * inch
    logo_x = MARGIN
    logo_y = PAGE_H - band_h + (band_h - logo_h) / 2
    if os.path.exists(LOGO_PATH):
        canv.drawImage(
            LOGO_PATH, logo_x, logo_y,
            width=logo_w, height=logo_h,
            preserveAspectRatio=True, mask="auto"
        )

    # Header right text
    canv.setFillColor(WHITE)
    canv.setFont("Helvetica-Bold", 9)
    canv.drawRightString(PAGE_W - MARGIN, PAGE_H - 0.33 * inch, "Match Results Report")
    canv.setFont("Helvetica", 8)
    canv.setFillColor(GOLD)
    canv.drawRightString(PAGE_W - MARGIN, PAGE_H - 0.52 * inch, "matchcareaba.com")

    # Page number (right side footer area)
    canv.setFillColor(MID_GRAY)
    canv.setFont("Helvetica", 7.5)
    canv.drawRightString(PAGE_W - MARGIN, 0.38 * inch, f"Page {doc.page}")

    # ── Footer band ───────────────────────────────────────────────────
    footer_h = 0.65 * inch
    canv.setFillColor(NAVY)
    canv.rect(0, 0, PAGE_W, footer_h, fill=1, stroke=0)

    # Gold accent at bottom of footer
    canv.setFillColor(GOLD)
    canv.rect(0, footer_h, PAGE_W, 2, fill=1, stroke=0)

    # Footer logo
    if os.path.exists(LOGO_PATH):
        flogo_w, flogo_h = 0.75 * inch, 0.38 * inch
        canv.drawImage(
            LOGO_PATH, MARGIN, (footer_h - flogo_h) / 2,
            width=flogo_w, height=flogo_h,
            preserveAspectRatio=True, mask="auto"
        )

    # Footer text center
    canv.setFillColor(colors.HexColor("#C8D8ED"))
    canv.setFont("Helvetica", 7)
    center_x = PAGE_W / 2
    canv.drawCentredString(
        center_x, 0.28 * inch,
        "This match was prepared exclusively for your family. All information is confidential."
    )
    canv.setFillColor(WHITE)
    canv.setFont("Helvetica-Bold", 7.5)
    canv.drawCentredString(center_x, 0.44 * inch, "matchcareaba.com")

    canv.restoreState()


# ─── Paragraph Styles ─────────────────────────────────────────────────────────

def make_styles():
    styles = getSampleStyleSheet()

    base = dict(fontName="Helvetica", leading=14, textColor=DARK_TEXT)

    s = {}

    s["title"] = ParagraphStyle(
        "title",
        fontName="Helvetica-Bold", fontSize=22,
        textColor=NAVY, leading=28, alignment=TA_CENTER,
        spaceAfter=4,
    )
    s["subtitle"] = ParagraphStyle(
        "subtitle",
        fontName="Helvetica", fontSize=12,
        textColor=NAVY_MID, leading=16, alignment=TA_CENTER,
        spaceAfter=2,
    )
    s["date_line"] = ParagraphStyle(
        "date_line",
        fontName="Helvetica", fontSize=9,
        textColor=DARK_TEXT, leading=13, alignment=TA_CENTER,
        spaceAfter=0,
    )
    s["intro"] = ParagraphStyle(
        "intro",
        fontName="Helvetica", fontSize=10.5,
        textColor=DARK_TEXT, leading=16, alignment=TA_LEFT,
        spaceAfter=4,
    )
    s["provider_name"] = ParagraphStyle(
        "provider_name",
        fontName="Helvetica-Bold", fontSize=13,
        textColor=NAVY, leading=17, spaceAfter=2,
    )
    s["card_label"] = ParagraphStyle(
        "card_label",
        fontName="Helvetica-Bold", fontSize=7.5,
        textColor=MID_GRAY, leading=10, spaceAfter=1,
        spaceBefore=5,
    )
    s["card_value"] = ParagraphStyle(
        "card_value",
        fontName="Helvetica", fontSize=9.5,
        textColor=DARK_TEXT, leading=13, spaceAfter=0,
    )
    s["card_note_label"] = ParagraphStyle(
        "card_note_label",
        fontName="Helvetica-Bold", fontSize=7.5,
        textColor=GOLD, leading=10, spaceAfter=1,
        spaceBefore=6,
    )
    s["card_note"] = ParagraphStyle(
        "card_note",
        fontName="Helvetica-Oblique", fontSize=9,
        textColor=colors.HexColor("#3A4E63"), leading=13, spaceAfter=0,
    )
    s["section_header"] = ParagraphStyle(
        "section_header",
        fontName="Helvetica-Bold", fontSize=11,
        textColor=NAVY, leading=14, spaceAfter=6, spaceBefore=4,
    )
    s["footer_note"] = ParagraphStyle(
        "footer_note",
        fontName="Helvetica-Oblique", fontSize=8,
        textColor=MID_GRAY, leading=12, alignment=TA_CENTER,
        spaceAfter=0,
    )

    return s


# ─── Provider Card Builder ────────────────────────────────────────────────────

def build_provider_card(provider: dict, match_num: int, styles: dict):
    """Returns a KeepTogether flowable for one provider card."""

    # ── Gold badge circle drawn via a small Drawing ───────────────────
    badge_size = 38
    badge_drawing = Drawing(badge_size, badge_size)
    badge_drawing.add(Circle(badge_size / 2, badge_size / 2, badge_size / 2 - 1,
                             fillColor=GOLD, strokeColor=GOLD))
    badge_drawing.add(String(badge_size / 2, badge_size / 2 - 5,
                             str(match_num),
                             fontSize=16, fontName="Helvetica-Bold",
                             fillColor=WHITE, textAnchor="middle"))

    badge_label = Paragraph(f"MATCH #{match_num}", ParagraphStyle(
        "badge_lbl", fontName="Helvetica-Bold", fontSize=7,
        textColor=GOLD, leading=9,
    ))

    # ── Card content rows ─────────────────────────────────────────────
    def lbl(text):
        return Paragraph(text.upper(), styles["card_label"])

    def val(text):
        return Paragraph(text, styles["card_value"])

    def checkmark_val(text):
        return Paragraph(text, styles["card_value"])

    card_rows = [
        # Badge row
        [badge_drawing,
         Paragraph(provider["name"], styles["provider_name"])],
    ]

    # Info table inside the card
    info_data = [
        [lbl("Address"),    val(provider["address"])],
        [lbl("Distance"),   val(provider["distance"])],
        [lbl("Insurance"),  checkmark_val(provider["insurance"])],
        [lbl("Setting"),    val(provider["setting"])],
        [lbl("Availability"), val(provider["availability"])],
    ]
    if provider["note"]:
        info_data.append([
            Paragraph("PROVIDER NOTE", styles["card_note_label"]),
            Paragraph(provider["note"], styles["card_note"]),
        ])

    info_table = Table(info_data, colWidths=[1.05 * inch, CONTENT_W - 1.2 * inch])
    info_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        # Light separator lines between rows
        ("LINEBELOW", (0, 0), (-1, -2), 0.3, colors.HexColor("#DDE6EF")),
    ]))

    # Header row of the card (badge + name)
    header_table = Table(
        [[badge_drawing, Paragraph(provider["name"], styles["provider_name"])]],
        colWidths=[badge_size + 10, CONTENT_W - badge_size - 10]
    )
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))

    # Outer card table (gives us the background + border)
    card_inner = [
        [header_table],
        [HRFlowable(width="100%", thickness=1.5, color=GOLD, spaceAfter=6)],
        [info_table],
    ]
    inner_table = Table(card_inner, colWidths=[CONTENT_W - 0.4 * inch])
    inner_table.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))

    outer_table = Table([[inner_table]], colWidths=[CONTENT_W])
    outer_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), WHITE),
        ("BOX", (0, 0), (-1, -1), 1.2, colors.HexColor("#C8D8ED")),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("TOPPADDING", (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
        # Left accent bar color (simulate with thick left border in GOLD)
        ("LINEBEFORE", (0, 0), (0, -1), 5, GOLD),
    ]))

    return KeepTogether([outer_table, Spacer(1, 0.18 * inch)])


# ─── Intro Hero Box ───────────────────────────────────────────────────────────

def build_intro_box(family_name: str, date: str, styles: dict):
    intro_text = (
        "Based on your child's profile, we've identified the following providers "
        "that match your insurance, location, and availability needs. Each match "
        "has been carefully reviewed by our team to ensure they meet our quality "
        "standards for care, communication, and family experience."
    )

    title_para     = Paragraph("Your ABA Therapy Match Results", styles["title"])
    subtitle_para  = Paragraph(f"Prepared exclusively for <b>{family_name}</b>", styles["subtitle"])
    date_para      = Paragraph(f"Report Date: {date}", styles["date_line"])
    divider        = HRFlowable(width="100%", thickness=1.5, color=GOLD,
                                spaceAfter=10, spaceBefore=10,
                                hAlign="CENTER")
    intro_para     = Paragraph(intro_text, styles["intro"])

    box_content = [
        [title_para],
        [subtitle_para],
        [date_para],
        [divider],
        [intro_para],
    ]

    box_table = Table(box_content, colWidths=[CONTENT_W - 0.5 * inch])
    box_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), SKY),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#C8D8ED")),
        ("LINEBEFORE", (0, 0), (0, -1), 5, NAVY_MID),
        ("LEFTPADDING", (0, 0), (-1, -1), 20),
        ("RIGHTPADDING", (0, 0), (-1, -1), 20),
        ("TOPPADDING", (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("ALIGN", (0, 0), (-1, 2), "CENTER"),
        ("ALIGN", (0, 3), (-1, -1), "LEFT"),
    ]))

    outer = Table([[box_table]], colWidths=[CONTENT_W])
    outer.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))

    return KeepTogether([outer, Spacer(1, 0.22 * inch)])


# ─── Section Divider ─────────────────────────────────────────────────────────

def section_divider(label: str, styles: dict):
    data = [[Paragraph(label, ParagraphStyle(
        "sec_div", fontName="Helvetica-Bold", fontSize=10,
        textColor=WHITE, leading=13,
    ))]]
    t = Table(data, colWidths=[CONTENT_W])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LINEBEFORE", (0, 0), (0, -1), 5, GOLD),
    ]))
    return KeepTogether([t, Spacer(1, 0.14 * inch)])


# ─── Next Steps Box ───────────────────────────────────────────────────────────

def build_next_steps(styles: dict):
    steps = [
        ("1", "Review each provider profile and note any questions you have."),
        ("2", "Call or email your top choice to schedule a free intake call."),
        ("3", "Have your child's insurance card and diagnosis paperwork ready."),
        ("4", "Contact us at <b>matchcareaba@gmail.com</b> if you need additional matches "
              "or have any questions — we're here to help."),
    ]

    step_rows = []
    for num, text in steps:
        step_rows.append([
            Paragraph(num, ParagraphStyle(
                "step_num", fontName="Helvetica-Bold", fontSize=11,
                textColor=WHITE, leading=14, alignment=TA_CENTER,
            )),
            Paragraph(text, ParagraphStyle(
                "step_text", fontName="Helvetica", fontSize=9.5,
                textColor=DARK_TEXT, leading=14,
            )),
        ])

    badge_col = 0.32 * inch
    TEXT_GAP = 8  # pt gap between number box and text
    # 12pt left + 12pt right padding inside outer box must be subtracted
    text_col = CONTENT_W - 0.4 * inch - 2 * 12 - badge_col - TEXT_GAP
    steps_table = Table(step_rows, colWidths=[badge_col, text_col])
    step_styles = [
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("LEFTPADDING", (1, 0), (1, -1), TEXT_GAP),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("LINEBELOW", (0, 0), (-1, -2), 0.4, colors.HexColor("#DDE6EF")),
    ]
    for i in range(len(steps)):
        step_styles.append(("BACKGROUND", (0, i), (0, i), NAVY_MID))

    steps_table.setStyle(TableStyle(step_styles))

    outer_data = [[steps_table]]
    outer = Table(outer_data, colWidths=[CONTENT_W - 0.4 * inch])
    outer.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), GOLD_LIGHT),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#C8B06A")),
        ("LINEBEFORE", (0, 0), (0, -1), 5, GOLD),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
    ]))

    wrapper = Table([[outer]], colWidths=[CONTENT_W])
    wrapper.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))

    return KeepTogether([wrapper, Spacer(1, 0.15 * inch)])


# ─── Confidentiality Footer Note ─────────────────────────────────────────────

def build_confidentiality_note(styles: dict):
    note = Paragraph(
        "This report was generated by Match Care ABA and is intended solely for the family named above. "
        "Provider availability and insurance acceptance are subject to change. Please confirm details "
        "directly with each provider. Match Care ABA does not share your personal information with "
        "providers without your explicit consent.",
        styles["footer_note"]
    )
    data = [[note]]
    t = Table(data, colWidths=[CONTENT_W])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_GRAY),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5DF")),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    return t


# ─── Main Build Function ──────────────────────────────────────────────────────

def build_pdf(output_path: str):
    styles = make_styles()

    # Frame that sits between header and footer
    top_margin    = 0.85 * inch + 0.25 * inch   # header band + breathing room
    bottom_margin = 0.65 * inch + 0.25 * inch   # footer band + breathing room

    frame = Frame(
        MARGIN, bottom_margin,
        CONTENT_W, PAGE_H - top_margin - bottom_margin,
        leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
        id="main"
    )

    doc = BaseDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=top_margin, bottomMargin=bottom_margin,
        title="Match Care ABA — Match Results",
        author="Match Care ABA",
        subject=f"ABA Therapy Match Results for {FAMILY_NAME}",
        creator="Match Care ABA (matchcareaba.com)",
    )

    page_template = PageTemplate(
        id="main_page",
        frames=[frame],
        onPage=draw_page,
    )
    doc.addPageTemplates([page_template])

    # ── Story ──────────────────────────────────────────────────────────
    story = []

    story.append(Spacer(1, 0.1 * inch))

    # Intro hero box
    story.append(build_intro_box(FAMILY_NAME, REPORT_DATE, styles))

    # Provider matches section
    story.append(section_divider("Your Provider Matches", styles))

    for i, provider in enumerate(PROVIDERS[:NUMBER_OF_PROVIDERS], start=1):
        story.append(build_provider_card(provider, i, styles))

    # Next steps
    story.append(section_divider("Your Next Steps", styles))
    story.append(build_next_steps(styles))

    # Confidentiality note
    story.append(build_confidentiality_note(styles))

    doc.build(story)
    print(f"✓ PDF generated: {output_path}")


if __name__ == "__main__":
    out = os.path.join(os.path.dirname(__file__), "match-results-template.pdf")
    build_pdf(out)
