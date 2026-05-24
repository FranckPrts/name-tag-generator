"""
generate_nametags.py
--------------------
Fills a name tag template (2-col x 4-row grid) from a CSV.

CSV expected columns (case-insensitive):
  first_name, last_name, type, school

Usage:
  python generate_nametags.py
  python generate_nametags.py --csv attendees.csv --template nametag_template.pdf --out filled_nametags.pdf

Template page size: letter (612 x 792 pt).
"""

import argparse
import io
import csv
from pathlib import Path

import config

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ─────────────────────────────────────────────
# GRID COORDINATES  (reportlab: bottom-up Y)
# ─────────────────────────────────────────────

PAGE_W, PAGE_H = 612.0, 792.0

# Each slot: (name_box_center_x, name_box_center_y, type_center_x, type_center_y, school_center_x, school_center_y)
# Slot order: left→right, top→bottom  (slots 0-7 for 8 tags per page)
SLOTS = [
    # Row 1
    (176, 696,  130, 622,  243, 622),   # 0 – top-left
    (438, 696,  392, 622,  505, 622),   # 1 – top-right
    # Row 2
    (176, 511,  130, 437,  243, 437),   # 2
    (438, 511,  392, 437,  505, 437),   # 3
    # Row 3
    (176, 318,  130, 244,  243, 244),   # 4
    (438, 318,  392, 244,  505, 244),   # 5
    # Row 4
    (176, 132,  130,  58,  243,  58),   # 6 – bottom-left
    (438, 132,  392,  58,  505,  58),   # 7 – bottom-right
]

# Name box dimensions (width × height in pts)
NAME_BOX_W = 210
NAME_BOX_H = 90

# Pill text bounds (width only — no opaque cover drawn; template shows through)
TYPE_PILL_W  = 120   # wide pill ("High School Student")
SCHOOL_PILL_W = 74   # narrow pill (school name)

# Font sizes (text auto-shrinks to fit pill width above)
NAME_FONT_SIZE   = 16
TYPE_FONT_SIZE   = 9
SCHOOL_FONT_SIZE = 8.5

# Nudge pill labels down to sit inside the template pills (pts, reportlab Y)
PILL_TEXT_Y_ADJ  = -9

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def read_csv(path: str) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        # normalise column names to lowercase
        rows = []
        for row in reader:
            rows.append({k.strip().lower(): v.strip() for k, v in row.items()})
    return rows


def draw_overlay(slots_data: list[dict | None]) -> bytes:
    """
    Render one overlay page for up to 8 attendees.
    slots_data: list of dicts with keys first_name, last_name, type, school
                (None = empty slot, leave blank)
    Returns PDF bytes.
    """
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(PAGE_W, PAGE_H))

    for idx, person in enumerate(slots_data):
        if person is None:
            continue

        nx, ny, tx, ty, sx, sy = SLOTS[idx]

        # ── Name: first line, last name underneath ─────
        _draw_name_stacked(
            c,
            person.get("first_name", ""),
            person.get("last_name", ""),
            nx,
            ny,
            max_width=NAME_BOX_W - 10,
            font="Helvetica-Bold",
            size=NAME_FONT_SIZE,
            color=(0.18, 0.18, 0.18),
        )

        # ── Invitee type (text only — no opaque cover box) ───
        _draw_text_centered(
            c,
            person.get("type", ""),
            tx,
            ty + PILL_TEXT_Y_ADJ,
            max_width=TYPE_PILL_W - 6,
            font="Helvetica",
            size=TYPE_FONT_SIZE,
            color=(0.25, 0.25, 0.25),
        )

        # ── School (text only — no opaque cover box) ─────────
        _draw_text_centered(
            c,
            person.get("school", ""),
            sx,
            sy + PILL_TEXT_Y_ADJ,
            max_width=SCHOOL_PILL_W - 6,
            font="Helvetica",
            size=SCHOOL_FONT_SIZE,
            color=(0.25, 0.25, 0.25),
        )

    c.save()
    buf.seek(0)
    return buf.read()


def _fit_font_size(c, text: str, font: str, size: float, max_width: float) -> float:
    current_size = size
    while current_size > 4:
        c.setFont(font, current_size)
        if c.stringWidth(text, font, current_size) <= max_width:
            return current_size
        current_size -= 0.5
    return 4


def _baseline_for_vertical_center(cy: float, font: str, size: float) -> float:
    """Return drawString Y so text is vertically centred at cy."""
    ascent = pdfmetrics.getAscent(font) / 1000.0 * size
    descent = pdfmetrics.getDescent(font) / 1000.0 * size  # negative
    return cy - (ascent + descent) / 2.0


def _draw_text_at_baseline(c, text: str, cx: float, baseline: float,
                           font: str, size: float, color: tuple):
    r, g, b = color
    c.setFillColorRGB(r, g, b)
    c.setFont(font, size)
    text_w = c.stringWidth(text, font, size)
    c.drawString(cx - text_w / 2, baseline, text)


def _draw_text_centered(c, text: str, cx: float, cy: float,
                         max_width: float, font: str, size: float,
                         color: tuple):
    """Draw text centred at (cx, cy), auto-shrinking to fit max_width."""
    if not text:
        return
    current_size = _fit_font_size(c, text, font, size, max_width)
    baseline = _baseline_for_vertical_center(cy, font, current_size)
    _draw_text_at_baseline(c, text, cx, baseline, font, current_size, color)


def _draw_name_stacked(c, first_name: str, last_name: str, cx: float, cy: float,
                       max_width: float, font: str, size: float, color: tuple):
    """Draw first name on top, last name underneath, centred in the name box."""
    first = first_name.strip()
    last = last_name.strip()
    if not first and not last:
        return
    if not last:
        _draw_text_centered(c, first, cx, cy, max_width, font, size, color)
        return
    if not first:
        _draw_text_centered(c, last, cx, cy, max_width, font, size, color)
        return

    current_size = size
    while current_size > 4:
        c.setFont(font, current_size)
        if (c.stringWidth(first, font, current_size) <= max_width
                and c.stringWidth(last, font, current_size) <= max_width):
            break
        current_size -= 0.5

    line_gap = current_size * 0.3
    ascent = pdfmetrics.getAscent(font) / 1000.0 * current_size
    descent = pdfmetrics.getDescent(font) / 1000.0 * current_size
    line_step = ascent - descent + line_gap

    block_center = cy
    first_baseline = _baseline_for_vertical_center(
        block_center + line_step / 2, font, current_size
    )
    second_baseline = _baseline_for_vertical_center(
        block_center - line_step / 2, font, current_size
    )

    _draw_text_at_baseline(c, first, cx, first_baseline, font, current_size, color)
    _draw_text_at_baseline(c, last, cx, second_baseline, font, current_size, color)


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def ensure_example_csv():
    """Write the example CSV from config if it does not exist."""
    csv_path = Path(config.CSV)
    if not csv_path.exists():
        csv_path.write_text(config.EXAMPLE_CSV, encoding="utf-8")


def generate(csv_path: str, template_path: str, out_path: str):
    attendees = read_csv(csv_path)
    writer = PdfWriter()
    PER_PAGE = 8

    for page_start in range(0, len(attendees), PER_PAGE):
        batch = attendees[page_start : page_start + PER_PAGE]
        # Pad to 8 slots
        slots_data = batch + [None] * (PER_PAGE - len(batch))

        # Fresh template read each page — merge_page mutates in place and would
        # otherwise bleed the first page's overlay into every subsequent page.
        tpl_page = PdfReader(template_path).pages[0]

        overlay_bytes = draw_overlay(slots_data)
        overlay_page = PdfReader(io.BytesIO(overlay_bytes)).pages[0]

        tpl_page.merge_page(overlay_page)
        writer.add_page(tpl_page)

    with open(out_path, "wb") as f:
        writer.write(f)

    print(f"✓  Generated {out_path}  ({len(attendees)} attendees, {writer._root_object['/Pages']['/Count']} page(s))")


if __name__ == "__main__":
    ensure_example_csv()

    parser = argparse.ArgumentParser(description="Fill name tag template from CSV")
    parser.add_argument("--csv", default=config.CSV, help="Path to attendees CSV")
    parser.add_argument("--template", default=config.TEMPLATE, help="Path to name tag template PDF")
    parser.add_argument("--out", default=config.OUT, help="Output PDF path")
    args = parser.parse_args()
    generate(args.csv, args.template, args.out)
