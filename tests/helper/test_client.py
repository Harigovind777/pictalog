import json

import httpx

from fakes import Recorder
from pictalog_helper.client import ServerClient


def test_client_sends_worker_token_and_handles_no_job(settings):
    rec = Recorder(lambda r: httpx.Response(204))
    client = ServerClient(settings, transport=rec.transport)
    assert client.claim() is None
    req = rec.requests[0]
    assert req.url == "http://localhost:8000/api/worker/claim"
    assert req.headers["x-worker-token"] == "dev-worker-token"
    assert rec.bodies()[0] == {"engine": "x/flux2-klein:4b"}


def test_client_claim_returns_job(settings):
    job = {"id": 7, "kind": "image", "payload": {"prompt": "p", "seed": 1, "variant_id": 3}}
    client = ServerClient(settings, transport=Recorder(lambda r: httpx.Response(200, json=job)).transport)
    assert client.claim() == job


def test_client_sends_results(settings):
    rec = Recorder(lambda r: httpx.Response(204))
    client = ServerClient(settings, transport=rec.transport)
    client.send_image(7, b"\x89PNG")
    client.send_items(8, [{"name": "Mug"}])
    client.fail(9, "boom")
    urls = [str(r.url) for r in rec.requests]
    assert urls == [
        "http://localhost:8000/api/worker/jobs/7/image",
        "http://localhost:8000/api/worker/jobs/8/items",
        "http://localhost:8000/api/worker/jobs/9/fail",
    ]
    assert b"\x89PNG" in rec.requests[0].content
    assert [json.loads(r.content) for r in rec.requests[1:]] == [{"items": [{"name": "Mug"}]}, {"error": "boom"}]
    assert all(r.headers["x-worker-token"] == "dev-worker-token" for r in rec.requests)


def test_client_download(settings):
    rec = Recorder(lambda r: httpx.Response(200, content=b"PK\x03\x04"))
    assert ServerClient(settings, transport=rec.transport).download(5) == b"PK\x03\x04"
    assert str(rec.requests[0].url) == "http://localhost:8000/api/worker/jobs/5/file"


def test_client_heartbeat(settings):
    rec = Recorder(lambda r: httpx.Response(204))
    ServerClient(settings, transport=rec.transport).heartbeat()
    assert str(rec.requests[0].url) == "http://localhost:8000/api/worker/heartbeat"
    assert rec.bodies() == [{"engine": "x/flux2-klein:4b"}]
