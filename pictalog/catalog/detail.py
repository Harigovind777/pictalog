from pictalog.schemas import ExtractedItem


def _is_word(token: str) -> bool:
    return not any(ch.isdigit() for ch in token) and sum(ch.isalpha() for ch in token) >= 3


def has_enough_detail(item: ExtractedItem) -> bool:
    """True when there's a real product name or description to picture (not just a product code)."""
    name = item.name or ""
    if item.sku and name.strip().lower() == item.sku.strip().lower():
        name = ""
    text = f"{name} {item.description or ''}"
    return any(_is_word(token) for token in text.split())
