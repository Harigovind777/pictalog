"""Printable catalog: a cover page, then a 2 × 3 grid of products per A4 page, one cell per variant."""

import io
import re
from collections.abc import Callable
from datetime import date
from pathlib import Path

import httpx
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas

from pictalog.models import Catalog, Product, User, Variant

FONT_DIR = Path(__file__).parent / "fonts"
REGULAR, BOLD = "DejaVuSans", "DejaVuSans-Bold"  # covers ₹, €, £ and accented Latin
INK, MUTED, PLACEHOLDER = HexColor("#1c1c1e"), HexColor("#6e6e73"), HexColor("#eeeeef")
PAGE_W, PAGE_H = A4
MARGIN, GUTTER = 15 * mm, 8 * mm
COLS, ROWS = 2, 3
CELL_W = (PAGE_W - 2 * MARGIN - (COLS - 1) * GUTTER) / COLS
CELL_H = (PAGE_H - 2 * MARGIN - 10 * mm - (ROWS - 1) * GUTTER) / ROWS  # 10 mm reserved for the footer
TEXT_H = 20 * mm

Fetch = Callable[..., httpx.Response]


def _register_fonts() -> None:
    if REGULAR not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(REGULAR, str(FONT_DIR / "DejaVuSans.ttf")))
        pdfmetrics.registerFont(TTFont(BOLD, str(FONT_DIR / "DejaVuSans-Bold.ttf")))


def _default_fetch(url: str, timeout: float) -> httpx.Response:
    return httpx.get(url, timeout=timeout, follow_redirects=True)


def price_label(price_text: str | None, currency: str) -> str:
    text = (price_text or "").strip()
    if text and currency and re.fullmatch(r"[\d.,\s]+", text):
        return f"{currency}{text}"
    return text


def variant_line(variant: Variant) -> str:
    parts = [f"Size {variant.size}" if variant.size else None, variant.colour, variant.material]
    return " · ".join(p for p in parts if p)


def _fit(text: str, font: str, size: float, width: float) -> str:
    if pdfmetrics.stringWidth(text, font, size) <= width:
        return text
    while text and pdfmetrics.stringWidth(text + "…", font, size) > width:
        text = text[:-1]
    return text.rstrip() + "…"


def _image_bytes(variant: Variant, storage, fetch: Fetch) -> bytes | None:
    try:
        if variant.image_key:
            return storage.read(variant.image_key)
        if variant.image_url_source and variant.image_url_source.startswith(("http://", "https://")):
            response = fetch(variant.image_url_source, timeout=5.0)
            if getattr(response, "status_code", 200) < 400:
                return response.content
    except Exception:
        return None
    return None


def _draw_image(c: Canvas, data: bytes | None, x: float, y: float, size: float) -> None:
    if data:
        try:
            c.drawImage(ImageReader(io.BytesIO(data)), x, y, size, size, preserveAspectRatio=True, anchor="c", mask="auto")
            return
        except Exception:
            pass
    c.setFillColor(PLACEHOLDER)
    c.roundRect(x, y, size, size, 3 * mm, stroke=0, fill=1)
    c.setFillColor(MUTED)
    c.setFont(REGULAR, 10)
    c.drawCentredString(x + size / 2, y + size / 2 - 3, "No image")


def _cover(c: Canvas, catalog: Catalog, user: User, storage, has_products: bool) -> None:
    if user.logo_key:
        try:
            logo = ImageReader(io.BytesIO(storage.read(user.logo_key)))
            c.drawImage(logo, PAGE_W / 2 - 30 * mm, PAGE_H / 2 + 40 * mm, 60 * mm, 30 * mm,
                        preserveAspectRatio=True, anchor="c", mask="auto")
        except Exception:
            pass
    c.setFillColor(INK)
    c.setFont(BOLD, 26)
    c.drawCentredString(PAGE_W / 2, PAGE_H / 2 + 18 * mm, _fit(user.company_name, BOLD, 26, PAGE_W - 2 * MARGIN))
    c.setFont(REGULAR, 16)
    c.drawCentredString(PAGE_W / 2, PAGE_H / 2 + 4 * mm, _fit(catalog.name, REGULAR, 16, PAGE_W - 2 * MARGIN))
    c.setFillColor(MUTED)
    c.setFont(REGULAR, 10)
    c.drawCentredString(PAGE_W / 2, PAGE_H / 2 - 6 * mm, date.today().strftime("%B %Y"))
    if not has_products:
        c.drawCentredString(PAGE_W / 2, PAGE_H / 2 - 20 * mm, "This catalog has no products yet.")
    c.showPage()


def _footer(c: Canvas, user: User, page: int) -> None:
    c.setFillColor(MUTED)
    c.setFont(REGULAR, 8)
    c.drawString(MARGIN, MARGIN, user.company_name)
    c.drawRightString(PAGE_W - MARGIN, MARGIN, str(page))


def _cell(c: Canvas, product: Product, variant: Variant, currency: str, image: bytes | None, x: float, top: float) -> None:
    size = min(CELL_W, CELL_H - TEXT_H)
    _draw_image(c, image, x + (CELL_W - size) / 2, top - size, size)
    y = top - size - 6 * mm
    c.setFillColor(INK)
    c.setFont(BOLD, 11)
    c.drawString(x, y, _fit(product.name or variant.sku or "Untitled", BOLD, 11, CELL_W))
    line = variant_line(variant)
    if line:
        y -= 5 * mm
        c.setFillColor(MUTED)
        c.setFont(REGULAR, 9)
        c.drawString(x, y, _fit(line, REGULAR, 9, CELL_W))
    price = price_label(variant.price_text, currency)
    if price:
        y -= 5.5 * mm
        c.setFillColor(INK)
        c.setFont(BOLD, 11)
        c.drawString(x, y, _fit(price, BOLD, 11, CELL_W))


def render_catalog_pdf(catalog: Catalog, user: User, storage, fetch: Fetch = _default_fetch) -> bytes:
    _register_fonts()
    buf = io.BytesIO()
    c = Canvas(buf, pagesize=A4)
    c.setTitle(catalog.name)
    c.setAuthor(user.company_name)
    cells = [(p, v) for p in catalog.products for v in p.variants]
    _cover(c, catalog, user, storage, bool(cells))
    per_page = COLS * ROWS
    for index, (product, variant) in enumerate(cells):
        slot = index % per_page
        col, row = slot % COLS, slot // COLS
        x = MARGIN + col * (CELL_W + GUTTER)
        top = PAGE_H - MARGIN - row * (CELL_H + GUTTER)
        _cell(c, product, variant, catalog.currency, _image_bytes(variant, storage, fetch), x, top)
        if slot == per_page - 1 or index == len(cells) - 1:
            _footer(c, user, index // per_page + 1)
            c.showPage()
    c.save()
    return buf.getvalue()
