"""Product lists in India's languages: headings, numbers, encodings and lists in any script."""

import codecs
from decimal import Decimal

import pytest

from pictalog.catalog.detail import has_enough_detail
from pictalog.catalog.prompt import _visible_size
from pictalog.parsing.cells import decode_text
from pictalog.parsing.mapping import find_table, map_columns
from pictalog.parsing.price import parse_price
from pictalog.parsing.rows import split_variants
from pictalog.parsing.tables import read_tables
from pictalog.schemas import ExtractedItem


@pytest.mark.parametrize(
    "headers",
    [
        ["उत्पाद का नाम", "कोड", "मूल्य (₹)", "साइज़", "रंग", "कपड़ा", "ब्रांड", "श्रेणी", "विवरण", "फोटो"],  # Hindi
        ["वस्तूचे नाव", "कोड", "किंमत", "आकार", "रंग", "कापड", "ब्रँड", "प्रकार", "वर्णन", "फोटो"],  # Marathi
        ["পণ্যের নাম", "কোড", "দাম", "সাইজ", "রং", "কাপড়", "ব্র্যান্ড", "ধরন", "বিবরণ", "ছবি"],  # Bengali
        ["নাম", "কোড", "মূল্য", "আকাৰ", "ৰং", "কাপোৰ", "ব্ৰেণ্ড", "প্ৰকাৰ", "বিৱৰণ", "ফটো"],  # Assamese
        ["ਨਾਮ", "ਕੋਡ", "ਕੀਮਤ", "ਸਾਈਜ਼", "ਰੰਗ", "ਕੱਪੜਾ", "ਬ੍ਰਾਂਡ", "ਕਿਸਮ", "ਵੇਰਵਾ", "ਫੋਟੋ"],  # Punjabi
        ["નામ", "કોડ", "કિંમત", "સાઇઝ", "રંગ", "કાપડ", "બ્રાન્ડ", "પ્રકાર", "વર્ણન", "ફોટો"],  # Gujarati
        ["ନାମ", "କୋଡ୍", "ମୂଲ୍ୟ", "ଆକାର", "ରଙ୍ଗ", "କପଡ଼ା", "ବ୍ରାଣ୍ଡ", "ପ୍ରକାର", "ବିବରଣୀ", "ଫଟୋ"],  # Odia
        ["பொருளின் பெயர்", "குறியீடு", "விலை", "அளவு", "நிறம்", "துணி", "பிராண்ட்", "வகை", "விவரம்", "படம்"],  # Tamil
        ["పేరు", "కోడ్", "ధర", "సైజు", "రంగు", "బట్ట", "బ్రాండ్", "రకం", "వివరణ", "ఫోటో"],  # Telugu
        ["ಹೆಸರು", "ಕೋಡ್", "ಬೆಲೆ", "ಗಾತ್ರ", "ಬಣ್ಣ", "ಬಟ್ಟೆ", "ಬ್ರ್ಯಾಂಡ್", "ವರ್ಗ", "ವಿವರಣೆ", "ಫೋಟೋ"],  # Kannada
        ["പേര്", "കോഡ്", "വില", "വലിപ്പം", "നിറം", "തുണി", "ബ്രാൻഡ്", "വിഭാഗം", "വിവരണം", "ഫോട്ടോ"],  # Malayalam
        ["نام", "کوڈ", "قیمت", "سائز", "رنگ", "کپڑا", "برانڈ", "قسم", "تفصیل", "تصویر"],  # Urdu
    ],
)
def test_headings_in_indian_languages(headers):
    fields = ["name", "sku", "price", "size", "colour", "material", "brand", "category", "description", "image_url"]
    assert map_columns(headers) == dict(zip(headers, fields))


def test_headings_match_however_they_were_typed():
    # With and without nukta, with a zero-width non-joiner, Arabic rather than Persian letters, older spellings.
    assert map_columns(["साइज", "रङ्ग", "ఎంఆర్‌పి"]) == {"साइज": "size", "रङ्ग": "colour", "ఎంఆర్‌పి": "price"}
    assert map_columns(["ఎంఆర్పి", "قيمت"]) == {"ఎంఆర్పి": "price", "قيمت": None}  # each field once
    assert map_columns(["قيمت"]) == {"قيمت": "price"}


def test_headings_used_on_indian_bills():
    assert map_columns(["Sl No", "Particulars", "HSN Code", "GST Rate", "Rs."]) == {
        "Sl No": None, "Particulars": "name", "HSN Code": None, "GST Rate": None, "Rs.": "price",
    }
    assert map_columns(["Item Name", "Net Wt", "Pin Code"]) == {"Item Name": "name", "Net Wt": "size", "Pin Code": None}
    assert map_columns(["Naam", "Keemat", "Rang"]) == {"Naam": "name", "Keemat": "price", "Rang": "colour"}  # Hindi in English letters


def test_find_table_in_hindi():
    table = [
        ["शर्मा किराना स्टोर — मूल्य सूची", "", ""],
        ["वस्तु", "वज़न", "दाम"],
        ["बासमती चावल", "1 किलो", "₹ 120"],
        ["सरसों का तेल", "1 लीटर", "₹ १८५"],
    ]
    match = find_table([table])
    assert match is not None
    assert match.mapping == {"वस्तु": "name", "वज़न": "size", "दाम": "price"}
    assert match.rows[1] == ["सरसों का तेल", "1 लीटर", "₹ १८५"]


def test_decode_utf16_files_from_excel():
    text = "नाम\tदाम\nचाय\t120\n"
    assert decode_text(codecs.BOM_UTF16_LE + text.encode("utf-16-le")) == text
    assert decode_text(text.encode("utf-16-le")) == text  # no byte-order mark
    assert decode_text(text.encode("utf-8")) == text


def test_tab_separated_text_is_read_as_a_table():
    text = "பெயர்\tவிலை\nகாபி தூள்\t250\n"  # Excel's "Unicode Text" export: UTF-16, tab-separated
    tables = read_tables("text", codecs.BOM_UTF16_LE + text.encode("utf-16-le"))
    assert tables == [[["பெயர்", "விலை"], ["காபி தூள்", "250"]]]
    assert read_tables("text", "Our new range of soaps, all handmade.\nPrice on request.".encode()) == []


def test_prices_in_indian_digits():
    assert parse_price("₹ १,२९९") == Decimal("1299")
    assert parse_price("৳ ২৫০") == Decimal("250")  # Bengali digits
    assert parse_price("ரூ. 1,20,000") == Decimal("120000")
    assert parse_price("روپے ۱۵۰") == Decimal("150")  # Urdu digits
    assert parse_price("₹ 499/-") == Decimal("499")


def test_lists_split_in_any_script():
    items = split_variants(ExtractedItem(name="कुर्ता", colour="लाल, नीला", size="M/L"))
    assert [(i.size, i.colour) for i in items] == [("M", "लाल"), ("M", "नीला"), ("L", "लाल"), ("L", "नीला")]
    urdu = split_variants(ExtractedItem(name="قمیص", colour="سرخ، نیلا"))
    assert [i.colour for i in urdu] == ["سرخ", "نیلا"]


@pytest.mark.parametrize("name", ["चाय", "घी", "பை", "చీర", "ಸೀರೆ", "ചായ", "চা", "چائے", "ਦਾਲ"])
def test_short_names_in_indian_scripts_are_real_names(name):
    assert has_enough_detail(ExtractedItem(name=name))


def test_codes_are_still_not_names():
    assert not has_enough_detail(ExtractedItem(name="A-1234"))
    assert not has_enough_detail(ExtractedItem(name="१२३४"))


def test_visible_sizes_in_indian_languages():
    assert _visible_size("1 लीटर") == "1 लीटर"
    assert _visible_size("500 ग्राम") == "500 ग्राम"
    assert _visible_size("साइज़ 8") is None
    assert _visible_size("அளவு 40") is None


def _pdf_with(lines: list[str]) -> bytes:
    import io

    from reportlab.pdfgen.canvas import Canvas

    from pictalog.pdf_text import draw

    buf = io.BytesIO()
    c = Canvas(buf)
    for i, line in enumerate(lines):
        draw(c, 50, 700 - 30 * i, line, 14)
    c.save()
    return buf.getvalue()


def test_pdfs_whose_indian_text_comes_out_broken_are_read_as_pictures():
    from pictalog.parsing.tables import extract_text

    # Joined letters come out as private characters and vowel signs in drawing order (ேകാ for കോ).
    pdf = _pdf_with(["वस्तु — दाम", "स्टील की पानी की बोतल — ₹350", "കോട്ടൺ സാരി — ₹1,450"])
    assert read_tables("pdf", pdf) == []
    assert extract_text("pdf", pdf) == ""


def test_pdfs_with_clean_text_are_still_read():
    from pictalog.parsing.tables import extract_text

    assert "Steel bottle" in extract_text("pdf", _pdf_with(["Steel bottle — ₹350"]))
    assert "चाय" in extract_text("pdf", _pdf_with(["चाय — ₹120"]))  # no joined letters: nothing broken
