#!/usr/bin/env python3
"""Generate Match Care ABA flyer — website-style design."""

import os
import math
import qrcode
import numpy as np
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import HexColor
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PIL import Image, ImageDraw
from io import BytesIO

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT = os.path.join(SCRIPT_DIR, "matchcareaba-flyer.pdf")
LOGO = os.path.join(SCRIPT_DIR, "logo.jpeg")
HERO_IMG = os.path.join(SCRIPT_DIR, "family-hero.jpeg")
WIDTH, HEIGHT = letter  # 612 x 792

# Website color palette
NAVY = HexColor("#1B3A6B")
TEAL = HexColor("#0891B2")
TEAL_LIGHT = HexColor("#22D3EE")
GOLD = HexColor("#F5A623")
GOLD_LIGHT = HexColor("#FFD166")
PEACH = HexColor("#FDEEE0")
WHITE = HexColor("#FFFFFF")
TEXT_DARK = HexColor("#1E293B")
MUTED = HexColor("#64748B")
SHADOW = HexColor("#E5D5C8")

FONT_B = "Helvetica-Bold"
FONT_R = "Helvetica"


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


def make_circular_image(path, diameter):
    img = Image.open(path).convert("RGBA")
    s = min(img.width, img.height)
    left = max(0, (img.width - s) // 8)
    top = (img.height - s) // 2
    img = img.crop((left, top, left + s, top + s))
    scale = 5
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


def draw_pill(c, x, y, w, h, color, text, font_size=12):
    rounded_rect(c, x, y, w, h, h / 2, fill=color)
    c.setFont(FONT_B, font_size)
    c.setFillColor(WHITE)
    c.drawString(x + 14, y + h / 2 - 4, text)


def build():
    c = canvas.Canvas(OUTPUT, pagesize=letter)
    c.setTitle("Match Care ABA - Free ABA Therapy Matching")

    M = 36  # margin

    # ══════════════════════════════════════════════
    # WARM PEACH BACKGROUND (matches website)
    # ══════════════════════════════════════════════
    c.setFillColor(PEACH)
    c.rect(0, 0, WIDTH, HEIGHT, fill=1, stroke=0)

    # ══════════════════════════════════════════════
    # GIANT GOLD CIRCLE — top-left background
    # ══════════════════════════════════════════════
    c.setFillColor(HexColor("#C5E8ED"))
    c.circle(-60, HEIGHT + 60, 380, fill=1, stroke=0)

    # Light blue circle — bottom-right background (smaller)
    c.setFillColor(HexColor("#C5E8ED"))
    c.circle(WIDTH + 40, -40, 260, fill=1, stroke=0)

    # ══════════════════════════════════════════════
    # LOGO — centered at top
    # ══════════════════════════════════════════════
    logo_s = 150
    logo_x = (WIDTH - logo_s) / 2
    logo_y = HEIGHT - logo_s - 6
    logo_img = remove_white_bg(LOGO)
    c.drawImage(logo_img, logo_x, logo_y, logo_s, logo_s,
                preserveAspectRatio=True, mask="auto")

    # ══════════════════════════════════════════════
    # HEADLINE (left side)
    # ══════════════════════════════════════════════
    hl_y = logo_y + 8
    c.setFont(FONT_B, 36)
    c.setFillColor(NAVY)
    for line in ["JUST RECEIVED", "AN AUTISM", "DIAGNOSIS?"]:
        c.drawString(M, hl_y, line)
        hl_y -= 42

    # Sub-headline — teal (website CTA color)
    hl_y -= 2
    c.setFont(FONT_B, 20)
    c.setFillColor(TEAL)
    c.drawString(M, hl_y, "WE'LL FIND YOUR ABA")
    hl_y -= 24
    c.drawString(M, hl_y, "THERAPY PROVIDER \u2014 FREE!")

    # Description — muted text, clean, with gold border
    hl_y -= 34
    desc_top = hl_y + 6
    desc_lines = [
        "WE HELP YOU NAVIGATE THE NEXT STEPS BY CONNECTING",
        "YOU WITH TRUSTED ABA PROVIDERS DEDICATED TO",
        "HELPING YOUR CHILD GROW AND THRIVE.",
    ]
    desc_bottom = desc_top - len(desc_lines) * 12 - 6
    rounded_rect(c, M - 10, desc_bottom, 310, desc_top - desc_bottom + 8, 8,
                 stroke=GOLD, sw=1.2)
    c.setFont(FONT_R, 9.5)
    c.setFillColor(MUTED)
    for line in desc_lines:
        c.drawString(M, hl_y, line)
        hl_y -= 12

    # ══════════════════════════════════════════════
    # CIRCULAR HERO PHOTO (right side, teal+gold frame)
    # ══════════════════════════════════════════════
    img_d = 250
    img_x = WIDTH - img_d - 16
    img_y = HEIGHT - img_d - 120

    icx = img_x + img_d / 2
    icy = img_y + img_d / 2
    pr = img_d / 2

    # Teal shadow circle (offset top-left, like website hero)
    c.setFillColor(HexColor("#C5E8ED"))
    c.circle(icx - 10, icy + 10, pr + 10, fill=1, stroke=0)

    # Gold shadow circle (offset bottom-right)
    c.setFillColor(HexColor("#FDE4B0"))
    c.circle(icx + 10, icy - 10, pr + 10, fill=1, stroke=0)

    # White border
    c.setFillColor(WHITE)
    c.circle(icx, icy, pr + 5, fill=1, stroke=0)

    hero = make_circular_image(HERO_IMG, img_d)
    c.drawImage(hero, img_x, img_y, img_d, img_d, mask="auto")

    # Decorative dots (gold + teal, website style)
    c.setFillColor(GOLD)
    c.circle(icx - 55, icy + pr + 24, 14, fill=1, stroke=0)
    c.setFillColor(TEAL)
    c.circle(icx + 60, icy - pr + 5, 9, fill=1, stroke=0)


    # ══════════════════════════════════════════════
    # CONTENT CARDS — 2×2 grid on peach background
    # ══════════════════════════════════════════════
    PAGE_W = WIDTH - 2 * M
    card_gap = 16
    card_w = (PAGE_W - card_gap) / 2
    card_h = 132
    row_gap = 14

    cards_top = hl_y - 18
    r1_y = cards_top - card_h
    r2_y = r1_y - row_gap - card_h
    c1_x = M
    c2_x = M + card_w + card_gap

    pill_w = card_w - 32
    pill_h = 22
    pgap = 28

    # ── Card 1: HOW IT WORKS ──
    rounded_rect(c, c1_x + 2, r1_y - 2, card_w, card_h, 40, fill=SHADOW)
    rounded_rect(c, c1_x, r1_y, card_w, card_h, 40, fill=WHITE)

    c.setFillColor(TEAL)
    c.circle(c1_x + 18, r1_y + card_h - 20, 4, fill=1, stroke=0)
    c.setFont(FONT_B, 12.5)
    c.setFillColor(NAVY)
    c.drawString(c1_x + 28, r1_y + card_h - 24, "HOW IT WORKS")

    py = r1_y + card_h - 50
    draw_pill(c, c1_x + 16, py, pill_w, pill_h, TEAL, "FILL OUT ONE SHORT FORM", 9)
    py -= pgap
    draw_pill(c, c1_x + 16, py, pill_w, pill_h, TEAL_LIGHT, "WE FIND YOUR MATCH", 9)
    py -= pgap
    draw_pill(c, c1_x + 16, py, pill_w, pill_h, TEAL, "GET CONNECTED & START THERAPY", 8)

    # ── Card 2: HOW ABA HELPS (taller + super-rounded, narrower) ──
    aba_w = card_w - 40
    aba_h = card_h + 14
    aba_y = r1_y - 14
    aba_r = 50
    aba_x = c2_x + 20
    rounded_rect(c, aba_x + 2, aba_y - 2, aba_w, aba_h, aba_r, fill=SHADOW)
    rounded_rect(c, aba_x, aba_y, aba_w, aba_h, aba_r, fill=WHITE)

    c.setFillColor(GOLD)
    c.circle(aba_x + 18, aba_y + aba_h - 20, 4, fill=1, stroke=0)
    c.setFont(FONT_B, 13.5)
    c.setFillColor(NAVY)
    c.drawString(aba_x + 28, aba_y + aba_h - 24, "HOW ABA HELPS")

    by = aba_y + aba_h - 44
    for main, sub in [
        ("Communication skills (asking,", "sharing, social interaction)"),
        ("Daily living skills (dressing,", "eating, routines)"),
        ("Emotional regulation", "(coping tools, transitions)"),
        ("Independence & confidence", ""),
    ]:
        c.setFillColor(GOLD)
        c.circle(aba_x + 18, by + 3, 3.5, fill=1, stroke=0)
        c.setFont(FONT_R, 10.5)
        c.setFillColor(TEXT_DARK)
        c.drawString(aba_x + 28, by, main)
        if sub:
            by -= 12
            c.drawString(aba_x + 28, by, sub)
        by -= 15

    # ── Card 3: WE MATCH YOU WITH (overlaps HOW IT WORKS) ──
    wmy_y = r2_y + 26
    rounded_rect(c, c1_x + 2, wmy_y - 2, card_w, card_h, 45, fill=SHADOW)
    rounded_rect(c, c1_x, wmy_y, card_w, card_h, 45, fill=WHITE)

    c.setFillColor(TEAL)
    c.circle(c1_x + 18, wmy_y + card_h - 20, 4, fill=1, stroke=0)
    c.setFont(FONT_B, 12.5)
    c.setFillColor(NAVY)
    c.drawString(c1_x + 28, wmy_y + card_h - 24, "WE MATCH YOU WITH")

    tp = wmy_y + card_h - 50
    draw_pill(c, c1_x + 16, tp, pill_w, pill_h, TEAL, "Clinic-Based Therapy", 9)
    tp -= pgap
    draw_pill(c, c1_x + 16, tp, pill_w, pill_h, TEAL_LIGHT, "In-Home Therapy", 9)
    tp -= pgap
    draw_pill(c, c1_x + 16, tp, pill_w, pill_h, TEAL, "In School/Daycare Therapy", 9)

    # ── Card 4: WHY MATCH CARE (narrower, overlaps HOW ABA HELPS) ──
    wmc_w = card_w - 60
    wmc_x = c2_x + 30
    wmc_y = r2_y + 14
    rounded_rect(c, wmc_x + 2, wmc_y - 2, wmc_w, card_h, 36, fill=SHADOW)
    rounded_rect(c, wmc_x, wmc_y, wmc_w, card_h, 36, fill=WHITE)

    c.setFillColor(TEAL)
    c.circle(wmc_x + 18, wmc_y + card_h - 20, 4, fill=1, stroke=0)
    c.setFont(FONT_B, 13.5)
    c.setFillColor(NAVY)
    c.drawString(wmc_x + 28, wmc_y + card_h - 24, "WHY MATCH CARE")

    wy = wmc_y + card_h - 42
    for item in [
        "Free for families, always",
        "Pre-verified providers",
        "Insurance matched first",
        "No long waitlists",
        "Personalized matching",
    ]:
        c.setFillColor(TEAL)
        c.circle(wmc_x + 18, wy + 3, 3.5, fill=1, stroke=0)
        c.setFont(FONT_R, 10.5)
        c.setFillColor(TEXT_DARK)
        c.drawString(wmc_x + 28, wy, item)
        wy -= 17

    # ══════════════════════════════════════════════
    # BOTTOM — teal tagline + QR + navy banner
    # ══════════════════════════════════════════════

    # Teal tagline pill (website CTA style)
    tag_w = card_w + 16
    tag_h = 40
    tag_x = M
    tag_y = r2_y - tag_h - 16
    rounded_rect(c, tag_x, tag_y, tag_w, tag_h, tag_h / 2, fill=TEAL)
    c.setFont(FONT_B, 10.5)
    c.setFillColor(WHITE)
    c.drawCentredString(tag_x + tag_w / 2, tag_y + 23,
                        "Match Care ABA \u2014 your personal")
    c.drawCentredString(tag_x + tag_w / 2, tag_y + 9,
                        "matching service. Completely free.")

    # QR Code + contact — larger, shifted right
    qr_s = 0.95 * inch
    qr_img = make_qr("https://matchcareaba.com")
    qr_x = c2_x + 20
    qr_y = tag_y + (tag_h - qr_s) / 2 - 4
    pad = 5
    rounded_rect(c, qr_x - pad, qr_y - pad, qr_s + 2 * pad, qr_s + 2 * pad, 8,
                 fill=WHITE, stroke=NAVY, sw=1.2)
    c.drawImage(qr_img, qr_x, qr_y, qr_s, qr_s)

    info_x = qr_x + qr_s + 14
    info_cy = qr_y + qr_s / 2
    c.setFont(FONT_B, 11)
    c.setFillColor(NAVY)
    c.drawString(info_x, info_cy + 14, "SCAN TO GET")
    c.drawString(info_x, info_cy, "STARTED!")
    c.setFont(FONT_B, 11)
    c.setFillColor(NAVY)
    c.drawString(info_x, info_cy - 18, "matchcareaba.com")
    c.setFont(FONT_B, 10)
    c.setFillColor(NAVY)
    c.drawString(info_x, info_cy - 34, "matchcareaba@gmail.com")

    # Navy bottom banner
    banner_h = 36
    c.setFillColor(NAVY)
    c.rect(0, 0, WIDTH, banner_h, fill=1, stroke=0)
    c.setFont(FONT_B, 11)
    c.setFillColor(WHITE)
    c.drawCentredString(WIDTH / 2, 18,
                        "100% Free for Families. Always.  |  matchcareaba.com")

    c.save()
    print(f"Flyer generated: {OUTPUT}")


if __name__ == "__main__":
    build()
