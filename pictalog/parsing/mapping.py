from dataclasses import dataclass

from pictalog.parsing.headings import field_for
from pictalog.parsing.tables import Table
from pictalog.schemas import ItemField


def _fields(headers: list[str]) -> list[ItemField | None]:
    """Field per column position; each field goes to the first column that claims it."""
    fields: list[ItemField | None] = []
    for header in headers:
        field = field_for(header)
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
