from decimal import Decimal

from pictalog.parsing.mapping import TableMatch
from pictalog.parsing.price import parse_price
from pictalog.parsing.rows import rows_to_items, split_variants
from pictalog.schemas import ExtractedItem


def test_rows_to_items_extra_and_split():
    match = TableMatch(
        headers=["Name", "Size", "Colour", "Fit"],
        rows=[["Tee", "S, M, L", "Red/Blue", "Slim"]],
        mapping={"Name": "name", "Size": "size", "Colour": "colour", "Fit": None},
    )
    items = rows_to_items(match)
    assert len(items) == 6
    assert all(i.name == "Tee" and i.extra == {"Fit": "Slim"} for i in items)
    assert [(i.size, i.colour) for i in items] == [
        ("S", "Red"), ("S", "Blue"), ("M", "Red"), ("M", "Blue"), ("L", "Red"), ("L", "Blue"),
    ]


def test_rows_to_items_maps_price_and_skips_empty_extra():
    match = TableMatch(
        headers=["Product", "MRP", "Notes"],
        rows=[["Mug", "₹199", ""]],
        mapping={"Product": "name", "MRP": "price", "Notes": None},
    )
    [item] = rows_to_items(match)
    assert item.price_text == "₹199"
    assert item.extra == {}
    assert item.size is None


def test_split_keeps_numbers():
    assert len(split_variants(ExtractedItem(name="Bottle", size="1,000 ml"))) == 1
    assert [i.size for i in split_variants(ExtractedItem(name="Shoe", size="6, 8"))] == ["6", "8"]
    assert [i.colour for i in split_variants(ExtractedItem(name="Tee", colour="Red | Blue; Green"))] == [
        "Red", "Blue", "Green",
    ]


def test_parse_price():
    assert parse_price("₹1,299.00") == Decimal("1299.00")
    assert parse_price("4,50 €") == Decimal("4.50")
    assert parse_price("$12") == Decimal("12")
    assert parse_price("Rs. 2,49,999") == Decimal("249999")
    assert parse_price("on request") is None
    assert parse_price(None) is None
