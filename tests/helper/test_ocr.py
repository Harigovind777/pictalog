import io
from pathlib import Path

import pytest
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from pictalog_helper import ocr

NOTO = Path(__file__).resolve().parents[2] / "pictalog" / "fonts" / "noto"


def test_clean_removes_trailing_joiners_and_modernises_chillus():
    assert ocr.clean("ஸ்டோர்ஸ்‌ — விலைப்‌ பட்டியல்‌") == "ஸ்டோர்ஸ் — விலைப் பட்டியல்"
    assert ocr.clean("കോട്ടണ്‍ സാരി") == "കോട്ടൺ സാരി"
    assert ocr.clean("क्‌ष") == "क्‌ष"  # inside a word the joiner changes the letters, so it stays


def _page(text: str, font: str) -> bytes:
    image = Image.new("RGB", (900, 160), "white")
    face = ImageFont.truetype(str(NOTO / font), 40, layout_engine=ImageFont.Layout.RAQM)
    ImageDraw.Draw(image).text((30, 50), text, fill="black", font=face)
    buf = io.BytesIO()
    image.save(buf, "PNG")
    return buf.getvalue()


@pytest.mark.skipif(not ocr.available(), reason="tesseract isn't installed")
def test_reads_hindi_and_tamil():
    assert "साड़ी" in ocr.read(_page("सूती साड़ी लाल रंग की बहुत सुंदर", "NotoSansDevanagari-Regular.ttf"))
    assert "புடவை" in ocr.read(_page("பருத்திப் புடவை சிவப்பு நிறம் அழகானது", "NotoSansTamil-Regular.ttf"))


@pytest.mark.skipif(not ocr.available(), reason="tesseract isn't installed")
def test_words_reads_a_ruled_table_cell_by_cell():
    face = ImageFont.truetype(str(NOTO / "NotoSansGujarati-Regular.ttf"), 30, layout_engine=ImageFont.Layout.RAQM)
    digits = ImageFont.truetype(str(NOTO.parent / "DejaVuSans.ttf"), 28)
    image = Image.new("RGB", (1000, 420), "#fbfaf6")
    draw = ImageDraw.Draw(image)
    for row, (name, price) in enumerate([("સુતરાઉ સાડી", "₹1,450"), ("ચાની પત્તી", "₹120"), ("પિત્તળનો દીવો", "₹899")]):
        y = 80 + row * 80
        draw.rectangle((80, y, 560, y + 80), outline="#444", width=2)
        draw.rectangle((560, y, 800, y + 80), outline="#444", width=2)
        draw.text((100, y + 52), name, fill="#222", font=face, anchor="ls")
        draw.text((580, y + 52), price, fill="#222", font=digits, anchor="ls")
    buf = io.BytesIO()
    image.filter(ImageFilter.GaussianBlur(0.6)).save(buf, "PNG")
    assert ocr.words(buf.getvalue()).splitlines() == ["સુતરાઉ સાડી", "ચાની પત્તી", "પિત્તળનો દીવો"]
