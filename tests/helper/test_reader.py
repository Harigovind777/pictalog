import io
import json

import httpx
from reportlab.pdfgen.canvas import Canvas

from fakes import Recorder, png
from pictalog_helper.reader import DocumentReader, split_chunks


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
    assert body["model"] == "qwen3:4b" and body["think"] is False and body["stream"] is False
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
