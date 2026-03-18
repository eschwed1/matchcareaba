#!/usr/bin/env python3
"""Generate the Match Care ABA autism diagnosis guide PDF."""

import qrcode
import io
import os
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak,
    HRFlowable, KeepTogether, Table, TableStyle, Image, Flowable
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.pdfgen import canvas as pdfcanvas
from PIL import Image as PILImage

# ── Brand Colors ──────────────────────────────────────────────────────────────
NAVY        = HexColor('#1B3A6B')
NAVY_MID    = HexColor('#2A5298')
GOLD        = HexColor('#D4A843')
GOLD_LIGHT  = HexColor('#F5C842')
SKY         = HexColor('#EEF6FF')
LIGHT_GRAY  = HexColor('#F8F9FA')
MEDIUM_GRAY = HexColor('#6B7280')
DARK_TEXT   = HexColor('#1F2937')
WARM_WHITE  = HexColor('#FAFAFA')
NAVY_DARK   = HexColor('#0F2347')

PAGE_W, PAGE_H = letter
MARGIN = 0.75 * inch
CONTENT_W = PAGE_W - 2 * MARGIN

LOGO_PATH = os.path.join(os.path.dirname(__file__), 'logo.jpeg')

# ── QR Code ───────────────────────────────────────────────────────────────────
def make_qr_image(url: str, size_px: int = 300) -> io.BytesIO:
    qr = qrcode.QRCode(
        version=1, error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10, border=2
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color='#1B3A6B', back_color='white')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf

# ── Custom Flowables ──────────────────────────────────────────────────────────
class ColorRect(Flowable):
    """A solid-color rectangle background."""
    def __init__(self, w, h, color, radius=4):
        super().__init__()
        self.w, self.h, self.color, self.radius = w, h, color, radius

    def wrap(self, *args):
        return self.w, self.h

    def draw(self):
        self.canv.setFillColor(self.color)
        self.canv.roundRect(0, 0, self.w, self.h, self.radius, fill=1, stroke=0)


class GoldAccentBox(Flowable):
    """A callout box with a gold left border and light background."""
    def __init__(self, content_flowables, width):
        super().__init__()
        self.content = content_flowables
        self.w = width
        self._height = None

    def wrap(self, avW, avH):
        inner_w = self.w - 0.3 * inch - 24
        total_h = 16
        for f in self.content:
            w, h = f.wrap(inner_w, avH)
            total_h += h + 4
        total_h += 16
        self._height = total_h
        return self.w, self._height

    def draw(self):
        c = self.canv
        h = self._height
        c.setFillColor(SKY)
        c.roundRect(0, 0, self.w, h, 4, fill=1, stroke=0)
        c.setFillColor(GOLD)
        c.rect(0, 0, 4, h, fill=1, stroke=0)
        inner_w = self.w - 0.3 * inch - 24
        y = h - 16
        for f in self.content:
            f.canv = c
            fw, fh = f.wrap(inner_w, h)
            y -= fh
            f.drawOn(c, 0.3 * inch, y)
            y -= 4


class ChecklistItem(Flowable):
    """A checklist item with a gold checkbox."""
    def __init__(self, text, style, width):
        super().__init__()
        self.para = Paragraph(text, style)
        self.w = width
        self._h = None

    def wrap(self, avW, avH):
        pw, ph = self.para.wrap(self.w - 28, avH)
        self._h = max(ph, 20)
        return self.w, self._h

    def draw(self):
        c = self.canv
        box_y = self._h - 16
        c.setFillColor(NAVY)
        c.roundRect(0, box_y - 2, 14, 14, 2, fill=1, stroke=0)
        c.setFillColor(GOLD)
        c.setFont('Helvetica-Bold', 9)
        c.drawString(3, box_y, '✓')
        self.para.canv = c
        pw, ph = self.para.wrap(self.w - 28, self._h)
        self.para.drawOn(c, 26, self._h - ph)


# ── Page Templates (header / footer on every page except cover) ───────────────
class DocWithHeaderFooter(SimpleDocTemplate):
    def __init__(self, filename, logo_path, **kwargs):
        super().__init__(filename, **kwargs)
        self.logo_path = logo_path

    def handle_pageBegin(self):
        super().handle_pageBegin()

    def afterPage(self):
        pass


def build_header_footer(canvas_obj, doc, logo_path, is_cover=False):
    canvas_obj.saveState()
    if is_cover:
        canvas_obj.restoreState()
        return

    # ── Header bar ────────────────────────────────────────────────────────────
    bar_h = 0.55 * inch
    canvas_obj.setFillColor(NAVY)
    canvas_obj.rect(0, PAGE_H - bar_h, PAGE_W, bar_h, fill=1, stroke=0)

    # Logo in header (small)
    try:
        img = PILImage.open(logo_path)
        aspect = img.width / img.height
        logo_h = bar_h * 0.70
        logo_w = logo_h * aspect
        canvas_obj.drawImage(
            logo_path, MARGIN, PAGE_H - bar_h + (bar_h - logo_h) / 2,
            width=logo_w, height=logo_h, mask='auto', preserveAspectRatio=True
        )
    except Exception:
        canvas_obj.setFillColor(GOLD)
        canvas_obj.setFont('Helvetica-Bold', 11)
        canvas_obj.drawString(MARGIN, PAGE_H - bar_h + 14, 'Match Care ABA')

    # Website in header (right)
    canvas_obj.setFillColor(GOLD)
    canvas_obj.setFont('Helvetica-Bold', 9)
    canvas_obj.drawRightString(PAGE_W - MARGIN, PAGE_H - bar_h + 18, 'matchcareaba.com')

    # Gold accent line below header
    canvas_obj.setStrokeColor(GOLD)
    canvas_obj.setLineWidth(2)
    canvas_obj.line(0, PAGE_H - bar_h, PAGE_W, PAGE_H - bar_h)

    # ── Footer bar ────────────────────────────────────────────────────────────
    footer_h = 0.38 * inch
    canvas_obj.setFillColor(NAVY)
    canvas_obj.rect(0, 0, PAGE_W, footer_h, fill=1, stroke=0)

    canvas_obj.setFillColor(GOLD)
    canvas_obj.setFont('Helvetica-Bold', 8)
    canvas_obj.drawCentredString(PAGE_W / 2, 13, 'matchcareaba.com')

    # Page number
    canvas_obj.setFillColor(white)
    canvas_obj.setFont('Helvetica', 7)
    canvas_obj.drawRightString(
        PAGE_W - MARGIN, 13, f'Page {canvas_obj.getPageNumber() - 1}'
    )

    # Logo in footer (very small)
    try:
        img = PILImage.open(logo_path)
        aspect = img.width / img.height
        logo_h = footer_h * 0.65
        logo_w = logo_h * aspect
        canvas_obj.drawImage(
            logo_path, MARGIN, (footer_h - logo_h) / 2,
            width=logo_w, height=logo_h, mask='auto', preserveAspectRatio=True
        )
    except Exception:
        pass

    canvas_obj.restoreState()


# ── Styles ────────────────────────────────────────────────────────────────────
def get_styles():
    styles = {}

    styles['body'] = ParagraphStyle(
        'body', fontName='Helvetica', fontSize=10.5, leading=17,
        textColor=DARK_TEXT, spaceAfter=8, alignment=TA_JUSTIFY
    )
    styles['body_left'] = ParagraphStyle(
        'body_left', fontName='Helvetica', fontSize=10.5, leading=17,
        textColor=DARK_TEXT, spaceAfter=8, alignment=TA_LEFT
    )
    styles['h1'] = ParagraphStyle(
        'h1', fontName='Helvetica-Bold', fontSize=22, leading=28,
        textColor=NAVY, spaceAfter=14, spaceBefore=6
    )
    styles['h2'] = ParagraphStyle(
        'h2', fontName='Helvetica-Bold', fontSize=16, leading=22,
        textColor=NAVY, spaceAfter=10, spaceBefore=18
    )
    styles['h3'] = ParagraphStyle(
        'h3', fontName='Helvetica-Bold', fontSize=12.5, leading=18,
        textColor=NAVY_MID, spaceAfter=6, spaceBefore=10
    )
    styles['callout_head'] = ParagraphStyle(
        'callout_head', fontName='Helvetica-Bold', fontSize=11, leading=16,
        textColor=NAVY, spaceAfter=4
    )
    styles['callout_body'] = ParagraphStyle(
        'callout_body', fontName='Helvetica', fontSize=10, leading=15,
        textColor=DARK_TEXT, spaceAfter=4
    )
    styles['bullet'] = ParagraphStyle(
        'bullet', fontName='Helvetica', fontSize=10.5, leading=16,
        textColor=DARK_TEXT, spaceAfter=4, leftIndent=14,
        bulletIndent=0
    )
    styles['bold_body'] = ParagraphStyle(
        'bold_body', fontName='Helvetica-Bold', fontSize=10.5, leading=17,
        textColor=DARK_TEXT, spaceAfter=4
    )
    styles['cta_head'] = ParagraphStyle(
        'cta_head', fontName='Helvetica-Bold', fontSize=20, leading=26,
        textColor=white, spaceAfter=10, alignment=TA_CENTER
    )
    styles['cta_sub'] = ParagraphStyle(
        'cta_sub', fontName='Helvetica', fontSize=12, leading=18,
        textColor=white, spaceAfter=14, alignment=TA_CENTER
    )
    styles['cta_url'] = ParagraphStyle(
        'cta_url', fontName='Helvetica-Bold', fontSize=16, leading=22,
        textColor=GOLD, spaceAfter=6, alignment=TA_CENTER
    )
    styles['section_label'] = ParagraphStyle(
        'section_label', fontName='Helvetica-Bold', fontSize=8.5, leading=12,
        textColor=GOLD, spaceAfter=2, spaceBefore=0
    )
    styles['small_gray'] = ParagraphStyle(
        'small_gray', fontName='Helvetica', fontSize=8.5, leading=12,
        textColor=MEDIUM_GRAY, spaceAfter=4
    )
    styles['step_num'] = ParagraphStyle(
        'step_num', fontName='Helvetica-Bold', fontSize=26, leading=30,
        textColor=GOLD, spaceAfter=0
    )
    styles['step_title'] = ParagraphStyle(
        'step_title', fontName='Helvetica-Bold', fontSize=13, leading=18,
        textColor=NAVY, spaceAfter=4
    )
    return styles


# ── Section divider line ──────────────────────────────────────────────────────
def section_divider():
    return HRFlowable(width=CONTENT_W, thickness=0.5, color=HexColor('#CBD5E1'),
                      spaceAfter=6, spaceBefore=4)


def gold_rule():
    return HRFlowable(width=0.6 * inch, thickness=3, color=GOLD,
                      spaceAfter=10, spaceBefore=2)


def bullet_item(text, styles):
    return Paragraph(f'<bullet>\u2022</bullet>{text}', styles['bullet'])


# ── Callout box builder ───────────────────────────────────────────────────────
def callout_box(title, items, styles, bg=SKY, border_color=GOLD):
    """Return a Table that looks like a callout card."""
    content_paras = []
    if title:
        content_paras.append(Paragraph(title, styles['callout_head']))
    for item in items:
        content_paras.append(Paragraph(item, styles['callout_body']))

    inner_table = Table([[content_paras]], colWidths=[CONTENT_W - 0.5 * inch])
    inner_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 14),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 14),
        ('LEFTPADDING', (0, 0), (-1, -1), 16),
        ('RIGHTPADDING', (0, 0), (-1, -1), 14),
        ('BACKGROUND', (0, 0), (-1, -1), bg),
        ('ROUNDEDCORNERS', [4, 4, 4, 4]),
    ]))

    wrapper = Table(
        [['', inner_table]],
        colWidths=[6, CONTENT_W - 6]
    )
    wrapper.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), border_color),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    return wrapper


def navy_callout(title, items, styles):
    return callout_box(title, items, styles,
                       bg=HexColor('#EEF2FB'), border_color=NAVY)


def step_row(num, title, body, styles):
    """Return a Table row for a numbered step."""
    num_cell = Paragraph(f'<b>{num}</b>', ParagraphStyle(
        'sn', fontName='Helvetica-Bold', fontSize=28, leading=32,
        textColor=GOLD, alignment=TA_CENTER
    ))
    body_content = [
        Paragraph(title, styles['step_title']),
        Paragraph(body, styles['callout_body'])
    ]
    t = Table([[num_cell, body_content]], colWidths=[0.55 * inch, CONTENT_W - 0.55 * inch])
    t.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('LINEBELOW', (0, 0), (-1, -1), 0.5, HexColor('#CBD5E1')),
    ]))
    return t


# ── Cover Page ────────────────────────────────────────────────────────────────
def draw_cover(canvas_obj, doc, logo_path):
    canvas_obj.saveState()
    w, h = PAGE_W, PAGE_H

    # Full navy background
    canvas_obj.setFillColor(NAVY_DARK)
    canvas_obj.rect(0, 0, w, h, fill=1, stroke=0)

    # Gold decorative stripes (top)
    for i, alpha in enumerate([1.0, 0.45, 0.2]):
        canvas_obj.setFillColor(GOLD)
        canvas_obj.setFillAlpha(alpha)
        canvas_obj.rect(0, h - (i + 1) * 5, w, 4, fill=1, stroke=0)
    canvas_obj.setFillAlpha(1.0)

    # Light texture rectangle for logo area
    canvas_obj.setFillColor(NAVY)
    canvas_obj.roundRect(w / 2 - 1.6 * inch, h - 2.6 * inch, 3.2 * inch, 1.9 * inch, 12, fill=1, stroke=0)

    # Logo
    try:
        img = PILImage.open(logo_path)
        aspect = img.width / img.height
        logo_h = 1.5 * inch
        logo_w = logo_h * aspect
        canvas_obj.drawImage(
            logo_path, w / 2 - logo_w / 2, h - 2.4 * inch,
            width=logo_w, height=logo_h, mask='auto', preserveAspectRatio=True
        )
    except Exception as e:
        canvas_obj.setFillColor(GOLD)
        canvas_obj.setFont('Helvetica-Bold', 20)
        canvas_obj.drawCentredString(w / 2, h - 1.8 * inch, 'Match Care ABA')

    # Gold line separator
    canvas_obj.setStrokeColor(GOLD)
    canvas_obj.setLineWidth(2.5)
    canvas_obj.line(w / 2 - 1.5 * inch, h - 2.85 * inch, w / 2 + 1.5 * inch, h - 2.85 * inch)

    # Main title
    canvas_obj.setFillColor(white)
    canvas_obj.setFont('Helvetica-Bold', 28)
    # Word-wrap manually
    title_lines = [
        'My Child Was Just',
        'Diagnosed with Autism —',
        'What Do I Do Next?'
    ]
    y = h - 3.7 * inch
    for line in title_lines:
        canvas_obj.drawCentredString(w / 2, y, line)
        y -= 36

    # Gold rule below title
    canvas_obj.setStrokeColor(GOLD)
    canvas_obj.setLineWidth(2)
    canvas_obj.line(w / 2 - 1 * inch, y + 10, w / 2 + 1 * inch, y + 10)

    # Subtitle
    canvas_obj.setFillColor(GOLD)
    canvas_obj.setFont('Helvetica-Bold', 15)
    canvas_obj.drawCentredString(w / 2, y - 20, 'A Free Guide for Families')

    # Tagline
    canvas_obj.setFillColor(HexColor('#A8BDD4'))
    canvas_obj.setFont('Helvetica', 11)
    canvas_obj.drawCentredString(w / 2, y - 44,
        'Practical steps, honest answers, and real support for')
    canvas_obj.drawCentredString(w / 2, y - 59,
        'families navigating an autism diagnosis.')

    # Bottom info box
    box_y = 1.25 * inch
    canvas_obj.setFillColor(NAVY_MID)
    canvas_obj.roundRect(MARGIN, box_y, w - 2 * MARGIN, 0.9 * inch, 8, fill=1, stroke=0)
    canvas_obj.setStrokeColor(GOLD)
    canvas_obj.setLineWidth(1.5)
    canvas_obj.roundRect(MARGIN, box_y, w - 2 * MARGIN, 0.9 * inch, 8, fill=0, stroke=1)

    canvas_obj.setFillColor(GOLD)
    canvas_obj.setFont('Helvetica-Bold', 11)
    canvas_obj.drawCentredString(w / 2, box_y + 0.52 * inch, 'Provided Free by Match Care ABA')
    canvas_obj.setFillColor(white)
    canvas_obj.setFont('Helvetica', 9.5)
    canvas_obj.drawCentredString(w / 2, box_y + 0.28 * inch,
        'Free ABA therapy matching in New York, New Jersey & North Carolina')
    canvas_obj.drawCentredString(w / 2, box_y + 0.12 * inch, 'matchcareaba.com')

    # Bottom gold stripes
    for i, alpha in enumerate([0.2, 0.45, 1.0]):
        canvas_obj.setFillColor(GOLD)
        canvas_obj.setFillAlpha(alpha)
        canvas_obj.rect(0, i * 5, w, 4, fill=1, stroke=0)
    canvas_obj.setFillAlpha(1.0)

    canvas_obj.restoreState()


# ── Build PDF ─────────────────────────────────────────────────────────────────
def build_pdf(output_path):
    styles = get_styles()
    story = []

    HEADER_H = 0.55 * inch
    FOOTER_H = 0.38 * inch
    TOP_MARGIN = HEADER_H + 0.35 * inch
    BOT_MARGIN = FOOTER_H + 0.3 * inch

    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=TOP_MARGIN,
        bottomMargin=BOT_MARGIN,
        title='My Child Was Just Diagnosed with Autism — What Do I Do Next?',
        author='Match Care ABA',
        subject='Autism Diagnosis Guide for Families',
        creator='Match Care ABA',
    )

    page_num = [0]

    def on_page(canvas_obj, doc_obj):
        page_num[0] += 1
        if page_num[0] == 1:
            draw_cover(canvas_obj, doc_obj, LOGO_PATH)
        else:
            build_header_footer(canvas_obj, doc_obj, LOGO_PATH, is_cover=False)

    # ── Cover page (content is drawn by on_page callback, no flowable needed) ──
    story.append(PageBreak())

    # ═════════════════════════════════════════════════════════════════════════
    # PAGE 2 — You Are Not Alone
    # ═════════════════════════════════════════════════════════════════════════
    story.append(Paragraph('01', styles['section_label']))
    story.append(Paragraph('You Are Not Alone', styles['h1']))
    story.append(gold_rule())
    story.append(Paragraph(
        'Hearing that your child has been diagnosed with autism can feel overwhelming. '
        'You may be flooded with questions, fears, and emotions — all at the same time. '
        '<b>That is completely normal, and you are not alone.</b>',
        styles['body']
    ))
    story.append(Paragraph(
        'More than 1 in 36 children in the United States is diagnosed with autism spectrum '
        'disorder (ASD). Hundreds of thousands of families have walked this path before you '
        'and have found the support, the therapies, and the community they needed. '
        'You will too.',
        styles['body']
    ))
    story.append(Spacer(1, 8))

    story.append(callout_box(
        'What you might be feeling right now — and why it\'s okay:',
        [
            '\u2022  <b>Shock or disbelief</b> — An official diagnosis can feel sudden even when you\'ve had concerns for a while.',
            '\u2022  <b>Grief</b> — You may grieve the future you had imagined for your child. This is a natural part of the process.',
            '\u2022  <b>Relief</b> — Many parents feel relieved that they finally have answers. That is equally valid.',
            '\u2022  <b>Determination</b> — The drive to do everything you can for your child. That\'s exactly why you\'re reading this guide.',
        ],
        styles
    ))

    story.append(Spacer(1, 12))
    story.append(Paragraph(
        'An autism diagnosis is not the end of the story. It is the beginning of a new chapter '
        'with more information, more support, and more direction than you had before. '
        'Early intervention — starting therapy as soon as possible — is one of the most powerful '
        'tools available to your child. <b>This guide will walk you through exactly what to do next.</b>',
        styles['body']
    ))

    story.append(Spacer(1, 10))
    story.append(navy_callout(
        'A Note from Match Care ABA',
        [
            'We built Match Care ABA because we believe every family deserves access to quality '
            'ABA therapy — regardless of income, insurance, or zip code. Our free matching service '
            'connects families in New York, New Jersey, and North Carolina with licensed, vetted ABA '
            'providers at no cost to you.'
        ],
        styles
    ))

    story.append(PageBreak())

    # ═════════════════════════════════════════════════════════════════════════
    # PAGE 3 — What Is ABA Therapy?
    # ═════════════════════════════════════════════════════════════════════════
    story.append(Paragraph('02', styles['section_label']))
    story.append(Paragraph('What Is ABA Therapy?', styles['h1']))
    story.append(gold_rule())
    story.append(Paragraph(
        '<b>Applied Behavior Analysis (ABA) therapy</b> is the most evidence-based, widely used, '
        'and insurance-covered treatment for autism spectrum disorder. It has been studied for '
        'over 50 years and is endorsed by the American Academy of Pediatrics, the U.S. Surgeon '
        'General, and the CDC.',
        styles['body']
    ))
    story.append(Paragraph(
        'ABA therapy focuses on understanding how behavior works and using that knowledge to '
        'increase helpful, meaningful behaviors while reducing behaviors that may be harmful or '
        'interfere with learning and daily life.',
        styles['body']
    ))

    story.append(Spacer(1, 8))
    story.append(Paragraph('What ABA Teaches', styles['h2']))

    cols = [
        ['Communication &\nLanguage Skills', 'Social Skills', 'Daily Living\n& Self-Care'],
        ['Learning to request needs, use words or AAC devices, follow directions.',
         'Taking turns, making eye contact, playing with peers, understanding emotions.',
         'Getting dressed, toileting, eating, routines, and independence.'],
        ['Attention &\nAcademic Readiness', 'Reducing Challenging\nBehaviors', 'Emotional\nRegulation'],
        ['Sitting, focusing, following classroom instructions, pre-academic skills.',
         'Understanding the "why" behind meltdowns, tantrums, or self-injurious behavior.',
         'Coping strategies, calming techniques, and managing frustration.'],
    ]

    skill_data = [
        [
            Table([[Paragraph(c[0], ParagraphStyle('sh', fontName='Helvetica-Bold', fontSize=10, leading=13, textColor=NAVY, alignment=TA_CENTER)),
                    Spacer(1, 4),
                    Paragraph(c[1], ParagraphStyle('sb', fontName='Helvetica', fontSize=9, leading=13, textColor=DARK_TEXT, alignment=TA_CENTER))]]
                  , colWidths=[(CONTENT_W - 0.2 * inch) / 3])
            for c in zip(cols[0], cols[1])
        ],
        [
            Table([[Paragraph(c[0], ParagraphStyle('sh2', fontName='Helvetica-Bold', fontSize=10, leading=13, textColor=NAVY, alignment=TA_CENTER)),
                    Spacer(1, 4),
                    Paragraph(c[1], ParagraphStyle('sb2', fontName='Helvetica', fontSize=9, leading=13, textColor=DARK_TEXT, alignment=TA_CENTER))]]
                  , colWidths=[(CONTENT_W - 0.2 * inch) / 3])
            for c in zip(cols[2], cols[3])
        ],
    ]

    col_w = (CONTENT_W - 0.3 * inch) / 3
    for row_items in skill_data:
        t = Table([row_items], colWidths=[col_w] * 3)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), SKY),
            ('BOX', (0, 0), (0, 0), 1, HexColor('#CBD5E1')),
            ('BOX', (1, 0), (1, 0), 1, HexColor('#CBD5E1')),
            ('BOX', (2, 0), (2, 0), 1, HexColor('#CBD5E1')),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [SKY]),
        ]))
        story.append(t)
        story.append(Spacer(1, 6))

    story.append(Spacer(1, 4))
    story.append(Paragraph('What ABA Therapy Looks Like Day-to-Day', styles['h2']))
    story.append(Paragraph(
        'ABA therapy is delivered by a <b>Board Certified Behavior Analyst (BCBA)</b>, who designs '
        'your child\'s individualized treatment plan, and <b>Registered Behavior Technicians (RBTs)</b>, '
        'who implement sessions directly with your child.',
        styles['body']
    ))
    story.append(Paragraph(
        'Sessions typically happen in your home, at a clinic, or in school settings. '
        'Therapy hours vary by your child\'s needs — most young children receive between '
        '10 and 40 hours per week, and insurance usually covers the full recommended amount.',
        styles['body']
    ))

    story.append(PageBreak())

    # ═════════════════════════════════════════════════════════════════════════
    # PAGE 4 — How to Get Started (Step by Step)
    # ═════════════════════════════════════════════════════════════════════════
    story.append(Paragraph('03', styles['section_label']))
    story.append(Paragraph('How to Get Started — Step by Step', styles['h1']))
    story.append(gold_rule())
    story.append(Paragraph(
        'The path from diagnosis to starting ABA therapy can feel confusing. '
        'Here is a clear, step-by-step roadmap to follow:',
        styles['body']
    ))
    story.append(Spacer(1, 10))

    steps = [
        ('1', 'Get the Written Diagnosis Report',
         'Ask your diagnosing provider (psychologist, developmental pediatrician, etc.) '
         'for the written evaluation report. You\'ll need this to submit to insurance and to start services.'),
        ('2', 'Contact Your Insurance',
         'Call the member services number on your insurance card and ask: "Does my plan cover ABA therapy for autism? '
         'What do I need to start?" Ask about deductibles, copays, and whether you need a referral.'),
        ('3', 'Get a Prescription from Your Pediatrician',
         'Most insurance companies require a written prescription or referral for ABA therapy from your child\'s '
         'primary care physician. Call your pediatrician\'s office and request one.'),
        ('4', 'Find an ABA Provider',
         'This is where most families get stuck — the waitlists are long and it\'s hard to know who to call. '
         'Match Care ABA removes this step entirely by matching you directly with providers accepting new patients.'),
        ('5', 'Complete the Insurance Authorization',
         'Your ABA provider will conduct an intake assessment and submit an authorization request to your insurance. '
         'This typically takes 2–4 weeks. Stay in touch with your provider during this process.'),
        ('6', 'Begin Therapy',
         'Once authorized, your BCBA will complete an initial assessment with your child and build an individualized '
         'treatment plan. Therapy sessions will then be scheduled and services begin.'),
    ]

    for num, title, body in steps:
        story.append(step_row(num, title, body, styles))
        story.append(Spacer(1, 4))

    story.append(Spacer(1, 10))
    story.append(callout_box(
        '\u23f1  Timeline Tip',
        ['The full process from diagnosis to first session typically takes 4–12 weeks. '
         'Starting the insurance and referral steps immediately after diagnosis will minimize delays. '
         'Don\'t wait — early intervention matters, and every week counts.'],
        styles,
        bg=HexColor('#FFF8EC'),
        border_color=GOLD
    ))

    story.append(PageBreak())

    # ═════════════════════════════════════════════════════════════════════════
    # PAGE 5 — How Insurance Works for ABA
    # ═════════════════════════════════════════════════════════════════════════
    story.append(Paragraph('04', styles['section_label']))
    story.append(Paragraph('How Insurance Works for ABA Therapy', styles['h1']))
    story.append(gold_rule())
    story.append(Paragraph(
        'The good news: <b>ABA therapy is covered by most insurance plans</b> — including Medicaid — '
        'in all 50 states. Federal law (the Affordable Care Act) requires most health insurance plans '
        'to cover ABA therapy as an essential health benefit for children diagnosed with autism.',
        styles['body']
    ))

    story.append(Spacer(1, 8))
    story.append(Paragraph('Private Insurance (Blue Cross, Aetna, United, Cigna, etc.)', styles['h2']))
    story.append(Paragraph(
        'Most private insurance plans cover ABA therapy with a copay or coinsurance after your deductible. '
        'Coverage typically requires:', styles['body_left']
    ))
    for item in [
        'A written autism diagnosis (DSM-5)',
        'A prescription/referral from your pediatrician',
        'A treatment authorization submitted by your ABA provider',
        'Annual re-authorizations as therapy continues',
    ]:
        story.append(bullet_item(item, styles))

    story.append(Spacer(1, 10))
    story.append(Paragraph('Medicaid (including CHIP)', styles['h2']))
    story.append(Paragraph(
        'If your child is covered by Medicaid (Medicaid, NJ FamilyCare, NC Medicaid, etc.), '
        'ABA therapy is fully covered with no copay in most cases. '
        'The authorization process is similar to private insurance.',
        styles['body']
    ))

    story.append(Spacer(1, 6))

    ins_data = [
        ['State', 'Medicaid Program', 'ABA Coverage'],
        ['New York', 'NY Medicaid / Health Home', 'Full coverage, no copay'],
        ['New Jersey', 'NJ FamilyCare', 'Full coverage, no copay'],
        ['North Carolina', 'NC Medicaid', 'Full coverage, no copay'],
    ]

    col_widths = [1.2 * inch, 2.3 * inch, CONTENT_W - 3.5 * inch]
    ins_table = Table(ins_data, colWidths=col_widths)
    ins_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NAVY),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, SKY]),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9.5),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#CBD5E1')),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TEXTCOLOR', (2, 1), (2, -1), HexColor('#15803D')),
        ('FONTNAME', (2, 1), (2, -1), 'Helvetica-Bold'),
    ]))
    story.append(ins_table)

    story.append(Spacer(1, 14))
    story.append(callout_box(
        'What if I get denied?',
        [
            'Insurance denials are common and often reversible. You have the right to appeal. '
            'Your ABA provider can assist with the appeals process. Match Care ABA can also help '
            'connect you with providers experienced in navigating denials.'
        ],
        styles,
        bg=HexColor('#FFF8EC'),
        border_color=GOLD
    ))

    story.append(Spacer(1, 12))
    story.append(Paragraph('What If I Don\'t Have Insurance?', styles['h2']))
    story.append(Paragraph(
        'If your child does not have insurance coverage, you may qualify for Medicaid based on '
        'income. You can also contact your state\'s early intervention program (for children under 3) '
        'or school district (for children 3–21), which are required by law to provide services at no cost.',
        styles['body']
    ))

    story.append(PageBreak())

    # ═════════════════════════════════════════════════════════════════════════
    # PAGE 6 — Questions to Ask a Provider
    # ═════════════════════════════════════════════════════════════════════════
    story.append(Paragraph('05', styles['section_label']))
    story.append(Paragraph('Questions to Ask a Provider', styles['h1']))
    story.append(gold_rule())
    story.append(Paragraph(
        'Not all ABA providers are the same. Asking the right questions upfront will help you '
        'find a provider who is the right fit for your child and family.',
        styles['body']
    ))

    story.append(Spacer(1, 6))

    categories = [
        ('About Qualifications', [
            'Are your BCBAs licensed in this state?',
            'What is the ratio of BCBA supervision hours to RBT-delivered therapy hours?',
            'How long has your agency been providing ABA therapy?',
        ]),
        ('About the Program', [
            'Do you offer home-based, center-based, or school-based therapy — or a combination?',
            'How do you individualize treatment plans? Is the program naturalistic or more structured?',
            'How do you involve parents in the therapy process?',
        ]),
        ('About Logistics', [
            'Are you accepting new patients right now?',
            'Do you accept my insurance (or Medicaid)?',
            'What does the intake and authorization process look like, and how long does it take?',
            'What happens if my assigned therapist (RBT) changes?',
        ]),
        ('About Communication', [
            'How will you keep me updated on my child\'s progress?',
            'What does parent training look like, and is it included?',
            'Who do I call with questions or concerns?',
        ]),
    ]

    for cat_title, questions in categories:
        story.append(KeepTogether([
            Paragraph(cat_title, styles['h3']),
            *[bullet_item(q, styles) for q in questions],
            Spacer(1, 6),
        ]))

    story.append(Spacer(1, 4))
    story.append(navy_callout(
        '\ud83d\udca1 Green Flags to Look For',
        [
            '\u2022  High BCBA supervision hours (5+ hours per month per client)',
            '\u2022  Clear parent training component built into the plan',
            '\u2022  Naturalistic, play-based approaches (especially for young children)',
            '\u2022  Transparent communication and dedicated case manager',
            '\u2022  Experience with your child\'s specific profile and age group',
        ],
        styles
    ))

    story.append(PageBreak())

    # ═════════════════════════════════════════════════════════════════════════
    # PAGE 7 — How Match Care ABA Can Help
    # ═════════════════════════════════════════════════════════════════════════
    story.append(Paragraph('06', styles['section_label']))
    story.append(Paragraph('How Match Care ABA Can Help', styles['h1']))
    story.append(gold_rule())
    story.append(Paragraph(
        'Finding an ABA provider on your own is one of the hardest parts of the process. '
        'Waitlists can stretch 6–18 months at popular agencies, and it\'s nearly impossible '
        'to know which providers have openings, accept your insurance, or serve your area. '
        '<b>That\'s exactly why we built Match Care ABA.</b>',
        styles['body']
    ))

    story.append(Spacer(1, 10))

    how_it_works = [
        ('Tell Us About Your Child', 'Answer a brief questionnaire about your child\'s age, diagnosis, location, insurance, and scheduling needs. It takes less than 5 minutes.'),
        ('We Find Your Match', 'Our team reviews your profile and identifies licensed ABA providers in your area who are accepting new patients and accept your insurance.'),
        ('We Make the Introduction', 'We connect you directly with matched providers — so you\'re not cold-calling agencies or sitting on waitlists.'),
        ('You Start Services', 'Work with your matched provider to complete intake and begin therapy. We follow up to make sure the match worked out.'),
    ]

    for i, (title, body) in enumerate(how_it_works, 1):
        step_style = TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 0), (0, -1), NAVY),
            ('BACKGROUND', (1, 0), (1, -1), white if i % 2 == 1 else SKY),
            ('LINEBELOW', (0, 0), (-1, -1), 0.5, HexColor('#CBD5E1')),
        ])
        num_para = Paragraph(
            str(i),
            ParagraphStyle('snum', fontName='Helvetica-Bold', fontSize=22,
                           leading=26, textColor=GOLD, alignment=TA_CENTER)
        )
        text_content = [
            Paragraph(title, styles['bold_body']),
            Paragraph(body, styles['callout_body']),
        ]
        row_t = Table([[num_para, text_content]], colWidths=[0.5 * inch, CONTENT_W - 0.5 * inch])
        row_t.setStyle(step_style)
        story.append(row_t)

    story.append(Spacer(1, 16))

    # "Why it's free" box
    story.append(callout_box(
        'Why is it free?',
        [
            'Match Care ABA is funded through partnerships with ABA provider agencies. '
            'Providers pay us a referral fee when a successful match is made — so the service '
            'is completely free for families. There is no catch, no subscription, and no obligation.'
        ],
        styles,
        bg=HexColor('#FFF8EC'),
        border_color=GOLD
    ))

    story.append(Spacer(1, 14))

    # Coverage map
    states_data = [
        ['New York', 'New Jersey', 'North Carolina'],
        ['NYC, Long Island,\nWestchester & more', 'Bergen, Essex, Hudson\nCounty & more', 'Raleigh, Charlotte,\nDurham & more'],
    ]
    col_w3 = CONTENT_W / 3
    states_t = Table(states_data, colWidths=[col_w3] * 3)
    states_t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NAVY_MID),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, 1), 9),
        ('TEXTCOLOR', (0, 1), (-1, 1), DARK_TEXT),
        ('ROWBACKGROUNDS', (0, 1), (-1, 1), [SKY]),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#CBD5E1')),
    ]))
    story.append(states_t)

    story.append(PageBreak())

    # ═════════════════════════════════════════════════════════════════════════
    # PAGE 8 — Resources and Next Steps
    # ═════════════════════════════════════════════════════════════════════════
    story.append(Paragraph('07', styles['section_label']))
    story.append(Paragraph('Resources & Next Steps', styles['h1']))
    story.append(gold_rule())
    story.append(Paragraph(
        'You don\'t have to figure this out alone. Here are trusted organizations, '
        'tools, and next steps to help you on your journey.',
        styles['body']
    ))

    story.append(Spacer(1, 6))
    story.append(Paragraph('National Organizations', styles['h2']))

    resources = [
        ('Autism Speaks', 'autismspeaks.org',
         'Resources, toolkits, and a 100-Day Kit for newly diagnosed families.'),
        ('Autism Society of America', 'autism-society.org',
         'Local chapters, community support, and information on rights and services.'),
        ('ASAT (Association for Science in Autism Treatment)', 'asatonline.org',
         'Research-based summaries of autism treatments and evidence-based practices.'),
        ('BACB (Behavior Analyst Certification Board)', 'bacb.com',
         'Verify that a BCBA is licensed and in good standing using their certificant registry.'),
    ]

    for org, url, desc in resources:
        story.append(KeepTogether([
            Paragraph(f'<b>{org}</b>  <font color="#2A5298">{url}</font>', styles['body_left']),
            Paragraph(desc, styles['small_gray']),
            Spacer(1, 4),
        ]))

    story.append(Spacer(1, 4))
    story.append(Paragraph('State-Specific Resources', styles['h2']))

    state_res = [
        ('<b>New York:</b>', 'NYS Early Intervention (for under 3) · CPSE/CSE school services (3–21) · NY Medicaid (DOH)'),
        ('<b>New Jersey:</b>', 'NJ Early Intervention · Child Study Team services · NJ FamilyCare (Medicaid)'),
        ('<b>North Carolina:</b>', 'NC Infant-Toddler Program · Exceptional Children services · NC Medicaid (DHHS)'),
    ]
    for label, text in state_res:
        story.append(Paragraph(f'{label} {text}', styles['bullet']))

    story.append(Spacer(1, 14))
    story.append(Paragraph('Your Immediate Next Steps', styles['h2']))

    next_steps = [
        'Request your written diagnosis report from your evaluator',
        'Ask your pediatrician for an ABA therapy prescription/referral',
        'Call your insurance to confirm ABA coverage',
        'Visit matchcareaba.com to start the free matching process',
        'Download and save this guide to share with family members',
    ]

    for i, step in enumerate(next_steps, 1):
        t = Table(
            [[Paragraph(str(i), ParagraphStyle('ns_num', fontName='Helvetica-Bold',
                        fontSize=13, textColor=white, alignment=TA_CENTER)),
              Paragraph(step, styles['body_left'])]],
            colWidths=[0.3 * inch, CONTENT_W - 0.3 * inch]
        )
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), NAVY),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (1, 0), (1, 0), 8),
            ('LINEBELOW', (0, 0), (-1, -1), 0.5, HexColor('#CBD5E1')),
        ]))
        story.append(t)

    story.append(PageBreak())

    # ═════════════════════════════════════════════════════════════════════════
    # LAST PAGE — CTA + QR Code
    # ═════════════════════════════════════════════════════════════════════════

    # Generate QR code
    qr_buf = make_qr_image('https://matchcareaba.com', 400)
    qr_img = Image(qr_buf, width=1.6 * inch, height=1.6 * inch)

    story.append(Spacer(1, 0.3 * inch))

    # Big CTA box
    cta_inner = [
        Paragraph('Ready to Find an ABA Provider?', styles['cta_head']),
        Spacer(1, 8),
        Paragraph(
            'Match Care ABA matches families with licensed, vetted ABA therapy '
            'providers — completely free of charge.',
            styles['cta_sub']
        ),
        Spacer(1, 4),
        Paragraph('No waitlists to navigate. No cold calls. Just answers.', styles['cta_sub']),
        Spacer(1, 16),
        Paragraph('Get started at:', ParagraphStyle(
            'cta_label', fontName='Helvetica', fontSize=11, textColor=HexColor('#A8BDD4'),
            alignment=TA_CENTER
        )),
        Paragraph('matchcareaba.com', styles['cta_url']),
        Spacer(1, 6),
        Paragraph('Serving families in New York · New Jersey · North Carolina', ParagraphStyle(
            'cta_states', fontName='Helvetica', fontSize=10, textColor=HexColor('#A8BDD4'),
            alignment=TA_CENTER
        )),
    ]

    cta_table = Table([cta_inner], colWidths=[CONTENT_W])
    cta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), NAVY_DARK),
        ('ROUNDEDCORNERS', [10, 10, 10, 10]),
        ('TOPPADDING', (0, 0), (-1, -1), 32),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 32),
        ('LEFTPADDING', (0, 0), (-1, -1), 28),
        ('RIGHTPADDING', (0, 0), (-1, -1), 28),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(cta_table)

    story.append(Spacer(1, 24))

    # QR code + label
    qr_label_style = ParagraphStyle(
        'qrl', fontName='Helvetica', fontSize=9, textColor=MEDIUM_GRAY, alignment=TA_CENTER
    )
    qr_title_style = ParagraphStyle(
        'qrt', fontName='Helvetica-Bold', fontSize=10, textColor=NAVY, alignment=TA_CENTER
    )

    qr_table = Table(
        [[qr_img, [
            Paragraph('Scan to get started', qr_title_style),
            Spacer(1, 6),
            Paragraph('Point your phone\'s camera at this\nQR code to visit matchcareaba.com', qr_label_style),
            Spacer(1, 8),
            Paragraph('Free · Fast · No Obligation', ParagraphStyle(
                'qrb', fontName='Helvetica-Bold', fontSize=9, textColor=GOLD, alignment=TA_CENTER
            )),
        ]]],
        colWidths=[1.8 * inch, CONTENT_W - 1.8 * inch]
    )
    qr_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (0, 0), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(qr_table)

    story.append(Spacer(1, 20))
    story.append(HRFlowable(width=CONTENT_W, thickness=0.5, color=HexColor('#CBD5E1')))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        'This guide is provided for informational purposes only and does not constitute medical or legal advice. '
        'Always consult with qualified healthcare professionals regarding your child\'s care.',
        ParagraphStyle('disc', fontName='Helvetica', fontSize=7.5, textColor=MEDIUM_GRAY,
                       alignment=TA_CENTER, leading=11)
    ))
    story.append(Paragraph(
        '© 2025 Match Care ABA · matchcareaba.com · Free ABA Therapy Matching Service',
        ParagraphStyle('copy', fontName='Helvetica', fontSize=7.5, textColor=MEDIUM_GRAY,
                       alignment=TA_CENTER, leading=11, spaceBefore=4)
    ))

    # ── Build ─────────────────────────────────────────────────────────────────
    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    print(f'PDF saved to: {output_path}')


if __name__ == '__main__':
    output = os.path.join(os.path.dirname(__file__), 'autism-diagnosis-guide.pdf')
    build_pdf(output)
