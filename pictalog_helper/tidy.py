"""Puts the words of a row the model read back into the fields they belong to.

A small model makes the same few slips in every language (each case in tests/helper/test_tidy.py is one it made): the
colour lands in the size (size "लाल"), or stays on the end of the name ("सुती साडी, लाल"); the size or price is
repeated on the name ("पितळेचा दिवा — ₹899"); a size keeps its unit but loses its number ("लिटर"); a material word is
taken off the front of the name ("पानी की बोतल" for "स्टील की पानी की बोतल"); and a material or colour on a Hindi list
comes back in English ("Brass"). Each is undone by comparing the fields with each other and with the text that was
read, so nothing new is made up. Prompting the model not to do these made it worse at everything else."""

import re
import unicodedata

from pictalog_helper import glossary

# Between a name and what follows it: a comma (or the Urdu one), or a dash with spaces round it (not T-Shirt's).
_SEPARATOR = re.compile(r"(\s*[,،]\s*|\s+[-–—]+\s+)")
_TOKEN = re.compile(r"\d+(?:[.,]\d+)*|[^\s\d.,;:!?()\[\]/|—–\-،]+")
_CURRENCY = {"₹", "rs", "inr", "रु", "रू", "रुपये", "रुपए", "ரூ", "৳", "টাকা", "ਰੁ", "રૂ", "ରୁ", "రూ", "ರೂ", "രൂ", "روپے"}


def _digits(text: str | None) -> str:
    return "".join(str(unicodedata.decimal(c)) for c in text or "" if unicodedata.category(c) == "Nd")


def _tokens(text: str) -> list[str]:
    return [glossary.normalise(t) for t in _TOKEN.findall(text)]


def _same_colour(a: str, b: str) -> bool:
    if glossary.normalise(a) == glossary.normalise(b):
        return True
    return glossary.colour(a) is not None and glossary.colour(a) == glossary.colour(b)


def _take_colour(item: dict, word: str) -> bool:
    """Makes `word` the item's colour, unless it already has a different one."""
    current = item.get("colour")
    if current and not _same_colour(current, word):
        return False
    if not current or current.isascii():  # the list's own word rather than the model's English for it
        item["colour"] = word
    return True


def _is_price(text: str, price: str | None) -> bool:
    words = {t for t in _tokens(text) if not _digits(t)}
    return _digits(text) == _digits(price) and words <= _CURRENCY | set(_tokens(price or ""))


def _colour_from_size(item: dict) -> None:
    size = item.get("size")
    if size and not _digits(size) and glossary.colour(size) and _take_colour(item, size):
        del item["size"]


def _trim_name(item: dict) -> None:
    parts = _SEPARATOR.split(item["name"])  # name, separator, name, …
    while len(parts) >= 3:
        tail, size = parts[-1].strip(), item.get("size")
        if glossary.colour(tail) and _take_colour(item, tail):
            pass
        elif _digits(tail) and (_is_price(tail, item.get("price_text")) or _tokens(tail) == _tokens(size or "")):
            pass
        elif _digits(tail) and size and not _digits(size) and _tokens(tail)[-len(_tokens(size)):] == _tokens(size):
            item["size"] = tail  # "— 1 लिटर" on the name, "लिटर" as the size
        else:
            break
        parts = parts[:-2]
    item["name"] = "".join(parts)


def _size_number(item: dict, source: str) -> None:
    """The number in front of the size's unit on the line of the list most like the product's name."""
    size = item.get("size")
    if not size or _digits(size):
        return
    unit, named = _tokens(size), set(_tokens(item["name"]))
    best, numbers = 0, set()
    for line in source.splitlines():
        tokens = _tokens(line)
        found = {
            tokens[i] for i in range(len(tokens) - len(unit))
            if _digits(tokens[i]) and tokens[i + 1:i + 1 + len(unit)] == unit
        }
        shared = len(named & set(tokens))
        if found and shared > best:
            best, numbers = shared, found
        elif found and shared == best:
            numbers |= found
    if best and len(numbers) == 1:
        item["size"] = f"{numbers.pop()} {size}"


def _material_in_name(item: dict, source: str) -> None:
    """The name as the list writes it, when the model took a material word (not a colour) off its front."""
    name = _tokens(item["name"])
    found = set()
    for line in source.splitlines():
        for segment in _SEPARATOR.split(line)[::2]:
            tokens = _tokens(segment)
            front = tokens[:-len(name)]
            if (
                name and len(tokens) > len(name) and tokens[-len(name):] == name
                and not any(map(_digits, front)) and any(map(glossary.material, front))
            ):
                found.add(re.sub(r"^\W+", "", segment.strip()))
    if len(found) == 1:
        item["name"] = found.pop()


def _in_list_language(item: dict) -> None:
    for field in ("material", "colour"):
        value = item.get(field)
        if value and value.isascii() and (word := glossary.native(item["name"], value)):
            item[field] = word


def tidy(item: dict, source: str = "") -> dict:
    """The row with its words in the right fields; `source` is the text it was read from, or OCR's words."""
    item = dict(item)
    _colour_from_size(item)
    if item.get("name"):
        _trim_name(item)
        _size_number(item, source)
        _material_in_name(item, source)
        _in_list_language(item)
    return item
