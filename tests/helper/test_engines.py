import httpx
import pytest

from fakes import Recorder, b64png, png
from pictalog_helper.engines import CachingEngine, OllamaImageEngine


def test_ollama_engine_request_and_decode(settings):
    rec = Recorder(lambda r: httpx.Response(200, json={"image": b64png(), "done": True}))
    engine = OllamaImageEngine(settings, transport=rec.transport)
    assert engine.generate("a red tee", 42) == png()
    assert str(rec.requests[0].url) == "http://localhost:11434/api/generate"
    assert rec.bodies()[0] == {
        "model": "x/flux2-klein:4b", "prompt": "a red tee", "stream": False,
        "width": 768, "height": 768, "seed": 42, "steps": 2,
    }
    assert engine.name == "x/flux2-klein:4b"


def test_ollama_engine_omits_steps_when_unset(settings):
    rec = Recorder(lambda r: httpx.Response(200, json={"image": b64png()}))
    OllamaImageEngine(settings.model_copy(update={"steps": None}), transport=rec.transport).generate("p", 1)
    assert "steps" not in rec.bodies()[0]


def test_ollama_engine_raises_on_error(settings):
    rec = Recorder(lambda r: httpx.Response(500, json={"error": "libmlxc.dylib not found"}))
    with pytest.raises(RuntimeError, match="libmlxc.dylib not found"):
        OllamaImageEngine(settings, transport=rec.transport).generate("p", 1)


class CountingEngine:
    name = "counting"

    def __init__(self):
        self.calls = 0

    def generate(self, prompt: str, seed: int) -> bytes:
        self.calls += 1
        return f"{prompt}-{seed}".encode()


def test_image_cache_reuses_same_prompt_and_seed():
    # Sizes S/M/L of one shirt share a prompt and seed: make the picture once.
    inner = CountingEngine()
    engine = CachingEngine(inner, size=2)
    assert engine.generate("tee", 1) == b"tee-1"
    assert engine.generate("tee", 1) == b"tee-1"
    assert inner.calls == 1
    engine.generate("tee", 2)
    engine.generate("mug", 1)
    engine.generate("tee", 1)  # evicted by the two newer entries
    assert inner.calls == 4
    assert engine.name == "counting"
