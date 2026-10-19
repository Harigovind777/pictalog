import io
import json

import httpx
from reportlab.pdfgen.canvas import Canvas

from fakes import Recorder, png
from pictalog_helper.config import HelperSettings
from pictalog_helper.reader import DocumentReader, chunk_limit, split_chunks


def chat_answer(items):
    return httpx.Response(200, json={"message": {"role": "assistant", "content": json.dumps({"items": items})}})


def test_split_chunks_on_lines():
    text = "\n".join(f"line {i:04d} " + "x" * 90 for i in range(130))  # ~13 000 chars
    chunks = split_chunks(text, 6000)
    assert len(chunks) == 3
    assert all(len(c) <= 6000 for c in chunks)
    assert "\n".join(chunks) == text


def test_reader_chunks_and_merges(settings):
    calls = iter(range(10))

    def handler(request):
        n = next(calls)
        return chat_answer([{"name": f"Product {n}", "price_text": "10"}])

    rec = Recorder(handler)
    text = "\n".join(f"Product line {i} " + "y" * 90 for i in range(130))
    items = DocumentReader(settings, transport=rec.transport).read(text=text, file=None, filename="a.docx")
    assert [i["name"] for i in items] == ["Product 0", "Product 1", "Product 2"]
    body = rec.bodies()[0]
    assert str(rec.requests[0].url) == "http://localhost:11434/api/chat"
    assert body["model"] == "qwen3.5:4b" and body["think"] is False and body["stream"] is False
    assert body["options"]["temperature"] == 0
    assert body["format"]["properties"]["items"]["type"] == "array"
    assert "Product line 0" in body["messages"][-1]["content"]


def test_reader_drops_rows_without_name_or_description(settings):
    rec = Recorder(lambda r: chat_answer([{"name": "Mug"}, {"price_text": "5"}, {"description": "Blue bowl"}]))
    items = DocumentReader(settings, transport=rec.transport).read(text="Mug 5", file=None, filename="a.txt")
    assert [i.get("name") or i.get("description") for i in items] == ["Mug", "Blue bowl"]


def test_reader_ocr_path_for_image(settings):
    def handler(request):
        if request.url.path == "/api/generate":
            return httpx.Response(200, json={"response": "Mug 199\nBowl 250"})
        return chat_answer([{"name": "Mug", "price_text": "199"}])

    rec = Recorder(handler)
    items = DocumentReader(settings, transport=rec.transport).read(text=None, file=png(), filename="list.jpg")
    assert [r.url.path for r in rec.requests] == ["/api/generate", "/api/chat"]
    ocr = rec.bodies()[0]
    assert ocr["model"] == "glm-ocr" and len(ocr["images"]) == 1
    assert "Mug 199" in rec.bodies()[1]["messages"][-1]["content"]
    assert items == [{"name": "Mug", "price_text": "199"}]


def test_reader_ocr_each_pdf_page(settings):
    buf = io.BytesIO()
    canvas = Canvas(buf)
    canvas.drawString(100, 700, "page one")
    canvas.showPage()
    canvas.drawString(100, 700, "page two")
    canvas.save()

    def handler(request):
        if request.url.path == "/api/generate":
            return httpx.Response(200, json={"response": "Lamp 900"})
        return chat_answer([{"name": "Lamp"}])

    rec = Recorder(handler)
    DocumentReader(settings, transport=rec.transport).read(text=None, file=buf.getvalue(), filename="scan.pdf")
    assert [r.url.path for r in rec.requests] == ["/api/generate", "/api/generate", "/api/chat"]


def test_reader_drops_invented_codes_and_placeholders(settings):
    rec = Recorder(lambda r: chat_answer([
        {"name": "Teak Table", "sku": "TEAK_TABLE_01", "colour": "not specified", "size": "N/A", "price_text": "₹48,000"},
        {"name": "Cane Chair", "sku": "CC-7", "material": "unknown"},
    ]))
    text = "Teak table for ₹48,000. Cane chair (code CC-7)."
    items = DocumentReader(settings, transport=rec.transport).read(text=text, file=None, filename="a.docx")
    assert items == [{"name": "Teak Table", "price_text": "₹48,000"}, {"name": "Cane Chair", "sku": "CC-7"}]


def test_reader_gives_room_caps_the_answer_and_keeps_the_language(settings):
    rec = Recorder(lambda r: chat_answer([{"name": "चाय पत्ती", "price_text": "₹120"}]))
    DocumentReader(settings, transport=rec.transport).read(text="चाय पत्ती — ₹120", file=None, filename="a.txt")
    body = rec.bodies()[0]
    assert body["options"]["num_ctx"] >= 8192 and body["options"]["num_predict"] > 0
    assert "Never translate" in body["messages"][0]["content"]


def test_chunks_are_smaller_for_indian_scripts():
    assert chunk_limit("Cotton saree, red — ₹1,450\n" * 50) == 6000
    assert chunk_limit("सूती साड़ी, लाल — ₹1,450\n" * 50) == 2000
    assert chunk_limit("பருத்திப் புடவை — ₹1,450 (cotton)\n" * 50) == 2000


def test_reader_uses_tesseract_first_and_the_model_when_it_cant(settings, monkeypatch):
    settings.tesseract = True
    monkeypatch.setattr("pictalog_helper.ocr.available", lambda: True)
    pages = iter(["चाय पत्ती — ₹120", None])
    monkeypatch.setattr("pictalog_helper.ocr.read", lambda png: next(pages))

    def handler(request):
        if request.url.path == "/api/generate":
            return httpx.Response(200, json={"response": "ᱪᱟ ₹120"})
        return chat_answer([{"name": "चाय पत्ती"}])

    rec = Recorder(handler)
    reader = DocumentReader(settings, transport=rec.transport)
    reader.read(text=None, file=png(), filename="hindi.jpg")
    assert [r.url.path for r in rec.requests] == ["/api/chat"]
    assert "चाय पत्ती" in rec.bodies()[0]["messages"][-1]["content"]
    reader.read(text=None, file=png(), filename="santali.jpg")  # Tesseract has no Ol Chiki data
    assert [r.url.path for r in rec.requests][1:] == ["/api/generate", "/api/chat"]
    assert rec.bodies()[1]["prompt"] == "Text Recognition:"


def test_other_ocr_models_are_asked_to_copy_the_text_without_translating(settings):
    settings.ocr_model = "gemma4:e4b"

    def handler(request):
        if request.url.path == "/api/generate":
            return httpx.Response(200, json={"response": "Mug 199"})
        return chat_answer([{"name": "Mug"}])

    rec = Recorder(handler)
    DocumentReader(settings, transport=rec.transport).read(text=None, file=png(), filename="list.jpg")
    assert "Don't translate" in rec.bodies()[0]["prompt"] and rec.bodies()[0]["think"] is False


def test_reader_drops_names_copied_into_the_code(settings):
    rec = Recorder(lambda r: chat_answer([
        {"name": "Cotton Saree", "sku": "Cotton Saree", "price_text": "₹1,450"},
        {"name": "Tea", "sku": "Tea Powder"},
        {"name": "Kurta", "sku": "KW-101"},
    ]))
    text = "Cotton Saree ₹1,450\nTea Powder\nKurta KW-101"
    items = DocumentReader(settings, transport=rec.transport).read(text=text, file=None, filename="a.txt")
    assert [i.get("sku") for i in items] == [None, None, "KW-101"]


def test_vision_reads_the_page_itself_with_tesseract_as_a_hint(settings, monkeypatch):
    settings.vision, settings.tesseract, settings.text_model = True, True, "qwen3.5:4b"
    monkeypatch.setattr("pictalog_helper.ocr.available", lambda: True)
    monkeypatch.setattr("pictalog_helper.ocr.words", lambda png: "चाय पत्ती — 7120")
    rec = Recorder(lambda r: chat_answer([{"name": "चाय पत्ती", "price_text": "₹120", "sku": "चाय पत्ती"}]))
    items = DocumentReader(settings, transport=rec.transport).read(text=None, file=png(), filename="list.jpg")
    assert [r.url.path for r in rec.requests] == ["/api/chat"]
    message = rec.bodies()[0]["messages"][-1]
    assert len(message["images"]) == 1 and "चाय पत्ती —" in message["content"]  # numbers come from the image
    assert "7120" not in message["content"]
    assert items == [{"name": "चाय पत्ती", "price_text": "₹120"}]


def test_reader_drops_the_shop_given_as_brand(settings):
    rec = Recorder(lambda r: chat_answer([
        {"name": "سوتی ساڑھی", "brand": "لکشمی اسٹورز"},
        {"name": "Kurta", "brand": "Fabindia"},
    ]))
    text = "لکشمی اسٹورز — قیمتوں کی فہرست\nسوتی ساڑھی 1,450 روپے\nKurta by Fabindia 999"
    items = DocumentReader(settings, transport=rec.transport).read(text=text, file=None, filename="a.txt")
    assert [i.get("brand") for i in items] == [None, "Fabindia"]


def test_hint_numbers_are_left_out_with_their_misread_rupee_sign():
    from pictalog_helper.reader import _NUMBER

    hint = "சேலை — 1 லிட்டர் — ₹350\nचाय — २1,450\nകോട്ടൺ — %120 ഗ്രാം\nKurta KW-101"
    assert _NUMBER.sub("…", hint) == "சேலை — … லிட்டர் — …\nचाय — …\nകോട്ടൺ — … ഗ്രാം\nKurta KW…"


def test_only_the_document_heading_counts_as_the_shop(settings):
    rec = Recorder(lambda r: chat_answer([{"name": "Kurta", "brand": "Fabindia"}, {"name": "Lamp", "brand": "Om"}]))
    text = "Home Store price list\n" + "x" * 5990 + "\nFabindia kurta 999\nOm lamp 120"  # two chunks
    items = DocumentReader(settings, transport=rec.transport).read(text=text, file=None, filename="a.txt")
    assert {i.get("brand") for i in items} == {"Fabindia", "Om"}  # "Om" isn't the word "Home"


def test_defaults_read_india_s_languages(monkeypatch):
    for name in ("TEXT_MODEL", "VISION", "TESSERACT", "OCR_MODEL"):
        monkeypatch.delenv(f"PICTALOG_HELPER_{name}", raising=False)
    defaults = HelperSettings()
    assert defaults.text_model == "qwen3.5:4b" and defaults.vision and defaults.tesseract
    assert defaults.ocr_model != "glm-ocr"  # glm-ocr misreads Indian scripts


def test_rows_are_tidied_against_the_text_they_were_read_from(settings, monkeypatch):
    rec = Recorder(lambda r: chat_answer([{"name": "पानी की बोतल", "material": "स्टील", "size": "लिटर", "colour": ""}]))
    text = "स्टील की पानी की बोतल — 1 लिटर — ₹350"
    items = DocumentReader(settings, transport=rec.transport).read(text=text, file=None, filename="a.txt")
    assert items == [{"name": "स्टील की पानी की बोतल", "material": "स्टील", "size": "1 लिटर"}]

    settings.vision, settings.tesseract = True, True  # a photo: OCR's words, with their numbers, are the text
    monkeypatch.setattr("pictalog_helper.ocr.available", lambda: True)
    monkeypatch.setattr("pictalog_helper.ocr.words", lambda png: "டீ தூள் — 250 கிராம் — ரூ. 120")
    rec = Recorder(lambda r: chat_answer([{"name": "டீ தூள்", "size": "கிராம்", "price_text": "ரூ. 120"}]))
    items = DocumentReader(settings, transport=rec.transport).read(text=None, file=png(), filename="list.jpg")
    assert items == [{"name": "டீ தூள்", "size": "250 கிராம்", "price_text": "ரூ. 120"}]
