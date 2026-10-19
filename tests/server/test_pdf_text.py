import io

import pypdfium2
from reportlab.pdfgen.canvas import Canvas

from pictalog.pdf_text import draw, fit, layout, runs, visual_order, width


def test_runs_split_by_script():
    assert runs("Silk साड़ी ₹500") == [(None, "Silk"), (None, " "), ("Devanagari", "साड़ी"), (None, " "), (None, "₹"), (None, "500")]
    assert runs("ਦਾਲ।") == [("Gurmukhi", "ਦਾਲ।")]  # the danda stays with its sentence
    assert runs("ক্ষ‍ত") == [("Bengali", "ক্ষ‍ত")]


def test_urdu_reads_right_to_left():
    parts = visual_order(runs("سرخ قمیص 500"))
    assert [p for _, p in parts] == ["500", " ", "قمیص", " ", "سرخ"]
    parts = visual_order(runs("Kurta قمیص سرخ"))  # an English line keeps its order; the Urdu words swap
    assert [p for _, p in parts] == ["Kurta", " ", "سرخ", " ", "قمیص"]
    parts = visual_order(runs("قیمت ۱۵۰"))  # Urdu digits read left to right
    assert [p for _, p in parts] == ["۱۵۰", " ", "قیمت"]


def test_urdu_numbers_are_not_turned_around():
    pieces = layout("روپے ۱۵۰۰۰", 10)
    assert [str(p.text) for p in pieces][0] == "۱۵۰۰۰"


def test_layout_uses_a_font_for_each_script():
    fonts = [p.font for p in layout("Tea चाय டீ", 10)]
    assert fonts == ["DejaVuSans", "DejaVuSans", "NotoSansDevanagari-Regular", "DejaVuSans", "NotoSansTamil-Regular"]
    assert layout("चाय", 10, bold=True)[0].font == "NotoSansDevanagari-Bold"


def test_shaped_text_is_narrower_than_its_letters():
    # क्ष is one glyph, not क + ् + ष side by side.
    assert width("क्ष", 20) < width("क", 20) + width("ष", 20)


def test_fit_never_leaves_half_a_syllable():
    text = "कांजीवरम रेशम साड़ी क्षत्रिय"
    short = fit(text, 10, width(text, 10) * 0.5)
    assert short.endswith("…")
    assert width(short, 10) <= width(text, 10) * 0.5
    assert short[-2] not in "्‌‍"  # no dangling virama or joiner before the ellipsis
    assert fit("Tea", 10, 100) == "Tea"


def test_draw_embeds_the_script_fonts():
    buf = io.BytesIO()
    c = Canvas(buf)
    draw(c, 300, 500, "बनारसी साड़ी · பட்டுப் புடவை · قمیص", 12, align="centre")
    c.save()
    pdf = buf.getvalue()
    for name in (b"NotoSansDevanagari", b"NotoSansTamil", b"NotoSansArabic"):
        assert name in pdf
    assert pypdfium2.PdfDocument(pdf)[0].get_textpage().count_chars() > 0
