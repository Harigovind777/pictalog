"""Text for the printed catalog in English and any of India's scripts.

ReportLab draws with one font at a time and doesn't join letters by itself. So text is split into runs of one script,
each run gets a Noto font that has its letters, and HarfBuzz shapes the run so that क + ् + ष prints as क्ष. Urdu,
Kashmiri and Sindhi runs read right to left and are put in visual order here."""

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from reportlab.lib.abag import ABag
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont, shapeFragWord
from reportlab.pdfgen.canvas import Canvas

FONT_DIR = Path(__file__).parent / "fonts"
BASE = {False: "DejaVuSans", True: "DejaVuSans-Bold"}  # Latin, digits, ₹ € £ and punctuation

# Noto font name → Unicode blocks it draws.
SCRIPTS: dict[str, list[tuple[int, int]]] = {
    "Devanagari": [(0x0900, 0x097F), (0xA8E0, 0xA8FF), (0x1CD0, 0x1CFF)],
    "Bengali": [(0x0980, 0x09FF)],
    "Gurmukhi": [(0x0A00, 0x0A7F)],
    "Gujarati": [(0x0A80, 0x0AFF)],
    "Oriya": [(0x0B00, 0x0B7F)],
    "Tamil": [(0x0B80, 0x0BFF)],
    "Telugu": [(0x0C00, 0x0C7F)],
    "Kannada": [(0x0C80, 0x0CFF)],
    "Malayalam": [(0x0D00, 0x0D7F)],
    "Arabic": [(0x0600, 0x06FF), (0x0750, 0x077F), (0x08A0, 0x08FF), (0xFB50, 0xFDFF), (0xFE70, 0xFEFF)],
    "OlChiki": [(0x1C50, 0x1C7F)],
    "MeeteiMayek": [(0xAAE0, 0xAAFF), (0xABC0, 0xABFF)],
}
RIGHT_TO_LEFT = {"Arabic"}
_JOINERS = "‌‍"  # zero-width (non-)joiners shape with the letters around them
_DANDAS = "।॥"  # full stops shared by most Indian scripts
_BASE_TOKENS = re.compile(r"\s+|\d(?:[\d.,]*\d)?|[^\s\d]+")
_ARABIC_DIGITS = re.compile(r"([٠-٩۰-۹][٠-٩۰-۹.,٫٬]*)")


def _script(ch: str) -> str | None:
    code = ord(ch)
    return next((name for name, blocks in SCRIPTS.items() if any(lo <= code <= hi for lo, hi in blocks)), None)


def font_name(script: str | None, bold: bool) -> str:
    if script is None:
        return BASE[bold]
    return f"NotoSans{script}-{'Bold' if bold else 'Regular'}"


def register_fonts() -> None:
    if BASE[False] in pdfmetrics.getRegisteredFontNames():
        return
    pdfmetrics.registerFont(TTFont(BASE[False], str(FONT_DIR / "DejaVuSans.ttf")))
    pdfmetrics.registerFont(TTFont(BASE[True], str(FONT_DIR / "DejaVuSans-Bold.ttf")))
    for script in SCRIPTS:
        for bold in (False, True):
            name = font_name(script, bold)
            pdfmetrics.registerFont(TTFont(name, str(FONT_DIR / "noto" / f"{name}.ttf")))


def runs(text: str) -> list[tuple[str | None, str]]:
    """Split text into (script, text) runs; None is the base font. Vowel signs, viramas, joiners and dandas stay with
    the letters before them. Base-font text is split further into words, spaces and numbers for right-to-left
    ordering."""
    out: list[tuple[str | None, str]] = []
    for ch in text:
        script = _script(ch)
        joins = unicodedata.category(ch)[0] == "M" or ch in _JOINERS or ch in _DANDAS
        if out and (script == out[-1][0] or (joins and out[-1][0] is not None)):
            out[-1] = (out[-1][0], out[-1][1] + ch)
        else:
            out.append((script, ch))
    split: list[tuple[str | None, str]] = []
    for script, part in out:
        if script is None:
            split += [(None, t) for t in _BASE_TOKENS.findall(part)]
        elif script in RIGHT_TO_LEFT:
            split += [(script, t) for t in _ARABIC_DIGITS.split(part) if t]  # numbers read left to right
        else:
            split.append((script, part))
    return split


def _direction(script: str | None, part: str) -> str:
    if script in RIGHT_TO_LEFT and not _ARABIC_DIGITS.fullmatch(part):
        return "R"
    if script or any(ch.isalpha() or ch.isdigit() for ch in part):
        return "L"
    return "N"  # spaces and punctuation take the direction around them


def visual_order(parts: list[tuple[str | None, str]]) -> list[tuple[str | None, str]]:
    """Runs in the order they're drawn left to right: a line that starts in Urdu reads from the right, and Urdu words
    inside an English line read right to left among themselves."""
    dirs = [_direction(s, p) for s, p in parts]
    strong = [d for d in dirs if d != "N"]
    base = strong[0] if strong else "L"
    resolved = []
    for i, d in enumerate(dirs):
        if d == "N":
            before = next((x for x in reversed(dirs[:i]) if x != "N"), base)
            after = next((x for x in dirs[i + 1 :] if x != "N"), base)
            d = before if before == after else base
        resolved.append(d)
    groups: list[tuple[str, list[tuple[str | None, str]]]] = []
    for d, part in zip(resolved, parts):
        if groups and groups[-1][0] == d:
            groups[-1][1].append(part)
        else:
            groups.append((d, [part]))
    if base == "R":
        groups.reverse()
    return [part for d, members in groups for part in (reversed(members) if d == "R" else members)]


@dataclass
class Piece:
    font: str
    text: str  # a ReportLab ShapedStr when the run was shaped
    width: float


def layout(text: str, size: float, bold: bool = False) -> list[Piece]:
    register_fonts()
    pieces = []
    for script, part in visual_order(runs(text)):
        font = font_name(script, bold)
        width = pdfmetrics.stringWidth(part, font, size)
        if script and not _ARABIC_DIGITS.fullmatch(part):  # HarfBuzz would turn Urdu numbers around
            width, (_, part) = shapeFragWord([width, (ABag(fontName=font, fontSize=size), part)], force=True)
        pieces.append(Piece(font, part, width))
    return pieces


def width(text: str, size: float, bold: bool = False) -> float:
    return sum(p.width for p in layout(text, size, bold))


def _drop_last_letter(text: str) -> str:
    """Remove the last letter with its vowel signs, virama and joiners, so a cut never leaves half a syllable."""
    text = text[:-1]
    while text and (unicodedata.category(text[-1])[0] == "M" or text[-1] in _JOINERS):
        text = text[:-1]
    return text


def fit(text: str, size: float, max_width: float, bold: bool = False) -> str:
    if width(text, size, bold) <= max_width:
        return text
    while text and width(text + "…", size, bold) > max_width:
        text = _drop_last_letter(text)
    return text.rstrip() + "…"


def draw(c: Canvas, x: float, y: float, text: str, size: float, bold: bool = False, align: str = "left") -> None:
    pieces = layout(text, size, bold)
    total = sum(p.width for p in pieces)
    x -= {"left": 0, "centre": total / 2, "right": total}[align]
    for piece in pieces:
        c.setFont(piece.font, size)
        c.drawString(x, y, piece.text)
        x += piece.width
