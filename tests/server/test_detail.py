from pictalog.catalog.detail import has_enough_detail
from pictalog.schemas import ExtractedItem


def test_has_enough_detail():
    assert has_enough_detail(ExtractedItem(name="Cotton T-Shirt"))
    assert not has_enough_detail(ExtractedItem(name="SKU-10023"))
    assert has_enough_detail(ExtractedItem(description="Blue ceramic mug"))
    assert not has_enough_detail(ExtractedItem(name="A1234"))
    assert not has_enough_detail(ExtractedItem(name="MUG", sku="MUG"))
    assert not has_enough_detail(ExtractedItem())
    assert not has_enough_detail(ExtractedItem(name="X"))
