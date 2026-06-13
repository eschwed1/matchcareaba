#!/usr/bin/env python3
"""Generate Match Care ABA tri-fold brochure — 11x8.5 landscape, 2 pages.
Redesigned: dense panels, colored bands, large text, two photos."""

import os
import math
import qrcode
import numpy as np
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.colors import HexColor
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PIL import Image, ImageDraw
from io import BytesIO

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT = os.path.join(SCRIPT_DIR, "matchcareaba-brochure.pdf")
LOGO = os.path.join(SCRIPT_DIR, "logo.jpeg")
HERO_IMG = os.path.join(SCRIPT_DIR, "family-hero.jpeg")
CHILD_IMG = os.path.join(SCRIPT_DIR, "child-learning.jpg")

# 11 x 8.5 landscape
WIDTH = 11 * inch    # 792pt
HEIGHT = 8.5 * inch  # 612pt
PANEL_W = WIDTH / 3  # 264pt

# Color palette
NAVY = HexColor("#1B3A6B")
NAVY_DARK = HexColor("#122B52")
TEAL = HexColor("#0891B2")
TEAL_LIGHT = HexColor("#22D3EE")
TEAL_DARK = HexColor("#066A84")
GOLD = HexColor("#F5A623")
GOLD_LIGHT = HexColor("#FFD166")
PEACH = HexColor("#FDEEE0")
WHITE = HexColor("#FFFFFF")
TEXT_DARK = HexColor("#1E293B")
MUTED = HexColor("#64748B")
SHADOW = HexColor("#E5D5C8")
LIGHT_BLUE = HexColor("#C5E8ED")
SKY = HexColor("#EEF6FF")

FONT_B = "Helvetica-Bold"
FONT_R = "Helvetica"


# ─── Helpers ────────────────────────────────────────────────────

def rounded_rect(c, x, y, w, h, r, fill=None, stroke=None, sw=1):
    p = c.beginPath()
    p.roundRect(x, y, w, h, r)
    if fill:
        c.setFillColor(fill)
    if stroke:
        c.setStrokeColor(stroke)
        c.setLineWidth(sw)
    c.drawPath(p, fill=1 if fill else 0, stroke=1 if stroke else 0)


def remove_white_bg(img_path, threshold=230):
    img = Image.open(img_path).convert("RGBA")
    data = np.array(img)
    white_mask = (data[:, :, 0] > threshold) & \
                 (data[:, :, 1] > threshold) & \
                 (data[:, :, 2] > threshold)
    data[white_mask, 3] = 0
    img = Image.fromarray(data)
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return ImageReader(buf)


def make_circular_image(path, diameter, left_offset=8):
    img = Image.open(path).convert("RGBA")
    s = min(img.width, img.height)
    left = max(0, (img.width - s) // left_offset)
    top = (img.height - s) // 2
    img = img.crop((left, top, left + s, top + s))
    scale = 4
    px = int(diameter * scale)
    img = img.resize((px, px), Image.LANCZOS)
    mask = Image.new("L", (px, px), 0)
    d = ImageDraw.Draw(mask)
    d.ellipse([(0, 0), (px - 1, px - 1)], fill=255)
    img.putalpha(mask)
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return ImageReader(buf)


def make_rounded_rect_image(path, w, h, radius):
    """Crop image to a rounded rectangle."""
    img = Image.open(path).convert("RGBA")
    # Crop to aspect ratio
    target_ratio = w / h
    img_ratio = img.width / img.height
    if img_ratio > target_ratio:
        new_w = int(img.height * target_ratio)
        left = (img.width - new_w) // 2
        img = img.crop((left, 0, left + new_w, img.height))
    else:
        new_h = int(img.width / target_ratio)
        top = (img.height - new_h) // 2
        img = img.crop((0, top, img.width, top + new_h))
    scale = 3
    px_w = int(w * scale)
    px_h = int(h * scale)
    px_r = int(radius * scale)
    img = img.resize((px_w, px_h), Image.LANCZOS)
    mask = Image.new("L", (px_w, px_h), 0)
    d = ImageDraw.Draw(mask)
    d.rounded_rectangle([(0, 0), (px_w - 1, px_h - 1)], radius=px_r, fill=255)
    img.putalpha(mask)
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return ImageReader(buf)


def make_qr(url):
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H,
                        box_size=12, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#1B3A6B", back_color="#FFFFFF").convert("RGB")
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return ImageReader(buf)


def draw_centered_wrapped(c, text, cx, y, max_width, font, size, color, leading=None):
    if leading is None:
        leading = size + 4
    c.setFont(font, size)
    c.setFillColor(color)
    words = text.split()
    lines = []
    current = ""
    for w in words:
        test = f"{current} {w}".strip()
        if c.stringWidth(test, font, size) <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = w
    if current:
        lines.append(current)
    for line in lines:
        c.drawCentredString(cx, y, line)
        y -= leading
    return y


def draw_band(c, x, y, w, h, color):
    """Draw a solid colored horizontal band."""
    c.setFillColor(color)
    c.rect(x, y, w, h, fill=1, stroke=0)


def draw_dots_row(c, cx, y, colors, radius=3, spacing=12):
    """Draw a row of decorative dots centered at cx."""
    total = (len(colors) - 1) * spacing
    sx = cx - total / 2
    for i, col in enumerate(colors):
        c.setFillColor(col)
        c.circle(sx + i * spacing, y, radius, fill=1, stroke=0)


# ─── Page 1: OUTSIDE (Back | Hidden Flap | Front Cover) ────────

def draw_outside(c):
    back_x = 0
    flap_x = PANEL_W
    front_x = 2 * PANEL_W
    M = 22

    logo_img = remove_white_bg(LOGO)
    qr_img = make_qr("https://matchcareaba.com")

    # ═══════════════════════════════════════════════════════════
    # BACK PANEL (left) — full navy
    # ═══════════════════════════════════════════════════════════
    draw_band(c, back_x, 0, PANEL_W, HEIGHT, NAVY)

    # Top gold accent band
    draw_band(c, back_x, HEIGHT - 8, PANEL_W, 8, GOLD)

    # Decorative circle top-right
    c.setFillColor(HexColor("#224B82"))
    c.circle(back_x + PANEL_W - 20, HEIGHT - 50, 80, fill=1, stroke=0)

    # Decorative circle bottom-left
    c.setFillColor(HexColor("#224B82"))
    c.circle(back_x + 20, 50, 60, fill=1, stroke=0)

    bcx = back_x + PANEL_W / 2

    # Logo — large, white circle background so it looks clean on navy
    logo_s = 140
    logo_x = bcx - logo_s / 2
    logo_y = HEIGHT - logo_s - 40
    c.setFillColor(LIGHT_BLUE)
    c.circle(bcx, logo_y + logo_s / 2, logo_s / 2 + 8, fill=1, stroke=0)
    c.drawImage(logo_img, logo_x, logo_y, logo_s, logo_s,
                preserveAspectRatio=True, mask="auto")

    # Gold separator line
    sep_y = logo_y - 16
    c.setStrokeColor(GOLD)
    c.setLineWidth(2)
    c.line(bcx - 60, sep_y, bcx + 60, sep_y)

    # "Your Free ABA Matching Service"
    ty = sep_y - 24
    c.setFont(FONT_B, 12)
    c.setFillColor(GOLD_LIGHT)
    c.drawCentredString(bcx, ty, "Your Free ABA")
    ty -= 16
    c.drawCentredString(bcx, ty, "Matching Service")

    # Teal band with "How ABA Helps" section
    band_h = 200
    band_y = ty - 30 - band_h
    draw_band(c, back_x, band_y, PANEL_W, band_h, TEAL)

    # Header inside band
    by = band_y + band_h - 22
    c.setFont(FONT_B, 13)
    c.setFillColor(WHITE)
    c.drawCentredString(bcx, by, "HOW ABA HELPS")

    # Gold underline
    by -= 10
    c.setStrokeColor(GOLD)
    c.setLineWidth(1.5)
    c.line(bcx - 50, by, bcx + 50, by)

    # Bullet points — matching flyer content
    aba_items = [
        ("Communication skills", "(asking, sharing, social interaction)"),
        ("Daily living skills", "(dressing, eating, routines)"),
        ("Emotional regulation", "(coping tools, transitions)"),
        ("Independence & confidence", ""),
    ]
    by -= 22
    for main, sub in aba_items:
        c.setFillColor(GOLD)
        c.circle(back_x + M + 10, by + 3, 4, fill=1, stroke=0)
        c.setFont(FONT_R, 10)
        c.setFillColor(WHITE)
        c.drawString(back_x + M + 22, by, main)
        if sub:
            by -= 14
            c.setFont(FONT_R, 9)
            c.setFillColor(HexColor("#B0E0E8"))
            c.drawString(back_x + M + 22, by, sub)
        by -= 18

    # Contact info section at bottom
    ty = band_y - 24
    c.setFont(FONT_B, 13)
    c.setFillColor(WHITE)
    c.drawCentredString(bcx, ty, "matchcareaba.com")
    ty -= 18
    c.setFont(FONT_R, 10)
    c.setFillColor(HexColor("#94A3B8"))
    c.drawCentredString(bcx, ty, "matchcareaba@gmail.com")

    # Bottom gold band
    draw_band(c, back_x, 0, PANEL_W, 8, GOLD)

    # ═══════════════════════════════════════════════════════════
    # HIDDEN FLAP (middle) — peach + child photo + ABA info
    # ═══════════════════════════════════════════════════════════
    draw_band(c, flap_x, 0, PANEL_W, HEIGHT, PEACH)

    # Top teal band
    draw_band(c, flap_x, HEIGHT - 50, PANEL_W, 50, TEAL)
    c.setFont(FONT_B, 18)
    c.setFillColor(WHITE)
    flap_cx = flap_x + PANEL_W / 2
    c.drawCentredString(flap_cx, HEIGHT - 34, "What is ABA?")

    # Child photo — wide rounded rectangle
    child_w = PANEL_W - 36
    child_h = 150
    child_img = make_rounded_rect_image(CHILD_IMG, child_w, child_h, 18)
    child_x = flap_x + (PANEL_W - child_w) / 2
    child_y = HEIGHT - 64 - child_h
    # Shadow
    rounded_rect(c, child_x + 2, child_y - 2, child_w, child_h, 18, fill=SHADOW)
    # Teal accent border
    rounded_rect(c, child_x - 3, child_y - 3, child_w + 6, child_h + 6, 20,
                 stroke=TEAL_LIGHT, sw=2.5)
    c.drawImage(child_img, child_x, child_y, child_w, child_h, mask="auto")

    # Decorative dots
    draw_dots_row(c, flap_cx, child_y - 14, [TEAL, GOLD, TEAL, GOLD, TEAL])

    # "Applied Behavior Analysis" — bigger header
    ty = child_y - 38
    c.setFont(FONT_B, 14)
    c.setFillColor(NAVY)
    c.drawCentredString(flap_cx, ty, "Applied Behavior")
    ty -= 18
    c.drawCentredString(flap_cx, ty, "Analysis (ABA)")

    # Gold separator
    ty -= 14
    c.setStrokeColor(GOLD)
    c.setLineWidth(2)
    c.line(flap_cx - 40, ty, flap_cx + 40, ty)

    # Body text
    ty -= 18
    info_text = (
        "The gold standard, evidence based treatment for "
        "autism. ABA helps children develop communication, "
        "social skills, and independence through structured, "
        "one on one therapy sessions."
    )
    ty = draw_centered_wrapped(c, info_text, flap_cx, ty, PANEL_W - 44,
                               FONT_R, 9.5, TEXT_DARK, leading=13)

    # Bold teal mission statement — larger, different font
    ty -= 16
    mission = (
        "We help you navigate the next steps by connecting "
        "you with trusted ABA providers dedicated to helping "
        "your child grow and thrive."
    )
    ty = draw_centered_wrapped(c, mission, flap_cx, ty, PANEL_W - 36,
                               "Helvetica-BoldOblique", 12, TEAL, leading=16)

    # Navy info box — pushed down
    box_h = 70
    box_y = ty - box_h - 22
    box_w = PANEL_W - 32
    box_x = flap_x + (PANEL_W - box_w) / 2
    rounded_rect(c, box_x, box_y, box_w, box_h, 12, fill=NAVY)

    c.setFont(FONT_B, 11)
    c.setFillColor(GOLD_LIGHT)
    c.drawCentredString(flap_cx, box_y + box_h - 20, "ABA is recommended by:")
    c.setFont(FONT_R, 9.5)
    c.setFillColor(WHITE)
    c.drawCentredString(flap_cx, box_y + box_h - 36, "American Academy of Pediatrics")
    c.drawCentredString(flap_cx, box_y + box_h - 50, "U.S. Surgeon General")
    c.drawCentredString(flap_cx, box_y + box_h - 64, "National Institutes of Health")

    # Bottom teal band
    draw_band(c, flap_x, 0, PANEL_W, 28, TEAL)
    c.setFont(FONT_B, 9)
    c.setFillColor(WHITE)
    c.drawCentredString(flap_cx, 10, "Covered by most insurance plans")

    # ═══════════════════════════════════════════════════════════
    # FRONT COVER (right) — peach + logo + hero + QR
    # ═══════════════════════════════════════════════════════════
    draw_band(c, front_x, 0, PANEL_W, HEIGHT, PEACH)

    # Top decorative circles
    c.setFillColor(LIGHT_BLUE)
    c.circle(front_x + 10, HEIGHT + 10, 80, fill=1, stroke=0)
    c.setFillColor(HexColor("#FDE4B0"))
    c.circle(front_x + PANEL_W - 10, HEIGHT - 20, 40, fill=1, stroke=0)

    front_cx = front_x + PANEL_W / 2

    # Logo — bigger
    logo_s2 = 155
    logo_x2 = front_cx - logo_s2 / 2
    logo_y2 = HEIGHT - logo_s2 - 14
    c.drawImage(logo_img, logo_x2, logo_y2, logo_s2, logo_s2,
                preserveAspectRatio=True, mask="auto")

    # Headline — moved up closer to logo
    hy = logo_y2 - 2
    c.setFont(FONT_B, 22)
    c.setFillColor(NAVY)
    c.drawCentredString(front_cx, hy, "Finding ABA")
    hy -= 26
    c.drawCentredString(front_cx, hy, "Therapy Just")
    hy -= 26
    c.drawCentredString(front_cx, hy, "Got Easier")

    # Gold separator
    hy -= 12
    c.setStrokeColor(GOLD)
    c.setLineWidth(2.5)
    c.line(front_cx - 50, hy, front_cx + 50, hy)

    # Subheadline
    hy -= 16
    c.setFont(FONT_B, 11)
    c.setFillColor(TEAL)
    c.drawCentredString(front_cx, hy, "Your Free Personal ABA")
    hy -= 15
    c.drawCentredString(front_cx, hy, "Therapy Matching Service")

    # Hero image — large circle with playful border, pushed down
    hy -= 24
    hero_d = 160
    hero_img = make_circular_image(HERO_IMG, hero_d)
    hero_x = front_cx - hero_d / 2
    hero_y = hy - hero_d
    hcx = hero_x + hero_d / 2
    hcy = hero_y + hero_d / 2
    # Teal shadow
    c.setFillColor(TEAL_LIGHT)
    c.circle(hcx - 6, hcy + 6, hero_d / 2 + 6, fill=1, stroke=0)
    # Gold shadow
    c.setFillColor(HexColor("#FDE4B0"))
    c.circle(hcx + 6, hcy - 6, hero_d / 2 + 6, fill=1, stroke=0)
    # White border
    c.setFillColor(WHITE)
    c.circle(hcx, hcy, hero_d / 2 + 4, fill=1, stroke=0)
    c.drawImage(hero_img, hero_x, hero_y, hero_d, hero_d, mask="auto")
    # Decorative dots
    c.setFillColor(GOLD)
    c.circle(hcx - 55, hcy + hero_d / 2 + 12, 7, fill=1, stroke=0)
    c.setFillColor(TEAL)
    c.circle(hcx + 58, hcy - hero_d / 2 + 5, 5, fill=1, stroke=0)

    # QR Code
    qr_s = 0.85 * inch
    qr_x = front_cx - qr_s / 2
    qr_y = hero_y - qr_s - 24
    pad = 5
    rounded_rect(c, qr_x - pad, qr_y - pad, qr_s + 2 * pad, qr_s + 2 * pad, 8,
                 fill=WHITE, stroke=NAVY, sw=1.2)
    c.drawImage(qr_img, qr_x, qr_y, qr_s, qr_s)

    # "Scan to get matched today"
    c.setFont(FONT_B, 9.5)
    c.setFillColor(NAVY)
    c.drawCentredString(front_cx, qr_y - 14, "Scan to get matched today!")

    # Bottom navy band
    draw_band(c, front_x, 0, PANEL_W, 28, NAVY)
    c.setFont(FONT_B, 10)
    c.setFillColor(WHITE)
    c.drawCentredString(front_cx, 10, "matchcareaba.com")

    # Panel fold guides (very light, for printing)
    c.setStrokeColor(HexColor("#DDDDDD"))
    c.setLineWidth(0.25)
    c.setDash(3, 3)
    c.line(PANEL_W, 0, PANEL_W, HEIGHT)
    c.line(2 * PANEL_W, 0, 2 * PANEL_W, HEIGHT)
    c.setDash()


# ─── Page 2: INSIDE (Left | Middle | Right) ────────────────────

def draw_inside(c):
    left_x = 0
    mid_x = PANEL_W
    right_x = 2 * PANEL_W
    M = 22

    logo_img = remove_white_bg(LOGO)
    qr_img = make_qr("https://matchcareaba.com")

    # Full page sky background
    draw_band(c, 0, 0, WIDTH, HEIGHT, SKY)

    # ═══════════════════════════════════════════════════════════
    # INSIDE LEFT — Empathy message + child photo
    # ═══════════════════════════════════════════════════════════
    lcx = left_x + PANEL_W / 2

    # Top navy band with headline
    band_h = 90
    draw_band(c, left_x, HEIGHT - band_h, PANEL_W, band_h, NAVY)
    c.setFont(FONT_B, 18)
    c.setFillColor(WHITE)
    c.drawCentredString(lcx, HEIGHT - 32, "You Shouldn't")
    c.drawCentredString(lcx, HEIGHT - 54, "Have to Do")
    c.drawCentredString(lcx, HEIGHT - 76, "This Alone")

    # Gold underline below band
    c.setStrokeColor(GOLD)
    c.setLineWidth(3)
    c.line(lcx - 50, HEIGHT - band_h - 2, lcx + 50, HEIGHT - band_h - 2)

    # Body text
    ty = HEIGHT - band_h - 24
    body = (
        "Getting an autism diagnosis for your child can feel "
        "overwhelming. Between finding the right provider, "
        "navigating insurance, and dealing with waitlists, "
        "it\u2019s a lot to handle on your own."
    )
    ty = draw_centered_wrapped(c, body, lcx, ty, PANEL_W - 44,
                               FONT_R, 10.5, TEXT_DARK, leading=15)

    ty -= 10
    body2 = (
        "That\u2019s why we created Match Care ABA. We take "
        "the stress out of finding ABA therapy so you can "
        "focus on what matters most, your child."
    )
    ty = draw_centered_wrapped(c, body2, lcx, ty, PANEL_W - 44,
                               FONT_R, 10.5, TEXT_DARK, leading=15)

    # Child photo — wide rounded rectangle
    ty -= 14
    child_w = PANEL_W - 36
    child_h = 120
    child_img = make_rounded_rect_image(CHILD_IMG, child_w, child_h, 16)
    child_x = left_x + (PANEL_W - child_w) / 2
    child_y = ty - child_h
    # Shadow
    rounded_rect(c, child_x + 2, child_y - 2, child_w, child_h, 16, fill=SHADOW)
    # Gold accent border
    rounded_rect(c, child_x - 3, child_y - 3, child_w + 6, child_h + 6, 18,
                 stroke=GOLD, sw=2)
    c.drawImage(child_img, child_x, child_y, child_w, child_h, mask="auto")

    # Decorative dots
    draw_dots_row(c, lcx, child_y - 12, [TEAL, GOLD, TEAL])

    # Reassurance box
    box_w = PANEL_W - 32
    box_h = 52
    box_x = left_x + (PANEL_W - box_w) / 2
    box_y = child_y - 28 - box_h
    rounded_rect(c, box_x, box_y, box_w, box_h, 10,
                 fill=WHITE, stroke=TEAL, sw=1.5)
    c.setFont(FONT_B, 10)
    c.setFillColor(TEAL)
    c.drawCentredString(lcx, box_y + box_h - 18, "Your personal matching")
    c.drawCentredString(lcx, box_y + box_h - 32, "service, completely free.")
    c.setFont(FONT_R, 9)
    c.setFillColor(MUTED)
    c.drawCentredString(lcx, box_y + box_h - 46, "Let us find the right fit for your family.")

    # Bottom teal band
    draw_band(c, left_x, 0, PANEL_W, 10, TEAL)

    # ═══════════════════════════════════════════════════════════
    # INSIDE MIDDLE — How It Works + hero image
    # ═══════════════════════════════════════════════════════════
    mcx = mid_x + PANEL_W / 2

    # Top gold accent band
    draw_band(c, mid_x, HEIGHT - 6, PANEL_W, 6, GOLD)

    # Section header
    my = HEIGHT - 30
    c.setFont(FONT_B, 20)
    c.setFillColor(NAVY)
    c.drawCentredString(mcx, my, "How It Works")

    # Gold underline
    my -= 14
    c.setStrokeColor(GOLD)
    c.setLineWidth(3)
    c.line(mcx - 50, my, mcx + 50, my)

    # 3 numbered steps — larger
    steps = [
        ("Fill Out One", "Short Form"),
        ("We Find Your", "Perfect Match"),
        ("Get Connected &", "Start Therapy"),
    ]
    my -= 32
    circle_r = 18
    for i, (line1, line2) in enumerate(steps):
        num = str(i + 1)
        cy = my - circle_r
        # Navy circle with number
        c.setFillColor(NAVY)
        c.circle(mid_x + M + circle_r, cy, circle_r, fill=1, stroke=0)
        c.setFont(FONT_B, 16)
        c.setFillColor(WHITE)
        c.drawCentredString(mid_x + M + circle_r, cy - 6, num)

        # Step text
        tx = mid_x + M + circle_r * 2 + 12
        c.setFont(FONT_B, 11.5)
        c.setFillColor(TEXT_DARK)
        c.drawString(tx, cy + 5, line1)
        c.setFont(FONT_R, 10.5)
        c.setFillColor(MUTED)
        c.drawString(tx, cy - 10, line2)

        # Connecting dashed line
        if i < 2:
            c.setStrokeColor(HexColor("#CBD5E1"))
            c.setLineWidth(1.2)
            c.setDash(3, 3)
            c.line(mid_x + M + circle_r, cy - circle_r - 3,
                   mid_x + M + circle_r, cy - circle_r - 20)
            c.setDash()

        my -= 62

    # Hero image — smaller circle with playful border
    my -= 4
    hero_d2 = 145
    hero_img2 = make_circular_image(HERO_IMG, hero_d2)
    hero_x2 = mcx - hero_d2 / 2
    hero_y2 = my - hero_d2
    hcx2 = hero_x2 + hero_d2 / 2
    hcy2 = hero_y2 + hero_d2 / 2
    # Gold shadow
    c.setFillColor(HexColor("#FDE4B0"))
    c.circle(hcx2 + 5, hcy2 - 5, hero_d2 / 2 + 5, fill=1, stroke=0)
    # Teal shadow
    c.setFillColor(TEAL_LIGHT)
    c.circle(hcx2 - 5, hcy2 + 5, hero_d2 / 2 + 5, fill=1, stroke=0)
    # White border
    c.setFillColor(WHITE)
    c.circle(hcx2, hcy2, hero_d2 / 2 + 3, fill=1, stroke=0)
    c.drawImage(hero_img2, hero_x2, hero_y2, hero_d2, hero_d2, mask="auto")
    # Decorative dots
    c.setFillColor(GOLD)
    c.circle(hcx2 - 40, hcy2 + hero_d2 / 2 + 10, 5, fill=1, stroke=0)
    c.setFillColor(TEAL)
    c.circle(hcx2 + 42, hcy2 - hero_d2 / 2 + 5, 3.5, fill=1, stroke=0)

    # Decorative dots below image
    draw_dots_row(c, mcx, hero_y2 - 12, [GOLD, TEAL, GOLD, TEAL, GOLD])

    # "100% Free" bold teal pill
    free_y = hero_y2 - 42
    pill_w = PANEL_W - 36
    pill_h = 36
    pill_x = mid_x + (PANEL_W - pill_w) / 2
    rounded_rect(c, pill_x, free_y - pill_h, pill_w, pill_h, pill_h / 2, fill=TEAL)
    c.setFont(FONT_B, 13)
    c.setFillColor(WHITE)
    c.drawCentredString(mcx, free_y - pill_h / 2 - 5, "100% Free for Families. Always.")

    # Bottom navy band
    draw_band(c, mid_x, 0, PANEL_W, 10, NAVY)

    # ═══════════════════════════════════════════════════════════
    # INSIDE RIGHT — Why Match Care ABA + therapy types + QR
    # ═══════════════════════════════════════════════════════════
    rcx = right_x + PANEL_W / 2

    # Top teal band with header
    band_h = 56
    draw_band(c, right_x, HEIGHT - band_h, PANEL_W, band_h, TEAL)
    c.setFont(FONT_B, 19)
    c.setFillColor(WHITE)
    c.drawCentredString(rcx, HEIGHT - 26, "Why Match")
    c.drawCentredString(rcx, HEIGHT - 48, "Care ABA?")

    # 5 checkmark bullets — larger
    ry = HEIGHT - band_h - 22
    bullets = [
        "Free for families, always",
        "Verified, trusted providers",
        "Insurance matched first",
        "No long waitlists",
        "Personalized to your child",
    ]
    bx = right_x + M + 6
    for bullet in bullets:
        # Gold checkmark circle
        c.setFillColor(GOLD)
        c.circle(bx + 10, ry + 3, 10, fill=1, stroke=0)
        c.setFont(FONT_B, 10)
        c.setFillColor(WHITE)
        c.drawCentredString(bx + 10, ry - 1, "\u2713")
        # Text
        c.setFont(FONT_R, 11)
        c.setFillColor(TEXT_DARK)
        c.drawString(bx + 26, ry, bullet)
        ry -= 28

    # Navy separator band
    sep_h = 30
    ry -= 8
    draw_band(c, right_x, ry - sep_h, PANEL_W, sep_h, NAVY)
    c.setFont(FONT_B, 12)
    c.setFillColor(WHITE)
    c.drawCentredString(rcx, ry - sep_h / 2 - 5, "We Match You With")

    # Therapy type pills — larger
    ry = ry - sep_h - 16
    therapy_types = [
        ("Clinic Based Therapy", TEAL),
        ("In Home Therapy", TEAL_LIGHT),
        ("At Daycare / School", TEAL),
    ]
    pill_w = PANEL_W - 44
    pill_h = 32
    for label, color in therapy_types:
        pill_x = right_x + (PANEL_W - pill_w) / 2
        rounded_rect(c, pill_x, ry - pill_h, pill_w, pill_h, pill_h / 2, fill=color)
        c.setFont(FONT_B, 11)
        c.setFillColor(WHITE)
        c.drawCentredString(rcx, ry - pill_h / 2 - 4, label)
        ry -= pill_h + 10

    # QR + contact — centered, pushed down
    ry -= 16
    qr_s = 0.85 * inch
    qr_x = rcx - qr_s / 2
    qr_y = ry - qr_s
    pad = 5
    rounded_rect(c, qr_x - pad, qr_y - pad, qr_s + 2 * pad, qr_s + 2 * pad, 8,
                 fill=WHITE, stroke=NAVY, sw=1.2)
    c.drawImage(qr_img, qr_x, qr_y, qr_s, qr_s)

    c.setFont(FONT_B, 9.5)
    c.setFillColor(NAVY)
    c.drawCentredString(rcx, qr_y - 14, "Scan to get matched today!")
    c.setFont(FONT_R, 8.5)
    c.setFillColor(MUTED)
    c.drawCentredString(rcx, qr_y - 26, "matchcareaba.com")

    # Logo at bottom of panel — bigger, near bottom
    logo_s3 = 95
    logo_x3 = rcx - logo_s3 / 2
    logo_y3 = 32
    c.drawImage(logo_img, logo_x3, logo_y3, logo_s3, logo_s3,
                preserveAspectRatio=True, mask="auto")

    # Bottom gold band
    draw_band(c, right_x, 0, PANEL_W, 28, GOLD)
    c.setFont(FONT_B, 9.5)
    c.setFillColor(NAVY)
    c.drawCentredString(rcx, 10, "matchcareaba.com")

    # Panel fold guides
    c.setStrokeColor(HexColor("#DDDDDD"))
    c.setLineWidth(0.25)
    c.setDash(3, 3)
    c.line(PANEL_W, 0, PANEL_W, HEIGHT)
    c.line(2 * PANEL_W, 0, 2 * PANEL_W, HEIGHT)
    c.setDash()


# ─── Build PDF ──────────────────────────────────────────────────

def build():
    c = canvas.Canvas(OUTPUT, pagesize=(WIDTH, HEIGHT))
    c.setTitle("Match Care ABA - Tri-Fold Brochure")

    # Page 1: Outside
    draw_outside(c)
    c.showPage()

    # Page 2: Inside
    draw_inside(c)

    c.save()
    print(f"Brochure generated: {OUTPUT}")


if __name__ == "__main__":
    build()
