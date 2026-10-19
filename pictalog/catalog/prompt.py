import hashlib
import re

from pictalog.models import Product, Variant
from pictalog.parsing.headings import normalise

STUDIO = (
    "Single product, centered, isolated on a seamless plain white background, soft even studio lighting, "
    "sharp focus, high detail, true-to-life colours, photorealistic e-commerce photo, "
    "no added text, letters, numbers or watermark."
)


# "Size 8" in India's languages: a numbered size, not a measurement.
_SIZE_WORDS = "|".join(
    normalise(w) for w in ["size", "साइज़", "साईज़", "नाप", "সাইজ", "ਸਾਈਜ਼", "સાઇઝ", "ସାଇଜ୍", "அளவு", "சைஸ்", "సైజు",
                           "ಸೈಜ್", "ಗಾತ್ರ", "സൈസ്", "വലിപ്പം", "سائز"]
)


def _visible_size(size: str | None) -> str | None:
    """Sizes with a unit (1 L, 350 ml, 5kg, 1 लीटर) change how a product looks. Letter or bare-number sizes (M, XL, 8,
    साइज़ 8) don't, and putting them in the prompt makes the model print them on the product."""
    if (
        size
        and re.search(r"\d", size)
        and re.search(r"[^\W\d_]", size)
        and not re.fullmatch(rf"(?:{_SIZE_WORDS}) \d+", normalise(size))
    ):
        return size.strip()
    return None


def build_subject(product: Product, variant: Variant) -> str:
    """What the product is and looks like, e.g. "Classic Tee by Acme in Red made of Cotton (Apparel). Soft cotton."."""
    description = (product.description or "").strip()[:300]
    subject = (product.name or "").strip()
    if not subject:
        subject, description = description, ""
    text = subject
    if product.brand:
        text += f" by {product.brand}"
    if variant.colour:
        text += f" in {variant.colour}"
    if variant.material:
        text += f" made of {variant.material}"
    if size := _visible_size(variant.size):
        text += f", {size}"
    if product.category:
        text += f" ({product.category})"
    text += "."
    if description:
        text += f" {description.rstrip('.')}."
    return text


def build_prompt(product: Product, variant: Variant) -> str:
    return f"Professional studio product photograph of {build_subject(product, variant)} {STUDIO}"


def seed_for(group_key: str, offset: int) -> int:
    """Variants of one product share a seed so they look like the same product; regenerating bumps the offset."""
    return int(hashlib.sha256(group_key.encode()).hexdigest()[:8], 16) + offset
