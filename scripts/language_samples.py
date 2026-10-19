"""The same four products, written the way a shop in each part of India would write them.

Used by scripts/make_samples.py (files to try in the app) and scripts/eval_languages.py (accuracy check). Each product
also lists English words a correct photo description must contain."""

from dataclasses import dataclass, field


@dataclass
class Product:
    name: str
    price: int
    price_text: str
    colour: str | None = None
    material: str | None = None
    size: str | None = None
    english: list[list[str]] = field(default_factory=list)  # each inner list: one of these words must appear


@dataclass
class Language:
    name: str
    code: str  # ISO 639
    font: str  # Noto font in pictalog/fonts/noto, "" for the Latin font
    shop: str
    headers: list[str]  # name, colour, size, price
    products: list[Product]
    footer: str = ""


SAREE = [["saree", "sari"], ["red"], ["cotton"]]
BOTTLE = [["bottle", "flask"], ["steel", "stainless", "metal"]]
TEA = [["tea", "chai"]]
LAMP = [["lamp", "diya"], ["brass", "bronze", "bell metal", "golden", "gold"]]

LANGUAGES = [
    Language("English", "en", "", "Lakshmi Stores — price list", ["Item", "Colour", "Size", "Price"], [
        Product("Cotton Saree", 1450, "₹1,450", colour="Red", english=SAREE),
        Product("Steel Water Bottle", 350, "₹350", size="1 L", english=BOTTLE),
        Product("Tea Powder", 120, "₹120", size="250 g", english=TEA),
        Product("Brass Diya", 899, "₹899", english=LAMP),
    ], "Free home delivery. Call 98470 00000."),
    Language("Hindi", "hi", "NotoSansDevanagari", "लक्ष्मी स्टोर्स — मूल्य सूची", ["वस्तु", "रंग", "साइज़", "दाम"], [
        Product("सूती साड़ी", 1450, "₹1,450", colour="लाल", english=SAREE),
        Product("स्टील की पानी की बोतल", 350, "₹350", size="1 लीटर", english=BOTTLE),
        Product("चाय पत्ती", 120, "₹ १२०", size="250 ग्राम", english=TEA),
        Product("पीतल का दीया", 899, "₹899", english=LAMP),
    ], "घर पर मुफ़्त डिलीवरी। फ़ोन: 98470 00000"),
    Language("Marathi", "mr", "NotoSansDevanagari", "लक्ष्मी स्टोअर्स — दरपत्रक", ["वस्तू", "रंग", "आकार", "किंमत"], [
        Product("सुती साडी", 1450, "₹1,450", colour="लाल", english=SAREE),
        Product("स्टीलची पाण्याची बाटली", 350, "₹350", size="1 लिटर", english=BOTTLE),
        Product("चहा पावडर", 120, "₹120", size="250 ग्रॅम", english=TEA),
        Product("पितळेचा दिवा", 899, "₹899", english=LAMP),
    ], "घरपोच मोफत डिलिव्हरी. फोन: 98470 00000"),
    Language("Nepali", "ne", "NotoSansDevanagari", "लक्ष्मी स्टोर्स — मूल्य सूची", ["सामान", "रङ", "आकार", "मूल्य"], [
        Product("सुती साडी", 1450, "रु. 1,450", colour="रातो", english=SAREE),
        Product("स्टिलको पानीको बोतल", 350, "रु. 350", size="1 लिटर", english=BOTTLE),
        Product("चियापत्ती", 120, "रु. 120", size="250 ग्राम", english=TEA),
        Product("पित्तलको दियो", 899, "रु. 899", english=LAMP),
    ]),
    Language("Bengali", "bn", "NotoSansBengali", "লক্ষ্মী স্টোর্স — মূল্য তালিকা", ["পণ্য", "রং", "মাপ", "দাম"], [
        Product("সুতির শাড়ি", 1450, "₹১,৪৫০", colour="লাল", english=SAREE),
        Product("স্টিলের জলের বোতল", 350, "₹৩৫০", size="১ লিটার", english=BOTTLE),
        Product("চা পাতা", 120, "₹১২০", size="২৫০ গ্রাম", english=TEA),
        Product("পিতলের প্রদীপ", 899, "₹৮৯৯", english=LAMP),
    ], "বিনামূল্যে হোম ডেলিভারি। ফোন: 98470 00000"),
    Language("Assamese", "as", "NotoSansBengali", "লক্ষ্মী ষ্ট'ৰ্চ — মূল্য তালিকা", ["সামগ্ৰী", "ৰং", "আকাৰ", "দাম"], [
        Product("কপাহী শাড়ী", 1450, "₹১,৪৫০", colour="ৰঙা", english=SAREE),
        Product("ষ্টীলৰ পানীৰ বটল", 350, "₹৩৫০", size="১ লিটাৰ", english=BOTTLE),
        Product("চাহপাত", 120, "₹১২০", size="২৫০ গ্ৰাম", english=TEA),
        Product("পিতলৰ চাকি", 899, "₹৮৯৯", english=LAMP),
    ]),
    Language("Punjabi", "pa", "NotoSansGurmukhi", "ਲਕਸ਼ਮੀ ਸਟੋਰ — ਕੀਮਤ ਸੂਚੀ", ["ਵਸਤੂ", "ਰੰਗ", "ਸਾਈਜ਼", "ਕੀਮਤ"], [
        Product("ਸੂਤੀ ਸਾੜੀ", 1450, "₹1,450", colour="ਲਾਲ", english=SAREE),
        Product("ਸਟੀਲ ਦੀ ਪਾਣੀ ਦੀ ਬੋਤਲ", 350, "₹350", size="1 ਲੀਟਰ", english=BOTTLE),
        Product("ਚਾਹ ਪੱਤੀ", 120, "₹120", size="250 ਗ੍ਰਾਮ", english=TEA),
        Product("ਪਿੱਤਲ ਦਾ ਦੀਵਾ", 899, "₹899", english=LAMP),
    ]),
    Language("Gujarati", "gu", "NotoSansGujarati", "લક્ષ્મી સ્ટોર્સ — ભાવ પત્રક", ["વસ્તુ", "રંગ", "માપ", "કિંમત"], [
        Product("સુતરાઉ સાડી", 1450, "₹1,450", colour="લાલ", english=SAREE),
        Product("સ્ટીલની પાણીની બોટલ", 350, "₹350", size="1 લિટર", english=BOTTLE),
        Product("ચાની પત્તી", 120, "₹120", size="250 ગ્રામ", english=TEA),
        Product("પિત્તળનો દીવો", 899, "₹899", english=LAMP),
    ]),
    Language("Odia", "or", "NotoSansOriya", "ଲକ୍ଷ୍ମୀ ଷ୍ଟୋର୍ସ — ମୂଲ୍ୟ ତାଲିକା", ["ଦ୍ରବ୍ୟ", "ରଙ୍ଗ", "ଆକାର", "ମୂଲ୍ୟ"], [
        Product("ସୂତା ଶାଢ଼ୀ", 1450, "₹1,450", colour="ନାଲି", english=SAREE),
        Product("ଷ୍ଟିଲ ପାଣି ବୋତଲ", 350, "₹350", size="1 ଲିଟର", english=BOTTLE),
        Product("ଚା ପତ୍ର", 120, "₹120", size="250 ଗ୍ରାମ", english=TEA),
        Product("ପିତ୍ତଳ ଦୀପ", 899, "₹899", english=LAMP),
    ]),
    Language("Tamil", "ta", "NotoSansTamil", "லட்சுமி ஸ்டோர்ஸ் — விலைப் பட்டியல்", ["பொருள்", "நிறம்", "அளவு", "விலை"], [
        Product("பருத்திப் புடவை", 1450, "₹1,450", colour="சிவப்பு", english=SAREE),
        Product("எவர்சில்வர் தண்ணீர் பாட்டில்", 350, "₹350", size="1 லிட்டர்", english=BOTTLE),
        Product("டீ தூள்", 120, "ரூ. 120", size="250 கிராம்", english=TEA),
        Product("பித்தளை விளக்கு", 899, "₹899", english=LAMP),
    ], "இலவச வீட்டு டெலிவரி. தொலைபேசி: 98470 00000"),
    Language("Telugu", "te", "NotoSansTelugu", "లక్ష్మి స్టోర్స్ — ధరల పట్టిక", ["వస్తువు", "రంగు", "సైజు", "ధర"], [
        Product("నూలు చీర", 1450, "₹1,450", colour="ఎరుపు", english=SAREE),
        Product("స్టీల్ నీళ్ల బాటిల్", 350, "₹350", size="1 లీటర్", english=BOTTLE),
        Product("టీ పొడి", 120, "₹120", size="250 గ్రాములు", english=TEA),
        Product("ఇత్తడి దీపం", 899, "₹899", english=LAMP),
    ]),
    Language("Kannada", "kn", "NotoSansKannada", "ಲಕ್ಷ್ಮಿ ಸ್ಟೋರ್ಸ್ — ಬೆಲೆ ಪಟ್ಟಿ", ["ವಸ್ತು", "ಬಣ್ಣ", "ಗಾತ್ರ", "ಬೆಲೆ"], [
        Product("ಹತ್ತಿ ಸೀರೆ", 1450, "₹1,450", colour="ಕೆಂಪು", english=SAREE),
        Product("ಸ್ಟೀಲ್ ನೀರಿನ ಬಾಟಲಿ", 350, "₹350", size="1 ಲೀಟರ್", english=BOTTLE),
        Product("ಟೀ ಪುಡಿ", 120, "₹120", size="250 ಗ್ರಾಂ", english=TEA),
        Product("ಹಿತ್ತಾಳೆ ದೀಪ", 899, "₹899", english=LAMP),
    ]),
    Language("Malayalam", "ml", "NotoSansMalayalam", "ലക്ഷ്മി സ്റ്റോഴ്സ് — വിലവിവരപ്പട്ടിക", ["സാധനം", "നിറം", "അളവ്", "വില"], [
        Product("കോട്ടൺ സാരി", 1450, "₹1,450", colour="ചുവപ്പ്", english=SAREE),
        Product("സ്റ്റീൽ വെള്ളക്കുപ്പി", 350, "₹350", size="1 ലിറ്റർ", english=BOTTLE),
        Product("തേയിലപ്പൊടി", 120, "₹120", size="250 ഗ്രാം", english=TEA),
        Product("പിച്ചള വിളക്ക്", 899, "₹899", english=LAMP),
    ], "സൗജന്യ ഹോം ഡെലിവറി. ഫോൺ: 98470 00000"),
    Language("Urdu", "ur", "NotoSansArabic", "لکشمی اسٹورز — قیمتوں کی فہرست", ["چیز", "رنگ", "سائز", "قیمت"], [
        Product("سوتی ساڑھی", 1450, "1,450 روپے", colour="سرخ", english=SAREE),
        Product("اسٹیل کی پانی کی بوتل", 350, "350 روپے", size="1 لیٹر", english=BOTTLE),
        Product("چائے کی پتی", 120, "۱۲۰ روپے", size="250 گرام", english=TEA),
        Product("پیتل کا دیا", 899, "899 روپے", english=LAMP),
    ]),
    Language("Santali", "sat", "NotoSansOlChiki", "ᱞᱚᱠᱥᱢᱤ ᱫᱚᱠᱟᱱ", ["ᱡᱤᱱᱤᱥ", "ᱨᱚᱝ", "ᱢᱟᱯ", "ᱜᱚᱱᱚᱝ"], [
        Product("ᱥᱟᱲᱤ", 1450, "₹1,450", colour="ᱟᱨᱟᱜ", english=SAREE[:1]),
        Product("ᱵᱚᱛᱚᱞ", 350, "₹350", size="1 ᱞᱤᱴᱚᱨ", english=BOTTLE[:1]),
        Product("ᱪᱟ", 120, "₹120", size="250 ᱜᱨᱟᱢ", english=TEA),
        Product("ᱫᱤᱭᱟ", 899, "₹899", english=LAMP[:1]),
    ]),
    Language("Manipuri", "mni", "NotoSansMeeteiMayek", "ꯂꯛꯁ꯭ꯃꯤ ꯁ꯭ꯇꯣꯔ", ["ꯄꯣꯠ", "ꯃꯆꯨ", "ꯆꯥꯡ", "ꯃꯃꯜ"], [
        Product("ꯁꯥꯔꯤ", 1450, "₹1,450", colour="ꯑꯉꯥꯡꯕ", english=SAREE[:1]),
        Product("ꯕꯣꯇꯜ", 350, "₹350", size="1 ꯂꯤꯇꯔ", english=BOTTLE[:1]),
        Product("ꯆꯥ", 120, "₹120", size="250 ꯒ꯭ꯔꯥꯝ", english=TEA),
        Product("ꯊꯥꯎꯃꯩ", 899, "₹899", english=LAMP[:1]),
    ]),
]


def lines(language: Language) -> list[str]:
    """A typed price list: shop name, one product per line, then the shop's details."""
    comma = "، " if language.font == "NotoSansArabic" else ", "
    out = [language.shop]
    for p in language.products:
        out.append(" — ".join(x for x in (comma.join(y for y in (p.name, p.colour) if y), p.size, p.price_text) if x))
    if language.footer:
        out.append(language.footer)
    return out


def rows(language: Language) -> list[list[str]]:
    """The same list as a spreadsheet: a title row, headings in the language, one row per product."""
    return [[language.shop], language.headers] + [
        [p.name, p.colour or "", p.size or "", p.price_text] for p in language.products
    ]
