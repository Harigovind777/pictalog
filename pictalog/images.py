import io
import uuid

from PIL import Image, ImageOps, UnidentifiedImageError

THUMB_SIZE = 400


def new_image_keys() -> tuple[str, str]:
    name = uuid.uuid4().hex
    return f"img/{name}.webp", f"img/{name}_t.webp"


def to_webp_pair(data: bytes) -> tuple[bytes, bytes]:
    """Full-size WebP plus a thumbnail whose long side is 400 px."""
    try:
        image = Image.open(io.BytesIO(data))
        image.load()
    except (UnidentifiedImageError, OSError) as e:
        raise ValueError("Not an image file") from e
    image = ImageOps.exif_transpose(image)
    if image.mode not in ("RGB", "RGBA"):
        image = image.convert("RGBA" if "A" in image.getbands() else "RGB")

    full = io.BytesIO()
    image.save(full, "WEBP", quality=90)
    thumb_image = image.copy()
    thumb_image.thumbnail((THUMB_SIZE, THUMB_SIZE))
    thumb = io.BytesIO()
    thumb_image.save(thumb, "WEBP", quality=85)
    return full.getvalue(), thumb.getvalue()
