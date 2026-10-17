from sqlalchemy import update
from sqlalchemy.orm import Session

from pictalog.catalog.prompt import build_prompt, seed_for
from pictalog.models import Job, Variant


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
            "seed": seed_for(product.group_key, variant.seed_offset),
        },
    )
    variant.image_status = "queued"
    db.add(job)
    return job
