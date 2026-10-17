from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session

from pictalog.api.deps import read_upload, store_image
from pictalog.auth import current_user
from pictalog.db import get_db
from pictalog.jobs import cancel_image_jobs, enqueue_image
from pictalog.models import User, Variant
from pictalog.schemas import VariantOut

router = APIRouter(prefix="/api/variants")


def get_owned_variant(db: Session, user: User, variant_id: int) -> Variant:
    variant = db.get(Variant, variant_id)
    if variant is None or variant.product.catalog.user_id != user.id:
        raise HTTPException(404, "Product not found.")
    return variant


@router.post("/{variant_id}/regenerate")
def regenerate(variant_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)) -> VariantOut:
    """A new take on the image — also how "Generate anyway" works for rows without enough detail."""
    variant = get_owned_variant(db, user, variant_id)
    variant.seed_offset += 1
    if variant.image_source in ("provided", "uploaded"):
        variant.image_source = "none"  # asking for an AI image replaces the photo once it's ready
    enqueue_image(db, variant)
    db.commit()
    return VariantOut.of(variant)


@router.post("/{variant_id}/image")
async def upload_photo(
    variant_id: int, file: UploadFile, request: Request, user: User = Depends(current_user), db: Session = Depends(get_db)
) -> VariantOut:
    variant = get_owned_variant(db, user, variant_id)
    full_key, thumb_key = store_image(request, await read_upload(file, request))
    cancel_image_jobs(db, variant.id)
    variant.image_key, variant.thumb_key = full_key, thumb_key
    variant.image_source, variant.image_status = "uploaded", "ready"
    db.commit()
    return VariantOut.of(variant)
