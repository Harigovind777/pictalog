"""Shared fakes for helper tests."""

import base64
import io
import json

import httpx
from PIL import Image


def png(color=(10, 120, 200), size=(32, 32)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, color).save(buf, "PNG")
    return buf.getvalue()


class Recorder:
    """An httpx MockTransport that records requests and answers from a handler."""

    def __init__(self, handler):
        self.requests: list[httpx.Request] = []
        self._handler = handler
        self.transport = httpx.MockTransport(self._handle)

    def _handle(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        return self._handler(request)

    def bodies(self) -> list[dict]:
        return [json.loads(r.content) for r in self.requests]


def b64png() -> str:
    return base64.b64encode(png()).decode()
