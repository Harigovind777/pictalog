import math
from datetime import date, datetime


def clean_cell(value: object) -> str:
    """Turn a raw cell from any reader into tidy text ("499.0" → "499", dates → ISO, blanks → "")."""
    if value is None:
        return ""
    if isinstance(value, float):
        if math.isnan(value):
            return ""
        return str(int(value)) if value.is_integer() else str(value)
    if isinstance(value, datetime):
        if value != value:  # pandas NaT
            return ""
        return value.date().isoformat() if value.time() == datetime.min.time() else value.isoformat(sep=" ")
    if isinstance(value, date):
        return value.isoformat()
    text = str(value).strip()
    return "" if text in ("nan", "NaT", "None") else text


def decode_text(data: bytes) -> str:
    """Decode text files saved by Excel and friends: UTF-8 (with or without BOM), then Windows-1252, then Latin-1."""
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("latin-1")
