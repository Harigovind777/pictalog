from datetime import timedelta

from pictalog.models import Heartbeat, utcnow
from test_images import png_bytes
from test_imports import SHEET, XLSX, docx_text, new_catalog, upload, xlsx

W = {"X-Worker-Token": "dev-worker-token"}


def applied_catalog(client, h) -> dict:
    cid = new_catalog(client, h)
    imp = upload(client, h, cid, "spring.xlsx", xlsx(SHEET), XLSX).json()
    return client.post(f"/api/imports/{imp['id']}/apply", json={"items": imp["items"]}, headers=h).json()


def test_worker_requires_token(client):
    assert client.post("/api/worker/claim", json={}).status_code == 401
    assert client.post("/api/worker/claim", json={}, headers={"X-Worker-Token": "wrong"}).status_code == 401


def test_claim_nothing_204(client):
    assert client.post("/api/worker/claim", json={"engine": "x"}, headers=W).status_code == 204


def test_worker_image_roundtrip(client, signup):
    h = signup()
    catalog = applied_catalog(client, h)
    job = client.post("/api/worker/claim", json={"engine": "flux"}, headers=W).json()
    assert job["kind"] == "image" and job["payload"]["prompt"].startswith("Professional studio product photograph")
    r = client.post(f"/api/worker/jobs/{job['id']}/image", files={"file": ("a.png", png_bytes(64, 64), "image/png")}, headers=W)
    assert r.status_code == 204
    variant = client.get(f"/api/catalogs/{catalog['id']}", headers=h).json()["products"][0]["variants"][0]
    assert variant["image_status"] == "ready" and variant["image_source"] == "generated"
    assert client.get(variant["thumb_url"]).status_code == 200


def test_worker_items_roundtrip(client, signup):
    h = signup()
    cid = new_catalog(client, h)
    imp = upload(client, h, cid, "range.docx", docx_text("Oak dining table 25,000")).json()
    job = client.post("/api/worker/claim", json={}, headers=W).json()
    assert job["kind"] == "extract" and job["payload"]["import_id"] == imp["id"]
    assert client.get(f"/api/worker/jobs/{job['id']}/file", headers=W).content.startswith(b"PK")
    items = [{"name": "Oak dining table", "price_text": "25,000"}]
    assert client.post(f"/api/worker/jobs/{job['id']}/items", json={"items": items}, headers=W).status_code == 204
    body = client.get(f"/api/imports/{imp['id']}", headers=h).json()
    assert body["status"] == "ready_for_review" and body["method"] == "ai"
    assert body["items"][0]["name"] == "Oak dining table" and body["diff"]["new"] == 1


def test_worker_no_items_marks_import_failed(client, signup):
    h = signup()
    cid = new_catalog(client, h)
    imp = upload(client, h, cid, "range.docx", docx_text("Hello there")).json()
    job = client.post("/api/worker/claim", json={}, headers=W).json()
    client.post(f"/api/worker/jobs/{job['id']}/items", json={"items": []}, headers=W)
    body = client.get(f"/api/imports/{imp['id']}", headers=h).json()
    assert body["status"] == "failed" and "couldn't find any products" in body["error"]


def test_completed_after_cancel_is_ignored(client, signup):
    h = signup()
    catalog = applied_catalog(client, h)
    job = client.post("/api/worker/claim", json={}, headers=W).json()
    vid = job["payload"]["variant_id"]
    photo = png_bytes(80, 80, (0, 200, 0))
    uploaded = client.post(f"/api/variants/{vid}/image", files={"file": ("p.png", photo, "image/png")}, headers=h).json()
    r = client.post(f"/api/worker/jobs/{job['id']}/image", files={"file": ("a.png", png_bytes(64, 64), "image/png")}, headers=W)
    assert r.status_code == 204
    variants = [v for p in client.get(f"/api/catalogs/{catalog['id']}", headers=h).json()["products"] for v in p["variants"]]
    after = next(v for v in variants if v["id"] == vid)
    assert after["image_source"] == "uploaded" and after["image_url"] == uploaded["image_url"]


def test_helper_status_online_then_offline(client, signup, db):
    h = signup()
    assert client.get("/api/helper/status", headers=h).json()["online"] is False
    client.post("/api/worker/claim", json={"engine": "flux2-klein"}, headers=W)
    status = client.get("/api/helper/status", headers=h).json()
    assert status["online"] is True and status["engine"] == "flux2-klein"
    beat = db.get(Heartbeat, 1)
    beat.last_seen_at = utcnow() - timedelta(seconds=31)
    db.commit()
    assert client.get("/api/helper/status", headers=h).json()["online"] is False


def test_heartbeat_keeps_helper_online(client, signup):
    h = signup()
    assert client.post("/api/worker/heartbeat", json={"engine": "flux"}).status_code == 401
    assert client.post("/api/worker/heartbeat", json={"engine": "flux"}, headers=W).status_code == 204
    status = client.get("/api/helper/status", headers=h).json()
    assert status["online"] is True and status["engine"] == "flux"
