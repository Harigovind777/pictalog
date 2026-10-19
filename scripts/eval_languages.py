"""How accurately Pictalog reads product lists in India's languages.

For each language the same four products are read from a spreadsheet (no AI), a typed list (AI reader), a photo of
a printed list (OCR, then the AI reader), and each product is described in English for its photo. Every answer is
checked against the known products.

    uv run python scripts/eval_languages.py                      # everything, with the helper's default models
    uv run python scripts/eval_languages.py --kinds photo --no-vision --only Hindi,Tamil

Needs Ollama (scripts/dev.sh starts one on port 11435) for every kind except "sheet".
"""

import argparse
import io
import re
import sys
import time
import unicodedata
from pathlib import Path

from openpyxl import Workbook
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from language_samples import LANGUAGES, Language, Product, lines, rows  # noqa: E402

from pictalog.parsing.headings import normalise  # noqa: E402
from pictalog.parsing.mapping import find_table  # noqa: E402
from pictalog.parsing.price import parse_price  # noqa: E402
from pictalog.parsing.rows import rows_to_items  # noqa: E402
from pictalog.parsing.tables import read_tables  # noqa: E402
from pictalog.pdf_text import FONT_DIR, runs, visual_order  # noqa: E402
from pictalog_helper.config import HelperSettings  # noqa: E402
from pictalog_helper.prompts import PromptWriter  # noqa: E402
from pictalog_helper.reader import DocumentReader  # noqa: E402

KINDS = ["sheet", "text", "photo", "table", "rewrite"]


# ---- making the documents -------------------------------------------------------------------------------------------


def xlsx(language: Language) -> bytes:
    wb = Workbook()
    for row in rows(language):
        wb.active.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _font(script: str | None, size: int) -> ImageFont.FreeTypeFont:
    path = FONT_DIR / "DejaVuSans.ttf" if script is None else FONT_DIR / "noto" / f"NotoSans{script}-Regular.ttf"
    return ImageFont.truetype(str(path), size, layout_engine=ImageFont.Layout.RAQM)


def _draw_line(draw: ImageDraw.ImageDraw, x: float, y: float, text: str, size: int) -> None:
    for script, part in visual_order(runs(text)):
        font = _font(script, size)
        draw.text((x, y), part, fill="#2a2a2a", font=font, anchor="ls")  # on a shared baseline
        x += font.getlength(part)


def photo(language: Language) -> bytes:
    """A phone photo of the printed list: slightly turned paper on a wooden table, a little soft."""
    text = lines(language)
    paper = Image.new("RGB", (1100, 140 + 90 * len(text)), "#fbfaf6")
    draw = ImageDraw.Draw(paper)
    _draw_line(draw, 60, 90, text[0], 40)
    for i, line in enumerate(text[1:]):
        _draw_line(draw, 60, 190 + i * 90, line, 30)
    photo = Image.new("RGB", (paper.width + 200, paper.height + 200), "#8a6f52")
    photo.paste(paper.rotate(1.5, expand=True, fillcolor="#8a6f52", resample=Image.Resampling.BICUBIC), (90, 80))
    buf = io.BytesIO()
    photo.filter(ImageFilter.GaussianBlur(0.6)).save(buf, "JPEG", quality=88)
    return buf.getvalue()


def _width(text: str, size: int) -> float:
    return sum(_font(script, size).getlength(part) for script, part in visual_order(runs(text)))


def table_photo(language: Language) -> bytes:
    """A phone photo of a printed table with ruled lines, like a bill book or a spreadsheet print-out."""
    title, headers, *body = rows(language)
    table = [headers] + body
    size, pad, row_h = 28, 18, 64
    widths = [max(_width(r[c], size) for r in table) + 2 * pad for c in range(4)]
    paper = Image.new("RGB", (int(sum(widths)) + 160, 230 + row_h * len(table)), "#fbfaf6")
    draw = ImageDraw.Draw(paper)
    _draw_line(draw, 60, 90, title[0], 36)
    top = 130
    for i, row in enumerate(table):
        x = 60
        for c, cell in enumerate(row):
            draw.rectangle((x, top + i * row_h, x + widths[c], top + (i + 1) * row_h), outline="#444", width=2)
            _draw_line(draw, x + pad, top + i * row_h + 42, cell, size)
            x += widths[c]
    photo = Image.new("RGB", (paper.width + 200, paper.height + 200), "#8a6f52")
    photo.paste(paper.rotate(-1.2, expand=True, fillcolor="#8a6f52", resample=Image.Resampling.BICUBIC), (100, 90))
    buf = io.BytesIO()
    photo.filter(ImageFilter.GaussianBlur(0.7)).save(buf, "JPEG", quality=85)
    return buf.getvalue()


# ---- scoring --------------------------------------------------------------------------------------------------------


def _numbers(text: str | None) -> list[int]:
    return [int(n) for n in re.findall(r"\d+", (text or "").replace(",", ""))]


def _scripts(text: str) -> set[str]:
    return {unicodedata.name(ch, "?").split()[0] for ch in text if unicodedata.category(ch)[0] == "L"}


def _overlap(expected: str, got: str | None) -> float:
    want, have = set(normalise(expected).split()), set(normalise(got or "").split())
    return len(want & have) / len(want) if want else 0.0


def score(products: list[Product], items: list[dict]) -> dict:
    """Fields right out of fields asked for: the name (no words missing or added), the price, the size's number and
    the colour in its own field. A product counts as found when its name or its price turns up."""
    right = total = found = translated = 0
    used: set[int] = set()
    for p in products:
        candidates = [(i, it) for i, it in enumerate(items) if i not in used]
        best = max(candidates, key=lambda c: _overlap(p.name, f"{c[1].get('name')} {c[1].get('description')}"), default=None)
        if best is None or _overlap(p.name, f"{best[1].get('name')} {best[1].get('description')}") == 0:
            best = next((c for c in candidates if parse_price(c[1].get("price_text")) == p.price), None)
        fields = 2 + (p.size is not None) + (p.colour is not None)
        total += fields
        if best is None:
            continue
        index, item = best
        used.add(index)
        found += 1
        name = f"{item.get('name') or ''}"
        if _overlap(p.name, name) == _overlap(name, p.name) == 1.0:
            right += 1
        elif name and not (_scripts(name) & _scripts(p.name)):
            translated += 1
        right += parse_price(item.get("price_text")) == p.price
        if p.size is not None:
            right += bool(_numbers(p.size)) and _numbers(p.size) == _numbers(item.get("size"))
        if p.colour is not None:
            right += normalise(p.colour) in normalise(item.get("colour") or "")
    return {"right": right, "total": total, "found": found, "extra": len(items) - len(used), "translated": translated}


# ---- running --------------------------------------------------------------------------------------------------------


def read_sheet(language: Language) -> list[dict]:
    match = find_table(read_tables("spreadsheet", xlsx(language)))
    return [] if match is None else [i.model_dump() for i in rows_to_items(match)]


def rewrite_score(writer: PromptWriter, language: Language) -> tuple[dict, list[str]]:
    right, notes = 0, []
    for p in language.products:
        subject = p.name + (f" in {p.colour}" if p.colour else "") + (f", {p.size}" if p.size else "") + "."
        english = (writer._english(subject) or "").lower()
        ok = all(any(word in english for word in group) for group in p.english)
        right += ok
        notes.append(f"{'✓' if ok else '✗'} {p.name} → {english or '(nothing)'}")
    return {"right": right, "total": len(language.products), "found": right, "extra": 0, "translated": 0}, notes


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--kinds", default=",".join(KINDS))
    parser.add_argument("--only", default="", help="comma-separated language names")
    parser.add_argument("--text-model")
    parser.add_argument("--ocr-model")
    parser.add_argument("--tesseract", action=argparse.BooleanOptionalAction, help="default: the helper's setting")
    parser.add_argument("--vision", action=argparse.BooleanOptionalAction, help="the text model reads photos itself")
    parser.add_argument("--ollama-url", default="http://127.0.0.1:11435")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    overrides = {"ollama_url": args.ollama_url}
    if args.text_model:
        overrides["text_model"] = args.text_model
    if args.ocr_model:
        overrides["ocr_model"] = args.ocr_model
    if args.tesseract is not None:
        overrides["tesseract"] = args.tesseract
    if args.vision is not None:
        overrides["vision"] = args.vision
    settings = HelperSettings(**overrides)
    reader, writer = DocumentReader(settings), PromptWriter(settings)
    kinds = args.kinds.split(",")
    wanted = set(args.only.split(",")) if args.only else None
    ocr = ("Tesseract, then " if settings.tesseract else "") + settings.ocr_model
    print(f"text model {settings.text_model} · OCR {ocr}" + (" · vision" if settings.vision else "") + "\n")

    totals = {k: [0, 0] for k in kinds}
    print(f"{'language':<11}" + "".join(f"{k:>16}" for k in kinds))
    for language in LANGUAGES:
        if wanted and language.name not in wanted:
            continue
        cells, notes = [], []
        for kind in kinds:
            start = time.monotonic()
            if kind == "sheet":
                result = score(language.products, read_sheet(language))
            elif kind == "text":
                items = reader.read("\n".join(lines(language)), None, "list.txt")
                result = score(language.products, items)
                notes += [f"text: {items}"]
            elif kind in ("photo", "table"):
                image = photo(language) if kind == "photo" else table_photo(language)
                items = reader.read(None, image, "list.jpg")
                result = score(language.products, items)
                notes += [f"{kind}: {items}"]
            else:
                result, rewrite_notes = rewrite_score(writer, language)
                notes += rewrite_notes
            seconds = time.monotonic() - start
            totals[kind][0] += result["right"]
            totals[kind][1] += result["total"]
            flag = ("T" if result["translated"] else "") + ("+" if result["extra"] else "")
            cells.append(f"{result['right']:>3}/{result['total']:<3}{flag:<2}{seconds:>5.0f}s")
        print(f"{language.name:<11}" + "".join(f"{c:>16}" for c in cells), flush=True)
        if args.verbose:
            for note in notes:
                print("    " + note)
    print(f"{'total':<11}" + "".join(f"{f'{r}/{t} {100 * r / max(t, 1):.0f}%':>16}" for r, t in totals.values()))
    print("\nT = a name came back translated out of its language · + = rows that aren't products")


if __name__ == "__main__":
    main()
