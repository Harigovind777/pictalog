"""Reading the words on a photo or scan with Tesseract, in any script it has language data for.

The page is read once with each script's language data and the reading Tesseract is most sure of wins (its own script
detection needs more text than a short price list has). Santali (Ol Chiki) and Manipuri (Meetei Mayek) have no
Tesseract data; `read` returns None for them, and for pages it can't read confidently, so the caller can use an OCR
model instead."""

import re
import shutil
import subprocess

# Script → Tesseract language data (brew install tesseract-lang). One script's data reads every language written in
# it: Devanagari covers Hindi, Marathi, Nepali, Konkani, Maithili, Dogri, Bodo and Sanskrit; Bengali covers Assamese
# and Bengali-script Manipuri.
LANGUAGES = {
    "Devanagari": "script/Devanagari",
    "Bengali": "script/Bengali",
    "Gurmukhi": "script/Gurmukhi",
    "Gujarati": "script/Gujarati",
    "Oriya": "script/Oriya",
    "Tamil": "script/Tamil",
    "Telugu": "script/Telugu",
    "Kannada": "script/Kannada",
    "Malayalam": "script/Malayalam",
    "Arabic": "urd+snd",
    "Latin": "eng",
}

# Malayalam chillu letters as Tesseract writes them (letter + virama + joiner) and as they're typed today.
_CHILLU = {"ണ്‍": "ൺ", "ന്‍": "ൻ", "ര്‍": "ർ", "ല്‍": "ൽ", "ള്‍": "ൾ", "ക്‍": "ൿ"}


def available() -> bool:
    return shutil.which("tesseract") is not None


def _run(png: bytes, *args: str) -> str:
    result = subprocess.run(["tesseract", "stdin", "stdout", *args], input=png, capture_output=True, timeout=120)
    return result.stdout.decode("utf-8", "replace")


def _confidence(png: bytes, langs: str, mode: str = "11") -> float:
    """Tesseract's average certainty (0–100) over the words it found, weighted by their length. Sparse mode (11) finds
    words one by one, so ruled tables score as well as plain lists."""
    words = [line.split("\t") for line in _run(png, "-l", langs, "--psm", mode, "tsv").splitlines()[1:]]
    scored = [(float(w[10]), len(w[11].strip())) for w in words if len(w) == 12 and w[11].strip() and float(w[10]) >= 0]
    letters = sum(n for _, n in scored)
    return sum(c * n for c, n in scored) / letters if letters else 0.0


def clean(text: str) -> str:
    """Tesseract ends words with a zero-width non-joiner after a virama, which changes nothing on screen but makes
    the same word compare unequal; and it writes Malayalam chillus the old way."""
    for old, new in _CHILLU.items():
        text = text.replace(old, new)
    return re.sub(r"\u200c(?=\s|[.,:;!?)\]—–-]|$)", "", text, flags=re.M)


def language_data(png: bytes, min_confidence: float = 75.0, min_lead: float = 8.0) -> str | None:
    """The language data that reads the page, or None unless one script's data reads it confidently and clearly better
    than the others (a script Tesseract doesn't know gets middling scores from several). English pages tie, as every
    option includes English."""
    options = [lang if lang == "eng" else f"{lang}+eng" for lang in LANGUAGES.values()]
    (best, langs), (second, _) = sorted(((_confidence(png, o), o) for o in options), reverse=True)[:2]
    if best < min_confidence:
        return None
    letters = [ch for ch in _run(png, "-l", langs, "--psm", "11") if ch.isalpha()]
    if letters and sum(ch.isascii() for ch in letters) / len(letters) > 0.8:
        return "eng"  # an English page: another script's data only adds misreadings
    return langs if best - second >= min_lead else None


def read(png: bytes) -> str | None:
    """The page's text line by line, or cell by cell when its ruled lines throw the line-by-line mode (whichever
    Tesseract is surer of); None when Tesseract can't read it."""
    langs = language_data(png)
    if not langs:
        return None
    mode = "6" if _confidence(png, langs, "6") >= _confidence(png, langs, "11") - 10 else "11"
    return clean(_run(png, "-l", langs, "--psm", mode)).strip()


def words(png: bytes) -> str | None:
    """Every word Tesseract finds, cell by cell, without the page's layout (ruled tables throw the line-by-line mode),
    or None when it can't read the page."""
    langs = language_data(png)
    if not langs:
        return None
    lines = clean(_run(png, "-l", langs, "--psm", "11")).splitlines()
    return "\n".join(line.strip() for line in lines if any(ch.isalpha() for ch in line))
