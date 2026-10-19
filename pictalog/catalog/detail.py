import unicodedata

from pictalog.schemas import ExtractedItem


def _is_word(token: str) -> bool:
    """A word rather than a code: no digits, and three Latin letters or two characters of another script. Indian
    scripts write a syllable as a letter plus vowel signs, so चाय (tea) or பை (bag) is short but a real word."""
    if any(ch.isdigit() for ch in token):
        return False
    letters = [ch for ch in token if unicodedata.category(ch)[0] in "LM"]
    latin = sum(unicodedata.name(ch, "").startswith("LATIN") for ch in letters)
    return latin >= 3 or len(letters) - latin >= 2


def has_enough_detail(item: ExtractedItem) -> bool:
    """True when there's a real product name or description to picture (not just a product code)."""
    name = item.name or ""
    if item.sku and name.strip().lower() == item.sku.strip().lower():
        name = ""
    text = f"{name} {item.description or ''}"
    return any(_is_word(token) for token in text.split())
