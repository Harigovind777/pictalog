import re
from decimal import Decimal, InvalidOperation

_NUMBER = re.compile(r"\d[\d.,]*\d|\d")


def parse_price(text: str | None) -> Decimal | None:
    """First number in a price, understanding 1,299.00 / 4,50 / 2,49,999 / 1.299.000 styles."""
    if not text:
        return None
    match = _NUMBER.search(text)
    if not match:
        return None
    number = match.group()
    if "," in number and "." in number:
        decimal_sep = "," if number.rfind(",") > number.rfind(".") else "."
        thousands = "." if decimal_sep == "," else ","
        number = number.replace(thousands, "").replace(decimal_sep, ".")
    elif "," in number:
        is_decimal = number.count(",") == 1 and re.search(r",\d{1,2}$", number)
        number = number.replace(",", ".") if is_decimal else number.replace(",", "")
    elif number.count(".") > 1:
        number = number.replace(".", "")
    try:
        return Decimal(number)
    except InvalidOperation:
        return None
