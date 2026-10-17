import base64
from collections import OrderedDict
from typing import Protocol

import httpx

from pictalog_helper.config import HelperSettings


class ImageEngine(Protocol):
    """Anything that turns a prompt into a PNG. A paid image API can implement this later."""

    name: str

    def generate(self, prompt: str, seed: int) -> bytes: ...


def ollama_error(res: httpx.Response) -> str:
    try:
        return res.json().get("error") or f"HTTP {res.status_code}"
    except ValueError:
        return f"HTTP {res.status_code}"


class OllamaImageEngine:
    def __init__(self, settings: HelperSettings, transport: httpx.BaseTransport | None = None):
        self.name = settings.image_model
        self._settings = settings
        self._http = httpx.Client(base_url=settings.ollama_url, timeout=settings.timeout, transport=transport)

    def generate(self, prompt: str, seed: int) -> bytes:
        s = self._settings
        body: dict = {
            "model": s.image_model, "prompt": prompt, "stream": False,
            "width": s.width, "height": s.height, "seed": seed,
        }
        if s.steps:
            body["steps"] = s.steps
        res = self._http.post("/api/generate", json=body)
        data = res.json() if res.headers.get("content-type", "").startswith("application/json") else {}
        if res.status_code >= 400 or "error" in data or "image" not in data:
            raise RuntimeError(data.get("error") or ollama_error(res))
        return base64.b64decode(data["image"])


class CachingEngine:
    """Remembers recent pictures by (prompt, seed): sizes S, M and L of one shirt get the same photo, made once."""

    def __init__(self, inner: ImageEngine, size: int = 64):
        self.name = inner.name
        self._inner = inner
        self._size = size
        self._cache: OrderedDict[tuple[str, int], bytes] = OrderedDict()

    def generate(self, prompt: str, seed: int) -> bytes:
        key = (prompt, seed)
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]
        image = self._inner.generate(prompt, seed)
        self._cache[key] = image
        if len(self._cache) > self._size:
            self._cache.popitem(last=False)
        return image
