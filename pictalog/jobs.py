from datetime import datetime, timedelta

from sqlalchemy import case, select, update
from sqlalchemy.orm import Session

from pictalog.catalog.prompt import STUDIO, build_prompt, build_subject, seed_for
from pictalog.images import save_image
from pictalog.models import Catalog, Heartbeat, Import, Job, Variant, utcnow
from pictalog.schemas import ExtractedItem


def cancel_image_jobs(db: Session, variant_id: int) -> None:
    db.execute(
        update(Job)
        .where(Job.kind == "image", Job.variant_id == variant_id, Job.status.in_(("queued", "running")))
        .values(status="cancelled")
    )


def enqueue_image(db: Session, variant: Variant) -> Job:
    """Queue a fresh image for this variant, replacing any image job still waiting or running."""
    cancel_image_jobs(db, variant.id)
    product = variant.product
    job = Job(
        kind="image",
        variant_id=variant.id,
        payload={
            "variant_id": variant.id,
            "prompt": build_prompt(product, variant),
            # The helper may rewrite the subject into plain English before adding the studio wording back.
            "subject": build_subject(product, variant),
            "studio": STUDIO,
            "seed": seed_for(product.group_key, variant.seed_offset),
        },
    )
    variant.image_status = "queued"
    db.add(job)
    return job


def enqueue_extract(db: Session, imp: Import, text: str | None) -> Job:
    """Ask the image helper's AI to read a file that has no usable table (free text, photos, scans)."""
    job = Job(
        kind="extract",
        import_id=imp.id,
        payload={"import_id": imp.id, "filename": imp.filename, "text": text},
    )
    db.add(job)
    return job


STALE_AFTER = timedelta(minutes=10)
MAX_ATTEMPTS = 3
HELPER_STOPPED = "The image helper stopped responding."


def _mark_target_failed(db: Session, job: Job, error: str) -> None:
    if job.kind == "image" and job.variant_id and (variant := db.get(Variant, job.variant_id)):
        variant.image_status = "failed"
    elif job.kind == "extract" and job.import_id and (imp := db.get(Import, job.import_id)):
        imp.status, imp.error = "failed", error


def requeue_stale(db: Session, now: datetime | None = None) -> None:
    """Jobs the helper claimed but never finished (Mac slept, helper crashed) go back in the queue."""
    now = now or utcnow()
    stale = db.scalars(select(Job).where(Job.status == "running", Job.claimed_at < now - STALE_AFTER)).all()
    for job in stale:
        if job.attempts >= MAX_ATTEMPTS:
            job.status, job.error = "failed", HELPER_STOPPED
            _mark_target_failed(db, job, "We couldn't read this file. Please try again.")
        else:
            job.status, job.claimed_at = "queued", None
            if job.kind == "image" and (variant := db.get(Variant, job.variant_id)):
                variant.image_status = "queued"
    db.commit()


def heartbeat(db: Session, engine: str | None, now: datetime | None = None) -> None:
    _beat(db, now or utcnow(), engine)
    db.commit()


def _beat(db: Session, now: datetime, engine: str | None) -> None:
    beat = db.get(Heartbeat, 1) or Heartbeat(id=1)
    beat.last_seen_at = now
    if engine:
        beat.engine = engine
    db.add(beat)


def claim_next(db: Session, engine: str | None, now: datetime | None = None) -> Job | None:
    """Hand the helper the oldest waiting job, file-reading first (someone is waiting on the check screen)."""
    now = now or utcnow()
    requeue_stale(db, now)
    _beat(db, now, engine)
    db.commit()
    candidates = db.scalars(
        select(Job.id)
        .where(Job.status == "queued")
        .order_by(case((Job.kind == "extract", 0), else_=1), Job.created_at, Job.id)
        .limit(5)
    ).all()
    for job_id in candidates:
        claimed = db.execute(
            update(Job)
            .where(Job.id == job_id, Job.status == "queued")
            .values(status="running", claimed_at=now, attempts=Job.attempts + 1)
        )
        if claimed.rowcount != 1:
            continue  # another helper got it first
        job = db.get(Job, job_id)
        db.refresh(job)
        if job.kind == "image" and (variant := db.get(Variant, job.variant_id)):
            variant.image_status = "generating"
        db.commit()
        return job
    return None


def complete_image(db: Session, storage, job: Job, image: bytes) -> None:
    if job.status != "running":
        return  # cancelled while the helper worked (photo uploaded, row removed, regenerated)
    job.status = "done"
    variant = db.get(Variant, job.variant_id) if job.variant_id else None
    if variant is not None and variant.image_source != "uploaded":
        old_keys = [variant.image_key, variant.thumb_key] if variant.image_source == "generated" else []
        variant.image_key, variant.thumb_key = save_image(storage, image)
        variant.image_source, variant.image_status = "generated", "ready"
        for key in filter(None, old_keys):
            storage.delete(key)
    db.commit()


def complete_extract(db: Session, job: Job, items: list[ExtractedItem]) -> None:
    if job.status != "running":
        return
    job.status = "done"
    imp = db.get(Import, job.import_id) if job.import_id else None
    if imp is not None and imp.status == "needs_ai":
        if items:
            imp.items, imp.status = [i.model_dump() for i in items], "ready_for_review"
        else:
            imp.status, imp.error = "failed", "We couldn't find any products in this file."
    db.commit()


def fail_job(db: Session, job: Job, error: str) -> None:
    if job.status != "running":
        return
    job.error = error[:2000]
    if job.attempts < MAX_ATTEMPTS:
        job.status, job.claimed_at = "queued", None
        if job.kind == "image" and (variant := db.get(Variant, job.variant_id)):
            variant.image_status = "queued"
    else:
        job.status = "failed"
        _mark_target_failed(db, job, "We couldn't read this file. Please try again or upload a clearer copy.")
    db.commit()


def helper_status(db: Session, now: datetime | None = None) -> dict:
    now = now or utcnow()
    beat = db.get(Heartbeat, 1)
    last_seen = beat.last_seen_at if beat else None
    return {
        "online": last_seen is not None and now - last_seen <= timedelta(seconds=30),
        "last_seen_at": last_seen,
        "engine": beat.engine if beat else None,
    }


def cancel_catalog_jobs(db: Session, catalog: Catalog) -> None:
    """Nothing left to do for a deleted catalog: stop the helper spending time on it."""
    variant_ids = [v.id for p in catalog.products for v in p.variants]
    import_ids = [i.id for i in catalog.imports]
    db.execute(
        update(Job)
        .where(Job.status.in_(("queued", "running")))
        .where((Job.variant_id.in_(variant_ids)) | (Job.import_id.in_(import_ids)))
        .values(status="cancelled")
    )
