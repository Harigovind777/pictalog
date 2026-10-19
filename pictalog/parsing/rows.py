import itertools
import re

from pictalog.parsing.mapping import TableMatch
from pictalog.schemas import ExtractedItem

# Split "S, M, L", "Red/Blue" or "سرخ، نیلا" (Urdu comma) but not "1,000 ml" or "10/12": a separator with digits on
# both sides stays.
_LIST_SEPARATOR = re.compile(r"\s*(?:(?<!\d)[,/;|،]|[,/;|،](?!\d))\s*")

_FIELD_TO_ATTR = {"price": "price_text"}


def rows_to_items(match: TableMatch) -> list[ExtractedItem]:
    items: list[ExtractedItem] = []
    for row in match.rows:
        values: dict[str, str] = {}
        extra: dict[str, str] = {}
        for header, cell in zip(match.headers, row):
            if not cell:
                continue
            field = match.mapping.get(header)
            if field:
                values[_FIELD_TO_ATTR.get(field, field)] = cell
            else:
                extra[header] = cell
        items += split_variants(ExtractedItem(**values, extra=extra))
    return items


def _parts(value: str | None) -> list[str | None]:
    if not value:
        return [value]
    parts = [p for p in _LIST_SEPARATOR.split(value) if p.strip()]
    return parts or [value]


def split_variants(item: ExtractedItem) -> list[ExtractedItem]:
    """One item per size × colour when a cell lists several values."""
    combos = list(itertools.product(_parts(item.size), _parts(item.colour)))
    if len(combos) == 1:
        return [item]
    return [item.model_copy(update={"size": size, "colour": colour}) for size, colour in combos]
