import httpx

from fakes import Recorder
from pictalog_helper.prompts import PromptWriter

JOB = {
    "prompt": "Professional studio product photograph of Théière in Bleu made of Fonte, 1,2 L (Cuisine). Single product.",
    "subject": "Théière in Bleu made of Fonte, 1,2 L (Cuisine).",
    "studio": "Single product.",
    "seed": 1,
}


def reply(text):
    return httpx.Response(200, json={"message": {"role": "assistant", "content": text}})


def test_rewrites_subject_into_plain_english(settings):
    rec = Recorder(lambda r: reply("A blue cast-iron teapot, 1.2 litres."))
    prompt = PromptWriter(settings, transport=rec.transport).prompt_for(JOB)
    assert prompt == "Professional studio product photograph of a blue cast-iron teapot, 1.2 litres. Single product."
    body = rec.bodies()[0]
    assert str(rec.requests[0].url) == "http://localhost:11434/api/chat"
    assert body["model"] == "qwen3:4b" and body["think"] is False and body["options"]["temperature"] == 0
    assert "Théière in Bleu" in body["messages"][-1]["content"]


def test_same_subject_asks_once(settings):
    rec = Recorder(lambda r: reply("A blue teapot."))
    writer = PromptWriter(settings, transport=rec.transport)
    writer.prompt_for(JOB)
    writer.prompt_for({**JOB, "seed": 2})
    assert len(rec.requests) == 1


def test_falls_back_to_original_prompt_when_the_model_fails(settings):
    rec = Recorder(lambda r: httpx.Response(500, json={"error": "model not found"}))
    assert PromptWriter(settings, transport=rec.transport).prompt_for(JOB) == JOB["prompt"]


def test_falls_back_for_empty_or_rambling_answers(settings):
    for answer in ("", "word " * 120):
        rec = Recorder(lambda r, a=answer: reply(a))
        assert PromptWriter(settings, transport=rec.transport).prompt_for(JOB) == JOB["prompt"]


def test_old_jobs_without_subject_use_their_prompt(settings):
    rec = Recorder(lambda r: reply("x"))
    assert PromptWriter(settings, transport=rec.transport).prompt_for({"prompt": "P", "seed": 1}) == "P"
    assert rec.requests == []


def test_can_be_turned_off(settings):
    rec = Recorder(lambda r: reply("x"))
    writer = PromptWriter(settings.model_copy(update={"rewrite_prompts": False}), transport=rec.transport)
    assert writer.prompt_for(JOB) == JOB["prompt"]
    assert rec.requests == []
