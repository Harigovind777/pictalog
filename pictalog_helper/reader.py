"""Reads catalog files that have no tidy table: free text goes to a local LLM, photos and scans go through OCR first.

OCR is Tesseract when it's installed and reads the page confidently (it knows most of India's scripts), else the OCR
model. With `vision` on, the text model looks at each page itself, with Tesseract's words as a hint. The two are good
at opposite things: Tesseract spells Tamil, Kannada or Odia words exactly but reads ₹ as a 2, 3, 4 or %, while the
model reads every price and size right but garbles words in those scripts. So the hint keeps Tesseract's words and
leaves out its numbers, and the model reads the numbers from the image."""

import base64
import io
import json
import re

import httpx
import pypdfium2
from PIL import Image
from pillow_heif import register_heif_opener

from pictalog_helper import ocr
from pictalog_helper.tidy import tidy
from pictalog_helper.config import HelperSettings
from pictalog_helper.engines import ollama_error

register_heif_opener()

FIELDS = ["name", "sku", "price_text", "size", "colour", "material", "brand", "category", "description"]
CHUNK_CHARS = 6000
# India's scripts take two to four times as many tokens per character as English, so their chunks are smaller.
CHUNK_CHARS_OTHER_SCRIPTS = 2000
# Room for a chunk, the instructions and the rows that come back; the cap stops a model that starts repeating itself.
OPTIONS = {"temperature": 0, "num_ctx": 8192, "num_predict": 4096}
PLACEHOLDERS = {
    "not specified", "unspecified", "unknown", "n/a", "na", "none", "null", "-", "—", "…", "...", "not available",
    "not mentioned",
}
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
    "Fields: name, sku (only a product code printed in the text), price_text (the price exactly as written, with its currency), size, colour, "
    "material, brand, category, description (one short sentence about the product). "
    "Only use information that is in the text. Leave out fields you can't find. Never invent products or prices. "
    "Copy names, colours, sizes and prices exactly as written, in their own language and script: the text may be in "
    "Hindi, Tamil, Bengali, Urdu or any other language, and a name written in Hindi stays in Hindi. Never translate "
    "or transliterate. "
    "Skip headings, addresses, phone numbers and terms and conditions."
)


def chunk_limit(text: str) -> int:
    letters = [ch for ch in text if ch.isalpha()]
    other = sum(not ch.isascii() for ch in letters)
    return CHUNK_CHARS_OTHER_SCRIPTS if letters and other / len(letters) > 0.3 else CHUNK_CHARS


# A number as OCR writes it, with the character before it when that's a misread ₹ (२1,450, %120, *899).
_NUMBER = re.compile(r"[^\s\w]?\d[\d.,]*")

TRANSCRIBE = (
    "Write out all the text in this image exactly as printed, line by line, in its own language and script. "
    "Don't translate, explain or add anything."
)


def _first_line(text: str) -> str:
    return next((line for line in text.splitlines() if line.strip()), "")


def _words(text: str) -> str:
    """Lower-case words between single spaces, so " om " is found in " om stores " but not in " home "."""
    return " " + " ".join(re.split(r"[\s,.;:!?|/()\[\]\"'—–-]+", text.lower())).strip() + " "


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
        if not (text and text.strip()) and file and self._settings.vision:
            return [item for png in page_images(file) for item in self._extract_page(png)]
        if not (text and text.strip()):
            text = self._ocr(file) if file else ""
        items: list[dict] = []
        heading = _first_line(text)
        for chunk in split_chunks(text.strip(), chunk_limit(text)) if text.strip() else []:
            items += self._extract(chunk, heading)
        return items

    def _post(self, path: str, body: dict) -> dict:
        res = self._http.post(path, json=body)
        if res.status_code >= 400:
            raise RuntimeError(ollama_error(res))
        return res.json()

    def _ocr(self, file: bytes) -> str:
        return "\n\n".join(self._ocr_page(png) for png in page_images(file))

    def _ocr_page(self, png: bytes) -> str:
        if self._settings.tesseract and ocr.available():
            text = ocr.read(png)
            if text:
                return text
        model = self._settings.ocr_model
        body = {"model": model, "images": [base64.b64encode(png).decode()], "stream": False, "options": OPTIONS}
        if model.startswith("glm-ocr"):
            body["prompt"] = "Text Recognition:"  # glm-ocr's own prompt
        else:
            body |= {"prompt": TRANSCRIBE, "think": False}  # Qwen 3.5 otherwise thinks until it runs out of room
        return self._post("/api/generate", body).get("response", "")

    def _extract_page(self, png: bytes) -> list[dict]:
        hint = ocr.words(png) if self._settings.tesseract and ocr.available() else None
        message = {"role": "user", "content": "The catalog page is in the image.", "images": [base64.b64encode(png).decode()]}
        if hint:
            message["content"] += (
                "\n\nIts words as read by OCR, which spells them exactly but misreads numbers, so the numbers have "
                "been taken out: copy the words from here, and read every price, size and number from the image.\n\n"
                + re.sub(r"[ \t]+", " ", _NUMBER.sub("", hint))
            )
        return self._extract(hint or "", _first_line(hint or ""), message)

    def _extract(self, chunk: str, heading: str, message: dict | None = None) -> list[dict]:
        """Rows from a chunk of text, or from a page image (`message`), tidied against `chunk` (OCR's words for an
        image); codes must appear in `chunk` when it's given. `heading` is the document's first line, usually the
        shop's name."""
        data = self._post("/api/chat", {
            "model": self._settings.text_model,
            "messages": [
                {"role": "system", "content": INSTRUCTIONS},
                message or {"role": "user", "content": f"Catalog text:\n\n{chunk}"},
            ],
            "format": SCHEMA,
            "think": False,
            "stream": False,
            "options": OPTIONS,
        })
        try:
            raw = json.loads(data["message"]["content"]).get("items", [])
        except (KeyError, ValueError, AttributeError):
            return []
        items = []
        for row in raw if isinstance(raw, list) else []:
            if not isinstance(row, dict):
                continue
            item = {
                f: str(row[f]).strip()
                for f in FIELDS
                if row.get(f) is not None and str(row[f]).strip().lower() not in PLACEHOLDERS | {""}
            }
            sku = item.get("sku", "")
            invented = chunk and sku.lower() not in chunk.lower()
            if sku and (invented or sku == item.get("name") or not any(c.isdigit() for c in sku)):
                del item["sku"]  # made up, or the name copied into the code: real codes have a digit (KW-101)
            if item.get("brand") and _words(item["brand"]) in _words(heading):
                del item["brand"]  # the shop whose list it is, from the heading, not the product's brand
            if item.get("name") or item.get("description"):
                items.append(tidy(item, chunk))
        return items
