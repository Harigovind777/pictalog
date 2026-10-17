"""Image models mostly understand English. Before a photo is made, the local text model rewrites the product
("Théière in Bleu made of Fonte") into a plain-English description of what it looks like ("a blue cast-iron teapot")."""

import logging
import re

import httpx

from pictalog_helper.config import HelperSettings
from pictalog_helper.engines import ollama_error

log = logging.getLogger("pictalog_helper")

FRAME = "Professional studio product photograph of"
MAX_WORDS = 60

INSTRUCTIONS = (
    "You help a product photographer. Rewrite the product below as one short English phrase that starts with the "
    "product's everyday English name (for example 'black peppercorns', 'green cardamom pods', 'teapot'), then says "
    "what it looks like: shape, colour, material and size. Translate every "
    "non-English word, and explain regional product names (for example 'kasavu mundu' is a white handwoven cotton "
    "wrap with a gold border). Leave out brand names, prices, product codes and any writing that would be printed on "
    "the product. Reply with the phrase only, under 40 words, with no notes or explanations."
)


class PromptWriter:
    def __init__(self, settings: HelperSettings, transport: httpx.BaseTransport | None = None):
        self._settings = settings
        self._http = httpx.Client(base_url=settings.ollama_url, timeout=120.0, transport=transport)
        self._cache: dict[str, str | None] = {}

    def prompt_for(self, payload: dict) -> str:
        subject, studio = payload.get("subject"), payload.get("studio")
        if not (self._settings.rewrite_prompts and subject and studio):
            return payload["prompt"]
        if subject not in self._cache:
            self._cache[subject] = self._english(subject)
        english = self._cache[subject]
        return f"{FRAME} {english}. {studio}" if english else payload["prompt"]

    def _english(self, subject: str) -> str | None:
        try:
            res = self._http.post("/api/chat", json={
                "model": self._settings.text_model,
                "messages": [{"role": "system", "content": INSTRUCTIONS}, {"role": "user", "content": subject}],
                "think": False,
                "stream": False,
                "options": {"temperature": 0},
            })
            if res.status_code >= 400:
                raise RuntimeError(ollama_error(res))
            text = res.json()["message"]["content"]
        except Exception as e:  # never block a photo on this: fall back to the original wording
            log.warning("couldn't rewrite %r: %s", subject, e)
            return None
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.S).strip().strip('"').strip()
        # The phrase is one sentence; anything after it is the model explaining itself.
        text = re.split(r"\.\s|\n|\s\(", text, maxsplit=1)[0].strip().rstrip(".")
        if not text or len(text.split()) > MAX_WORDS:
            return None
        if re.match(r"(A|An|The) [a-z]", text):
            text = text[0].lower() + text[1:]
        log.info("%s → %s", subject, text)
        return text
