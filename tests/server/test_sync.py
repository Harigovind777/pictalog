from decimal import Decimal

from sqlalchemy import select

from pictalog.catalog.sync import apply_items, diff_items, group_key, match_key
from pictalog.models import Job, Product, Variant
from pictalog.schemas import ExtractedItem as Item


def variants(db, catalog) -> list[Variant]:
    db.refresh(catalog)
    return [v for p in catalog.products for v in p.variants]


def queued_jobs(db) -> list[Job]:
    return db.scalars(select(Job).where(Job.status == "queued")).all()


def mark_ready(db, variant: Variant, source: str = "generated") -> None:
    variant.image_key, variant.thumb_key = "img/a.webp", "img/a_t.webp"
    variant.image_source, variant.image_status = source, "ready"
    for job in queued_jobs(db):
        job.status = "done"
    db.commit()


def test_keys():
    assert match_key(Item(name="Tee", sku=" T-1 ")) == "sku:t-1"
    assert match_key(Item(name="Classic  Tee", size="M", colour="Red")) == "nv:classic tee|m|red|"
    assert group_key(Item(name="Tee", brand="Acme")) == "acme|tee"
    assert group_key(Item(description="Blue ceramic mug")) == "|blue ceramic mug"


def test_apply_new_items_queue_images(db, catalog):
    diff = apply_items(db, catalog, [
        Item(name="Tee", size="S", price_text="499"),
        Item(name="Tee", size="M", price_text="499"),
        Item(sku="SKU-1"),
    ])
    assert len(diff.new) == 3
    vs = variants(db, catalog)
    assert [v.image_status for v in vs] == ["queued", "queued", "not_enough_detail"]
    assert len(queued_jobs(db)) == 2
    assert len(catalog.products) == 2
    assert [v.size for v in catalog.products[0].variants] == ["S", "M"]
    assert vs[0].price_value == Decimal("499")
    job = queued_jobs(db)[0]
    assert job.kind == "image" and job.variant_id == vs[0].id
    assert job.payload["prompt"].startswith("Professional studio product photograph of Tee. ")
    assert job.payload["seed"] == queued_jobs(db)[1].payload["seed"]  # same product, same seed


def test_apply_provided_image_url(db, catalog):
    apply_items(db, catalog, [Item(name="Mug", image_url="https://example.com/mug.jpg")])
    [v] = variants(db, catalog)
    assert v.image_status == "ready" and v.image_source == "provided"
    assert v.image_url_source == "https://example.com/mug.jpg"
    assert queued_jobs(db) == []


def test_price_only_change_keeps_image(db, catalog):
    apply_items(db, catalog, [Item(name="Tee", size="S", price_text="499")])
    [v] = variants(db, catalog)
    mark_ready(db, v)
    diff = apply_items(db, catalog, [Item(name="Tee", size="S", price_text="599")])
    assert len(diff.changed) == 1 and diff.changed[0][2] is False
    [v] = variants(db, catalog)
    assert v.price_value == Decimal("599")
    assert v.image_status == "ready" and v.image_key == "img/a.webp"
    assert queued_jobs(db) == []


def test_unchanged_rows_counted(db, catalog):
    apply_items(db, catalog, [Item(name="Tee", size="S")])
    diff = diff_items(db, catalog, [Item(name="Tee", size="S")])
    assert diff.unchanged == 1 and not diff.new and not diff.changed and not diff.removed


def test_visual_change_requeues_generated_but_not_uploaded(db, catalog):
    apply_items(db, catalog, [Item(name="Tee", sku="T1", colour="Red"), Item(name="Mug", sku="M1", colour="White")])
    tee, mug = variants(db, catalog)
    mark_ready(db, tee, "generated")
    mark_ready(db, mug, "uploaded")
    diff = apply_items(db, catalog, [Item(name="Tee", sku="T1", colour="Blue"), Item(name="Mug", sku="M1", colour="Black")])
    assert [c[2] for c in diff.changed] == [True, True]
    tee, mug = variants(db, catalog)
    assert tee.image_status == "queued" and tee.colour == "Blue"
    assert mug.image_status == "ready" and mug.image_key == "img/a.webp" and mug.colour == "Black"
    assert [j.variant_id for j in queued_jobs(db)] == [tee.id]


def test_removed_rows_deleted(db, catalog):
    apply_items(db, catalog, [Item(name="Tee"), Item(name="Mug")])
    diff = apply_items(db, catalog, [Item(name="Tee")])
    assert len(diff.removed) == 1 and diff.removed_names == ["Mug"]
    assert [p.name for p in catalog.products] == ["Tee"]
    assert db.scalars(select(Product).where(Product.name == "Mug")).all() == []
    assert [j.variant_id for j in queued_jobs(db)] == [variants(db, catalog)[0].id]  # Mug's job cancelled


def test_match_by_sku_survives_rename(db, catalog):
    apply_items(db, catalog, [Item(name="Tee", sku="T1")])
    diff = apply_items(db, catalog, [Item(name="Classic Tee", sku="T1")])
    assert len(diff.changed) == 1 and not diff.new and not diff.removed
    assert [p.name for p in catalog.products] == ["Classic Tee"]


def test_duplicate_rows_kept_separately(db, catalog):
    diff = apply_items(db, catalog, [Item(name="Tee"), Item(name="Tee")])
    assert len(diff.new) == 2
    assert len(variants(db, catalog)) == 2
    assert diff_items(db, catalog, [Item(name="Tee"), Item(name="Tee")]).unchanged == 2


def test_diff_summary():
    from pictalog.catalog.sync import Diff

    diff = Diff(new=[Item(name="Tee", size="S", colour="Red")], changed=[(1, Item(name="Mug"), False)],
                removed=[2], removed_names=["Bowl"], unchanged=3)
    assert diff.summary() == {
        "new": 1, "changed": 1, "removed": 1, "unchanged": 3,
        "new_names": ["Tee · S · Red"], "changed_names": ["Mug"], "removed_names": ["Bowl"],
    }
