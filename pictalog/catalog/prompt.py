import hashlib

from pictalog.models import Product, Variant

STUDIO = (
    "Single product, centered, isolated on a seamless plain white background, soft even studio lighting, "
    "sharp focus, high detail, true-to-life colours, photorealistic e-commerce photo, no watermark."
)


def build_prompt(product: Product, variant: Variant) -> str:
    description = (product.description or "").strip()[:300]
    subject = (product.name or "").strip()
    if not subject:
        subject, description = description, ""
    text = f"Professional studio product photograph of {subject}"
    if product.brand:
        text += f" by {product.brand}"
    if variant.colour:
        text += f" in {variant.colour}"
    if variant.material:
        text += f" made of {variant.material}"
    if variant.size:
        text += f", size {variant.size}"
    if product.category:
        text += f" ({product.category})"
    text += "."
    if description:
        text += f" {description.rstrip('.')}."
    return f"{text} {STUDIO}"


def seed_for(group_key: str, offset: int) -> int:
    """Variants of one product share a seed so they look like the same product; regenerating bumps the offset."""
    return int(hashlib.sha256(group_key.encode()).hexdigest()[:8], 16) + offset
