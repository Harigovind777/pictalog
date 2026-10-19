"""Column headings that name each kind of product information, in English and in India's languages.

Headings are compared after `normalise`, so the lists below can be written the way people usually type them:
with or without nuktas (साइज़ / साइज), with zero-width joiners, in Arabic or Persian letter forms (قيمت / قیمت)."""

import unicodedata

from pictalog.schemas import ItemField

ENGLISH: dict[ItemField, list[str]] = {
    "name": [
        "name", "product", "product name", "item", "item name", "title", "product title", "article", "model",
        "particulars", "item particulars", "goods",
    ],
    "sku": [
        "sku", "code", "item code", "product code", "id", "product id", "item id", "article no", "article number",
        "part no", "part number", "barcode", "ean", "upc", "style no", "style number", "model no", "model number",
    ],
    "price": [
        "price", "mrp", "rate", "cost", "unit price", "selling price", "retail price", "amount", "sale price",
        "rs", "inr", "offer price",
    ],
    "size": [
        "size", "sizes", "dimension", "dimensions", "volume", "weight", "net weight", "capacity", "pack size",
        "net quantity", "net qty", "wt", "net wt",
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

# Shop price lists across India. Several languages share a script (Hindi, Marathi, Nepali, Konkani, Maithili, Dogri,
# Bodo and Sanskrit all use Devanagari), so a word listed once covers every language that writes it that way.
INDIAN: dict[str, dict[ItemField, list[str]]] = {
    "Hindi": {
        "name": ["नाम", "उत्पाद", "उत्पाद का नाम", "वस्तु", "वस्तु का नाम", "सामान", "माल", "आइटम", "प्रोडक्ट"],
        "sku": ["कोड", "आइटम कोड", "उत्पाद कोड"],
        "price": [
            "मूल्य", "कीमत", "क़ीमत", "दाम", "दर", "रेट", "एमआरपी", "बिक्री मूल्य", "विक्रय मूल्य", "खुदरा मूल्य",
            "अधिकतम खुदरा मूल्य", "रुपये", "राशि",
        ],
        "size": ["साइज़", "आकार", "नाप", "माप", "वज़न", "शुद्ध वज़न", "भार"],
        "colour": ["रंग", "रङ्ग", "कलर"],
        "material": ["सामग्री", "कपड़ा", "फ़ैब्रिक", "धातु"],
        "brand": ["ब्रांड", "कंपनी", "निर्माता"],
        "category": ["श्रेणी", "वर्ग", "प्रकार", "किस्म", "कैटेगरी"],
        "description": ["विवरण", "वर्णन", "जानकारी", "विशेषताएँ", "विशेषताएं"],
        "image_url": ["चित्र", "फ़ोटो", "तस्वीर", "छवि"],
    },
    "Marathi, Konkani and Nepali": {
        "name": ["नाव", "नांव", "वस्तू", "वस्तूचे नाव", "उत्पादन"],
        "price": ["किंमत", "मोल"],
        "size": ["वजन", "तौल"],
        "colour": ["रङ"],
        "material": ["कापड", "साहित्य"],
        "brand": ["ब्रँड", "ब्रान्ड"],
        "description": ["तपशील", "माहिती"],
    },
    "Bengali": {
        "name": ["নাম", "পণ্য", "পণ্যের নাম", "জিনিস"],
        "sku": ["কোড"],
        "price": ["দাম", "মূল্য", "দর", "এমআরপি"],
        "size": ["সাইজ", "মাপ", "আকার", "ওজন"],
        "colour": ["রং", "রঙ"],
        "material": ["কাপড়", "উপাদান"],
        "brand": ["ব্র্যান্ড", "কোম্পানি"],
        "category": ["ধরন", "বিভাগ", "শ্রেণী"],
        "description": ["বিবরণ", "বর্ণনা"],
        "image_url": ["ছবি", "ফটো"],
    },
    "Assamese": {
        "name": ["সামগ্ৰী"],
        "size": ["আকাৰ", "জোখ"],
        "colour": ["ৰং"],
        "material": ["কাপোৰ"],
        "brand": ["ব্ৰেণ্ড"],
        "category": ["প্ৰকাৰ"],
        "description": ["বিৱৰণ"],
    },
    "Manipuri": {
        "name": ["মিং", "ꯃꯤꯡ", "ꯄꯣꯠ"], "price": ["মমল", "ꯃꯃꯜ"], "colour": ["মচু", "ꯃꯆꯨ"], "size": ["ꯆꯥꯡ"],
    },
    "Santali": {"name": ["ᱧᱩᱛᱩᱢ", "ᱡᱤᱱᱤᱥ"], "price": ["ᱜᱚᱱᱚᱝ"], "colour": ["ᱨᱚᱝ"], "size": ["ᱢᱟᱯ"]},
    "Punjabi": {
        "name": ["ਨਾਮ", "ਨਾਂ", "ਵਸਤੂ", "ਉਤਪਾਦ"],
        "sku": ["ਕੋਡ"],
        "price": ["ਕੀਮਤ", "ਮੁੱਲ", "ਭਾਅ", "ਰੇਟ"],
        "size": ["ਸਾਈਜ਼", "ਆਕਾਰ", "ਮਾਪ", "ਭਾਰ"],
        "colour": ["ਰੰਗ"],
        "material": ["ਕੱਪੜਾ"],
        "brand": ["ਬ੍ਰਾਂਡ", "ਕੰਪਨੀ"],
        "category": ["ਕਿਸਮ", "ਸ਼੍ਰੇਣੀ"],
        "description": ["ਵੇਰਵਾ", "ਵਰਣਨ"],
        "image_url": ["ਫੋਟੋ", "ਤਸਵੀਰ"],
    },
    "Gujarati": {
        "name": ["નામ", "વસ્તુ", "ઉત્પાદન"],
        "sku": ["કોડ"],
        "price": ["કિંમત", "ભાવ", "દર", "એમઆરપી"],
        "size": ["સાઇઝ", "માપ", "કદ", "વજન"],
        "colour": ["રંગ"],
        "material": ["કાપડ", "મટીરિયલ"],
        "brand": ["બ્રાન્ડ", "કંપની"],
        "category": ["પ્રકાર", "વર્ગ", "શ્રેણી"],
        "description": ["વર્ણન", "વિગત"],
        "image_url": ["ફોટો", "ચિત્ર"],
    },
    "Odia": {
        "name": ["ନାମ", "ଦ୍ରବ୍ୟ", "ଉତ୍ପାଦ"],
        "sku": ["କୋଡ୍"],
        "price": ["ମୂଲ୍ୟ", "ଦାମ", "ଦର"],
        "size": ["ଆକାର", "ମାପ", "ଓଜନ"],
        "colour": ["ରଙ୍ଗ"],
        "material": ["କପଡ଼ା"],
        "brand": ["ବ୍ରାଣ୍ଡ"],
        "category": ["ପ୍ରକାର", "ବର୍ଗ"],
        "description": ["ବିବରଣୀ", "ବର୍ଣ୍ଣନା"],
        "image_url": ["ଫଟୋ", "ଚିତ୍ର"],
    },
    "Tamil": {
        "name": ["பெயர்", "பொருள்", "பொருளின் பெயர்", "பொருட்கள்", "உருப்படி"],
        "sku": ["குறியீடு", "கோட்"],
        "price": ["விலை", "எம்ஆர்பி", "விற்பனை விலை"],
        "size": ["அளவு", "எடை", "சைஸ்"],
        "colour": ["நிறம்", "கலர்"],
        "material": ["துணி", "மூலப்பொருள்"],
        "brand": ["பிராண்ட்", "நிறுவனம்"],
        "category": ["வகை", "பிரிவு"],
        "description": ["விவரம்", "விளக்கம்"],
        "image_url": ["படம்", "புகைப்படம்"],
    },
    "Telugu": {
        "name": ["పేరు", "వస్తువు", "ఉత్పత్తి"],
        "sku": ["కోడ్"],
        "price": ["ధర", "రేటు", "ఎంఆర్‌పి"],
        "size": ["సైజు", "పరిమాణం", "కొలత", "బరువు"],
        "colour": ["రంగు"],
        "material": ["బట్ట", "పదార్థం"],
        "brand": ["బ్రాండ్", "కంపెనీ"],
        "category": ["రకం", "వర్గం"],
        "description": ["వివరణ", "వివరాలు"],
        "image_url": ["ఫోటో", "చిత్రం"],
    },
    "Kannada": {
        "name": ["ಹೆಸರು", "ವಸ್ತು", "ಉತ್ಪನ್ನ"],
        "sku": ["ಕೋಡ್"],
        "price": ["ಬೆಲೆ", "ದರ", "ಎಂಆರ್‌ಪಿ"],
        "size": ["ಗಾತ್ರ", "ಅಳತೆ", "ಸೈಜ್", "ತೂಕ"],
        "colour": ["ಬಣ್ಣ"],
        "material": ["ಬಟ್ಟೆ", "ಸಾಮಗ್ರಿ"],
        "brand": ["ಬ್ರ್ಯಾಂಡ್", "ಕಂಪನಿ"],
        "category": ["ವರ್ಗ", "ವಿಧ", "ಪ್ರಕಾರ"],
        "description": ["ವಿವರಣೆ", "ವಿವರ"],
        "image_url": ["ಫೋಟೋ", "ಚಿತ್ರ"],
    },
    "Malayalam": {
        "name": ["പേര്", "ഉൽപ്പന്നം", "ഉത്പന്നം", "സാധനം", "ഇനം"],
        "sku": ["കോഡ്"],
        "price": ["വില", "നിരക്ക്", "എംആർപി"],
        "size": ["വലിപ്പം", "വലുപ്പം", "അളവ്", "സൈസ്", "തൂക്കം", "ഭാരം"],
        "colour": ["നിറം"],
        "material": ["തുണി", "മെറ്റീരിയൽ"],
        "brand": ["ബ്രാൻഡ്", "കമ്പനി"],
        "category": ["വിഭാഗം", "തരം"],
        "description": ["വിവരണം", "വിശദാംശങ്ങൾ"],
        "image_url": ["ഫോട്ടോ", "ചിത്രം"],
    },
    "Urdu, Kashmiri and Sindhi": {
        "name": ["نام", "نالو", "ناو", "پروڈکٹ", "اشیاء", "چیز"],
        "sku": ["کوڈ"],
        "price": ["قیمت", "دام", "نرخ", "ریٹ"],
        "size": ["سائز", "ناپ", "وزن"],
        "colour": ["رنگ"],
        "material": ["کپڑا", "مٹیریل"],
        "brand": ["برانڈ", "کمپنی"],
        "category": ["قسم", "زمرہ"],
        "description": ["تفصیل", "وضاحت"],
        "image_url": ["تصویر", "فوٹو"],
    },
    "In English letters": {
        "name": ["naam", "naam vastu"],
        "price": ["keemat", "kimat", "kimmat", "daam", "vilai", "dhara", "bele"],
        "colour": ["rang"],
        "description": ["vivaran"],
    },
}

# Headings that contain a field's word but hold something else: tax codes and rates, serial numbers, addresses.
NOT_PRODUCT_INFO = [
    "hsn", "sac", "hs code", "gst", "gstin", "cgst", "sgst", "igst", "tax", "vat", "pin code", "pincode",
    "एचएसएन", "जीएसटी", "कर",
]

_NUKTAS = "़়਼઼଼಼"
_ARABIC_FORMS = str.maketrans({"ي": "ی", "ى": "ی", "ك": "ک"})


def normalise(text: str) -> str:
    """Lower-case words of any script separated by single spaces, with typing variations removed."""
    text = unicodedata.normalize("NFKC", text).casefold().translate(_ARABIC_FORMS)
    kept = []
    for ch in unicodedata.normalize("NFD", text):
        category = unicodedata.category(ch)
        if ch in _NUKTAS or category == "Cf":
            continue  # nuktas and zero-width joiners are typed inconsistently
        kept.append(ch if category[0] in "LMN" else " ")
    return " ".join(unicodedata.normalize("NFC", "".join(kept)).split())


SYNONYMS: dict[str, ItemField] = {
    normalise(word): field for table in (ENGLISH, *INDIAN.values()) for field, words in table.items() for word in words
}
_LONGEST_FIRST = sorted(SYNONYMS.items(), key=lambda kv: len(kv[0]), reverse=True)
_NEVER = [normalise(word) for word in NOT_PRODUCT_INFO]


def field_for(heading: str) -> ItemField | None:
    norm = normalise(heading)
    if not norm:
        return None
    padded = f" {norm} "
    if any(f" {word} " in padded for word in _NEVER):
        return None
    if norm in SYNONYMS:
        return SYNONYMS[norm]
    return next((field for word, field in _LONGEST_FIRST if f" {word} " in padded), None)
