"""Reads catalog files that have no tidy table: free text goes to a local LLM, photos and scans go through OCR first."""

import base64
import io
import json

import httpx
import pypdfium2
from PIL import Image
from pillow_heif import register_heif_opener

from pictalog_helper.config import HelperSettings
from pictalog_helper.engines import ollama_error

register_heif_opener()

FIELDS = ["name", "sku", "price_text", "size", "colour", "material", "brand", "category", "description"]
CHUNK_CHARS = 6000
MAX_OCR_SIDE = 2000

SCHEMA = {
    "type": "object",
    "properties": {
        "items": {
            "type": "array",
            "items": {"type": "object", "properties": {f: {"type": "string"} for f in FIELDS}},
        }
    },
    "required": ["items"],
}

INSTRUCTIONS = (
    "You turn product catalogs into rows. Return JSON {\"items\": [...]} with one item per product variant: "
    "if a product comes in several sizes or colours with their own price, make one item for each. "
    "Fields: name, sku (product code), price_text (the price exactly as written, with its currency), size, colour, "
    "material, brand, category, description (one short sentence about the product). "
    "Only use information that is in the text. Leave out fields you can't find. Never invent products or prices. "
    "Skip headings, addresses, phone numbers and terms and conditions."
)


def split_chunks(text: str, limit: int = CHUNK_CHARS) -> list[str]:
    """Split on line breaks into pieces of at most `limit` characters ("\\n".join(chunks) == text)."""
    chunks: list[str] = []
    current: list[str] = []
    size = 0
    for line in text.split("\n"):
        while len(line) > limit:  # a single enormous line
            if current:
                chunks.append("\n".join(current))
                current, size = [], 0
            chunks.append(line[:limit])
            line = line[limit:]
        added = len(line) + (1 if current else 0)
        if current and size + added > limit:
            chunks.append("\n".join(current))
            current, size = [], 0
            added = len(line)
        current.append(line)
        size += added
    if current:
        chunks.append("\n".join(current))
    return chunks


def _png(image: Image.Image) -> bytes:
    image = image.convert("RGB")
    image.thumbnail((MAX_OCR_SIDE, MAX_OCR_SIDE))
    buf = io.BytesIO()
    image.save(buf, "PNG")
    return buf.getvalue()


def page_images(file: bytes) -> list[bytes]:
    """Each page of a scanned PDF, or the photo itself, as PNG."""
    if file.startswith(b"%PDF"):
        pdf = pypdfium2.PdfDocument(file)
        try:
            return [_png(page.render(scale=150 / 72).to_pil()) for page in pdf]
        finally:
            pdf.close()
    return [_png(Image.open(io.BytesIO(file)))]


class DocumentReader:
    def __init__(self, settings: HelperSettings, transport: httpx.BaseTransport | None = None):
        self._settings = settings
        self._http = httpx.Client(base_url=settings.ollama_url, timeout=settings.timeout, transport=transport)

    def read(self, text: str | None, file: bytes | None, filename: str) -> list[dict]:
        if not (text and text.strip()):
            text = self._ocr(file) if file else ""
        items: list[dict] = []
        for chunk in split_chunks(text.strip()) if text.strip() else []:
            items += self._extract(chunk)
        return items

    def _post(self, path: str, body: dict) -> dict:
        res = self._http.post(path, json=body)
        if res.status_code >= 400:
            raise RuntimeError(ollama_error(res))
        return res.json()

    def _ocr(self, file: bytes) -> str:
        pages = []
        for png in page_images(file):
            data = self._post("/api/generate", {
                "model": self._settings.ocr_model,
                "prompt": "Text Recognition:",
                "images": [base64.b64encode(png).decode()],
                "stream": False,
            })
            pages.append(data.get("response", ""))
        return "\n\n".join(pages)

    def _extract(self, chunk: str) -> list[dict]:
        data = self._post("/api/chat", {
            "model": self._settings.text_model,
            "messages": [
                {"role": "system", "content": INSTRUCTIONS},
                {"role": "user", "content": f"Catalog text:\n\n{chunk}"},
            ],
            "format": SCHEMA,
            "think": False,
            "stream": False,
            "options": {"temperature": 0},
        })
        try:
            raw = json.loads(data["message"]["content"]).get("items", [])
        except (KeyError, ValueError, AttributeError):
            return []
        items = []
        for row in raw if isinstance(raw, list) else []:
            if not isinstance(row, dict):
                continue
            item = {f: str(row[f]).strip() for f in FIELDS if row.get(f) not in (None, "") and str(row[f]).strip()}
            if item.get("name") or item.get("description"):
                items.append(item)
        return items
