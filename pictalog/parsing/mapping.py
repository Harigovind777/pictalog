import re
from dataclasses import dataclass

from pictalog.parsing.tables import Table
from pictalog.schemas import ItemField

FIELD_SYNONYMS: dict[ItemField, list[str]] = {
    "name": ["name", "product", "product name", "item", "item name", "title", "product title", "article", "model"],
    "sku": [
        "sku", "code", "item code", "product code", "id", "product id", "item id", "article no", "article number",
        "part no", "part number", "barcode", "ean", "upc", "style no", "style number", "model no", "model number",
    ],
    "price": [
        "price", "mrp", "rate", "cost", "unit price", "selling price", "retail price", "amount", "sale price",
    ],
    "size": [
        "size", "sizes", "dimension", "dimensions", "volume", "weight", "net weight", "capacity", "pack size",
        "net quantity", "net qty",
    ],
    "colour": ["colour", "colours", "color", "colors", "shade", "finish"],
    "material": ["material", "materials", "fabric", "composition"],
    "brand": ["brand", "make", "manufacturer"],
    "category": [
        "category", "type", "department", "collection", "group", "product type", "sub category", "subcategory",
    ],
    "description": [
        "description", "product description", "details", "desc", "features", "specification", "specifications",
        "specs", "notes",
    ],
    "image_url": ["image", "image url", "image link", "photo", "picture", "img", "thumbnail", "photo url"],
}

_EXACT = {syn: field for field, syns in FIELD_SYNONYMS.items() for syn in syns}
_BY_LENGTH = sorted(_EXACT.items(), key=lambda kv: len(kv[0]), reverse=True)


def _normalise(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def _field_for(header: str) -> ItemField | None:
    norm = _normalise(header)
    if not norm:
        return None
    if norm in _EXACT:
        return _EXACT[norm]
    padded = f" {norm} "
    return next((field for syn, field in _BY_LENGTH if f" {syn} " in padded), None)


def _fields(headers: list[str]) -> list[ItemField | None]:
    """Field per column position; each field goes to the first column that claims it."""
    fields: list[ItemField | None] = []
    for header in headers:
        field = _field_for(header)
        fields.append(None if field in fields else field)
    return fields


def map_columns(headers: list[str]) -> dict[str, ItemField | None]:
    return dict(zip(headers, _fields(headers)))


@dataclass
class TableMatch:
    headers: list[str]
    rows: list[list[str]]
    mapping: dict[str, ItemField | None]


def _unique_headers(raw: list[str]) -> list[str]:
    headers: list[str] = []
    for i, header in enumerate(raw):
        name = header or f"Column {i + 1}"
        candidate, n = name, 2
        while candidate in headers:
            candidate, n = f"{name} ({n})", n + 1
        headers.append(candidate)
    return headers


def find_table(tables: list[Table]) -> TableMatch | None:
    """Find the product table: the row (in the first 10 of any table) that looks most like a header."""
    best: tuple[int, Table, int] | None = None  # (score, table, header row index)
    for table in tables:
        for index, row in enumerate(table[:10]):
            fields = [f for f in _fields(row) if f]
            if len(fields) < 2 or not ({"name", "description"} & set(fields)):
                continue
            if best is None or len(fields) > best[0]:
                best = (len(fields), table, index)
    if best is None:
        return None
    _, table, index = best
    headers = _unique_headers(table[index])
    width = len(headers)
    rows = [
        (row + [""] * width)[:width]
        for row in table[index + 1 :]
        if any(cell.strip() for cell in row)
    ]
    return TableMatch(headers=headers, rows=rows, mapping=map_columns(headers))
