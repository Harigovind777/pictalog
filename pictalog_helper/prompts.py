"""Image models mostly understand English. Before a photo is made, the local text model rewrites the product
("Théière in Bleu made of Fonte") into a plain-English description of what it looks like ("a blue cast-iron teapot")."""

import logging
import re

import httpx

from pictalog_helper import glossary
from pictalog_helper.config import HelperSettings
from pictalog_helper.engines import ollama_error

log = logging.getLogger("pictalog_helper")

FRAME = "Professional studio product photograph of"
MAX_WORDS = 60

INSTRUCTIONS = (
    "You help a product photographer. Translate the product below into one short English phrase for its photo: "
    "first what it is, in plain everyday English, then what it looks like: material, colour, shape and size. "
    "It may be written in Hindi, Tamil, Bengali, Urdu or any other language of India: translate every word, explain "
    "regional product names, and keep every detail it gives. Meanings given after it are correct; use them. Never add "
    "a colour or material it doesn't give, and never describe a different product. Leave out brand names, prices, "
    "product codes and any writing that would be printed on the product. Reply with the phrase only, under 40 words, "
    "with no notes or explanations."
)


def _with_notes(subject: str) -> str:
    found = glossary.notes(subject)
    return f"{subject}\n\nMeanings: {'; '.join(found)}." if found else subject


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
                "messages": [{"role": "system", "content": INSTRUCTIONS}, {"role": "user", "content": _with_notes(subject)}],
                "think": False,
                "stream": False,
                "options": {"temperature": 0, "num_predict": 120},  # one short phrase; stops a model that rambles
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
