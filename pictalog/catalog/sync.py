"""Bring a catalog in line with the rows of an uploaded file: add new rows, update changed ones, drop removed ones."""

import hashlib
import json
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from pictalog.catalog.detail import has_enough_detail
from pictalog.jobs import cancel_image_jobs, enqueue_image
from pictalog.models import Catalog, Product, Variant, utcnow
from pictalog.parsing.price import parse_price
from pictalog.schemas import ExtractedItem

VISUAL_FIELDS = ("name", "brand", "category", "description", "size", "colour", "material", "image_url")
MAX_NAMES = 20


def _norm(text: str | None) -> str:
    return " ".join((text or "").lower().split())


def _subject(item: ExtractedItem) -> str:
    return item.name or (item.description or "")[:60] or item.sku or ""


def group_key(item: ExtractedItem) -> str:
    return f"{_norm(item.brand)}|{_norm(_subject(item))}"


def match_key(item: ExtractedItem) -> str:
    if item.sku and item.sku.strip():
        return "sku:" + _norm(item.sku)
    return "nv:" + "|".join(_norm(v) for v in (_subject(item), item.size, item.colour, item.material))


def _sha1(text: str) -> str:
    return hashlib.sha1(text.encode()).hexdigest()


def visual_hash(item: ExtractedItem) -> str:
    """Everything that changes how the product looks. Price and extra columns are deliberately left out."""
    return _sha1("\x1f".join(getattr(item, f) or "" for f in VISUAL_FIELDS))


def row_hash(item: ExtractedItem) -> str:
    return _sha1(json.dumps(item.model_dump(), sort_keys=True, ensure_ascii=False))


def _label(name: str | None, size: str | None, colour: str | None) -> str:
    return " · ".join(x for x in (name, size, colour) if x) or "Untitled"


def _item_label(item: ExtractedItem) -> str:
    return _label(_subject(item), item.size, item.colour)


@dataclass
class Diff:
    new: list[ExtractedItem] = field(default_factory=list)
    changed: list[tuple[int, ExtractedItem, bool]] = field(default_factory=list)  # (variant_id, item, visual?)
    removed: list[int] = field(default_factory=list)
    removed_names: list[str] = field(default_factory=list)
    unchanged: int = 0

    def summary(self) -> dict:
        return {
            "new": len(self.new),
            "changed": len(self.changed),
            "removed": len(self.removed),
            "unchanged": self.unchanged,
            "new_names": [_item_label(i) for i in self.new[:MAX_NAMES]],
            "changed_names": [_item_label(i) for _, i, _ in self.changed[:MAX_NAMES]],
            "removed_names": self.removed_names[:MAX_NAMES],
        }


def _unique_keys(items: list[ExtractedItem]) -> list[str]:
    """Match keys in file order; repeated rows get "#2", "#3" so each row stays its own variant."""
    seen: dict[str, int] = {}
    keys = []
    for item in items:
        key = match_key(item)
        seen[key] = seen.get(key, 0) + 1
        keys.append(key if seen[key] == 1 else f"{key}#{seen[key]}")
    return keys


def _existing(catalog: Catalog) -> dict[str, Variant]:
    return {v.match_key: v for p in catalog.products for v in p.variants}


def diff_items(db: Session, catalog: Catalog, items: list[ExtractedItem]) -> Diff:
    existing = _existing(catalog)
    diff = Diff()
    for key, item in zip(_unique_keys(items), items):
        variant = existing.pop(key, None)
        if variant is None:
            diff.new.append(item)
        elif variant.row_hash != row_hash(item):
            diff.changed.append((variant.id, item, variant.visual_hash != visual_hash(item)))
        else:
            diff.unchanged += 1
    diff.removed = [v.id for v in existing.values()]
    diff.removed_names = [_label(v.product.name or v.sku, v.size, v.colour) for v in existing.values()]
    return diff


def apply_items(db: Session, catalog: Catalog, items: list[ExtractedItem]) -> Diff:
    diff = diff_items(db, catalog, items)
    keys = _unique_keys(items)
    existing = _existing(catalog)

    for key in set(existing) - set(keys):
        variant = existing.pop(key)
        cancel_image_jobs(db, variant.id)
        variant.product.variants.remove(variant)  # delete-orphan cascade removes it

    products = {p.group_key: p for p in catalog.products}
    ordered: list[Product] = []
    for position, (key, item) in enumerate(zip(keys, items)):
        gkey = group_key(item)
        product = products.get(gkey)
        if product is None:
            product = Product(group_key=gkey)
            catalog.products.append(product)
            products[gkey] = product
        product.name, product.brand = item.name, item.brand
        product.category, product.description = item.category, item.description
        if product not in ordered:
            product.position = len(ordered)
            ordered.append(product)

        variant = existing.get(key)
        is_new = variant is None
        if variant is None:
            variant = Variant(match_key=key)
            product.variants.append(variant)
        elif variant.product is not product:
            variant.product = product
        visual_changed = variant.visual_hash != visual_hash(item)
        variant.sku, variant.size, variant.colour, variant.material = item.sku, item.size, item.colour, item.material
        variant.price_text, variant.price_value = item.price_text, parse_price(item.price_text)
        variant.extra = dict(item.extra)
        variant.position = position
        variant.visual_hash, variant.row_hash = visual_hash(item), row_hash(item)
        db.flush()
        _decide_image(db, variant, item, is_new, visual_changed)

    db.flush()
    for product in list(catalog.products):
        if not product.variants:
            catalog.products.remove(product)
    catalog.updated_at = utcnow()
    db.commit()
    db.refresh(catalog)
    return diff


def _decide_image(db: Session, variant: Variant, item: ExtractedItem, is_new: bool, visual_changed: bool) -> None:
    if variant.image_source == "uploaded":
        return  # a photo the company uploaded is never replaced by an import
    if item.image_url:
        if is_new or variant.image_source != "provided" or variant.image_url_source != item.image_url:
            cancel_image_jobs(db, variant.id)
            variant.image_url_source = item.image_url
            variant.image_source, variant.image_status = "provided", "ready"
            variant.image_key = variant.thumb_key = None
        return
    if not (is_new or visual_changed):
        return  # e.g. only the price changed
    variant.image_url_source = None
    if has_enough_detail(item):
        if variant.image_source == "provided":
            variant.image_source = "none"
        enqueue_image(db, variant)
    else:
        cancel_image_jobs(db, variant.id)
        variant.image_source, variant.image_status = "none", "not_enough_detail"
        variant.image_key = variant.thumb_key = None
