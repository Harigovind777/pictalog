from datetime import timedelta

from pictalog.catalog.sync import apply_items
from pictalog.jobs import claim_next, complete_image, enqueue_extract, fail_job, requeue_stale
from pictalog.models import Import, Job, Variant, utcnow
from pictalog.schemas import ExtractedItem as Item
from test_images import png_bytes


def an_import(db, catalog) -> Import:
    imp = Import(catalog=catalog, filename="a.docx", file_key="uploads/x/a.docx", kind="docx", status="needs_ai")
    db.add(imp)
    db.flush()
    return imp


def test_claim_prefers_extract_jobs(db, catalog):
    apply_items(db, catalog, [Item(name="Tee")])
    enqueue_extract(db, an_import(db, catalog), "Oak table")
    db.commit()
    first = claim_next(db, "test-engine")
    assert first.kind == "extract" and first.status == "running" and first.attempts == 1
    second = claim_next(db, "test-engine")
    assert second.kind == "image"
    assert db.get(Variant, second.variant_id).image_status == "generating"
    assert claim_next(db, "test-engine") is None


def test_claim_empty_returns_none(db):
    assert claim_next(db, None) is None


def test_stale_job_requeued_then_failed_after_3(db, catalog):
    apply_items(db, catalog, [Item(name="Tee")])
    t0 = utcnow()
    for attempt in (1, 2, 3):
        now = t0 + timedelta(minutes=11 * (attempt - 1))
        job = claim_next(db, "e", now=now)
        assert job is not None and job.attempts == attempt
        requeue_stale(db, now + timedelta(minutes=11))
    db.refresh(job)
    assert job.status == "failed"
    assert db.get(Variant, job.variant_id).image_status == "failed"


def test_running_job_not_requeued_before_10_minutes(db, catalog):
    apply_items(db, catalog, [Item(name="Tee")])
    t0 = utcnow()
    job = claim_next(db, "e", now=t0)
    requeue_stale(db, t0 + timedelta(minutes=9))
    db.refresh(job)
    assert job.status == "running"


def test_fail_requeues_until_third_attempt(db, catalog):
    apply_items(db, catalog, [Item(name="Tee")])
    for attempt in (1, 2, 3):
        job = claim_next(db, "e")
        fail_job(db, job, "boom")
        db.refresh(job)
        assert job.status == ("queued" if attempt < 3 else "failed")
    assert db.get(Variant, job.variant_id).image_status == "failed"


def test_complete_image_saves_webp(db, catalog, app):
    apply_items(db, catalog, [Item(name="Tee")])
    job = claim_next(db, "e")
    complete_image(db, app.state.storage, job, png_bytes(64, 64))
    variant = db.get(Variant, job.variant_id)
    assert variant.image_status == "ready" and variant.image_source == "generated"
    assert app.state.storage.exists(variant.image_key) and app.state.storage.exists(variant.thumb_key)
    assert db.get(Job, job.id).status == "done"
