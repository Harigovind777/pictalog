from sqlalchemy import select

from pictalog.models import Job
from test_images import png_bytes
from test_worker_api import applied_catalog


def first_variant(catalog: dict) -> dict:
    return catalog["products"][0]["variants"][0]


def test_regenerate_bumps_seed_and_queues(client, signup, db):
    h = signup()
    v = first_variant(applied_catalog(client, h))
    [old_job] = db.scalars(select(Job).where(Job.variant_id == v["id"])).all()
    r = client.post(f"/api/variants/{v['id']}/regenerate", headers=h)
    assert r.status_code == 200 and r.json()["image_status"] == "queued"
    jobs = db.scalars(select(Job).where(Job.variant_id == v["id"]).order_by(Job.id)).all()
    db.refresh(jobs[0])
    assert [j.status for j in jobs] == ["cancelled", "queued"]
    assert jobs[1].payload["seed"] == old_job.payload["seed"] + 1


def test_generate_anyway_for_not_enough_detail(client, signup, db):
    h = signup()
    cid = client.post("/api/catalogs", json={"name": "C"}, headers=h).json()["id"]
    from test_imports import XLSX, upload, xlsx

    imp = upload(client, h, cid, "codes.xlsx", xlsx([["Name", "SKU"], ["A1234", "A1234"]]), XLSX).json()
    catalog = client.post(f"/api/imports/{imp['id']}/apply", json={"items": imp["items"]}, headers=h).json()
    v = first_variant(catalog)
    assert v["image_status"] == "not_enough_detail"
    assert client.post(f"/api/variants/{v['id']}/regenerate", headers=h).json()["image_status"] == "queued"


def test_upload_photo_cancels_jobs(client, signup, db):
    h = signup()
    v = first_variant(applied_catalog(client, h))
    r = client.post(f"/api/variants/{v['id']}/image", files={"file": ("p.png", png_bytes(50, 50), "image/png")}, headers=h)
    assert r.status_code == 200
    body = r.json()
    assert body["image_source"] == "uploaded" and body["image_status"] == "ready"
    assert body["image_url"].startswith("/api/files/img/")
    statuses = db.scalars(select(Job.status).where(Job.variant_id == v["id"])).all()
    assert statuses == ["cancelled"]


def test_upload_photo_rejects_non_image(client, signup):
    h = signup()
    v = first_variant(applied_catalog(client, h))
    r = client.post(f"/api/variants/{v['id']}/image", files={"file": ("p.png", b"nope", "image/png")}, headers=h)
    assert r.status_code == 400


def test_variant_of_other_company_404(client, signup):
    a = signup("a@x.com")
    b = signup("b@x.com")
    v = first_variant(applied_catalog(client, a))
    assert client.post(f"/api/variants/{v['id']}/regenerate", headers=b).status_code == 404
    r = client.post(f"/api/variants/{v['id']}/image", files={"file": ("p.png", png_bytes(5, 5), "image/png")}, headers=b)
    assert r.status_code == 404


def test_regenerate_an_uploaded_photo_makes_an_ai_image(client, signup, db, app):
    from pictalog.jobs import complete_image
    from pictalog.models import Variant

    h = signup()
    v = first_variant(applied_catalog(client, h))
    client.post(f"/api/variants/{v['id']}/image", files={"file": ("p.png", png_bytes(50, 50), "image/png")}, headers=h)
    assert client.post(f"/api/variants/{v['id']}/regenerate", headers=h).json()["image_status"] == "queued"
    job = db.scalars(select(Job).where(Job.variant_id == v["id"], Job.status == "queued")).one()
    job.status = "running"  # as if the helper had claimed it
    db.commit()
    complete_image(db, app.state.storage, job, png_bytes(64, 64))
    variant = db.get(Variant, v["id"])
    db.refresh(variant)
    assert variant.image_source == "generated" and variant.image_status == "ready"
