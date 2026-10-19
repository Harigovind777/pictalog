"""Materials and colours in India's languages, for the English photo description.

A small model often gets these wrong in exactly the way that shows in a photo: पीतल (brass) becomes copper, सुती (cotton)
becomes silk, लाल (red) becomes white. So the words found in a product's name are looked up here and handed to the
model as notes ("पीतल = brass"), which it can't copy as a whole answer the way it copies an example sentence."""

import re
import unicodedata

# English → the word in Hindi/Marathi/Nepali, Bengali/Assamese, Punjabi, Gujarati, Odia, Tamil, Telugu, Kannada,
# Malayalam and Urdu, with common spellings. Inflected forms are found by their start (पितळेचा, of brass → पितळ).
WORDS: dict[str, list[str]] = {
    "brass": ["पीतल", "पितळ", "पित्तल", "পিতল", "ਪਿੱਤਲ", "પિત્તળ", "ପିତ୍ତଳ", "பித்தளை", "ఇత్తడి", "ಹಿತ್ತಾಳೆ", "പിച്ചള", "پیتل"],
    "copper": ["तांबा", "तांबे", "तांब्या", "তামা", "ਤਾਂਬਾ", "તાંબા", "ତମ୍ବା", "செம்பு", "రాగి", "ತಾಮ್ರ", "ചെമ്പ്", "تانبا", "تانبے"],
    "bell metal": ["कांसा", "काँसा", "কাঁসা", "ਕਾਂਸੀ", "કાંસા", "କଂସା", "வெண்கல", "కంచు", "ಕಂಚು", "ഓട്ടു", "کانسی"],
    "stainless steel": [
        "स्टील", "स्टिल", "স্টিল", "ষ্টীল", "ਸਟੀਲ", "સ્ટીલ", "ଷ୍ଟିଲ", "ஸ்டீல்", "எவர்சில்வர்", "స్టీల్", "ಸ್ಟೀಲ್",
        "സ്റ്റീൽ", "اسٹیل", "سٹیل",
    ],
    "iron": ["लोहा", "लोखंड", "লোহা", "ਲੋਹਾ", "લોખંડ", "ଲୁହା", "இரும்பு", "ఇనుము", "ಕಬ್ಬಿಣ", "ഇരുമ്പ്", "لوہا", "لوہے"],
    "silver": ["चांदी", "चाँदी", "রুপো", "রূপা", "ਚਾਂਦੀ", "ચાંદી", "ରୁପା", "வெள்ளி", "వెండి", "ಬೆಳ್ಳಿ", "വെള്ളി", "چاندی"],
    "gold": ["सोना", "सोने", "সোনা", "ਸੋਨਾ", "સોના", "ସୁନା", "தங்க", "బంగారు", "ಚಿನ್ನ", "സ്വർണ", "سونا", "سونے"],
    "clay": ["मिट्टी", "माती", "মাটি", "ਮਿੱਟੀ", "માટી", "ମାଟି", "களிமண்", "మట్టి", "ಮಣ್ಣಿನ", "കളിമൺ", "مٹی"],
    "wood": ["लकड़ी", "लाकडी", "কাঠ", "ਲੱਕੜ", "લાકડા", "କାଠ", "மர", "చెక్క", "ಮರದ", "മരം", "لکڑی"],
    "glass": ["काँच", "कांच", "কাচ", "ਕੱਚ", "કાચ", "କାଚ", "கண்ணாடி", "గాజు", "ಗಾಜು", "ചില്ല്", "کانچ", "شیشہ"],
    "cotton": [
        "सूती", "सुती", "कपास", "সুতি", "সুতী", "কপাহী", "ਸੂਤੀ", "સુતરાઉ", "સુતરની", "ସୂତା", "ସୂତି", "பருத்தி", "నూలు",
        "ಹತ್ತಿ", "പരുത്തി", "سوتی",
    ],
    "silk": ["रेशम", "रेशमी", "रेशीम", "রেশম", "ਰੇਸ਼ਮ", "રેશમ", "ରେଶମ", "பட்டு", "పట్టు", "ರೇಷ್ಮೆ", "പട്ടു", "ریشم", "ریشمی"],
    "wool": ["ऊन", "ऊनी", "উলের", "ਉੱਨ", "ਊਨੀ", "ઊન", "ପଶମ", "கம்பளி", "ఉన్ని", "ಉಣ್ಣೆ", "കമ്പിളി", "اون", "اونی"],
    "jute": ["जूट", "পাট", "ਜੂਟ", "શણ", "ଝୋଟ", "சணல்", "జనపనార", "ಸೆಣಬು", "ചണം", "پٹسن"],
    "leather": ["चमड़ा", "चमड़े", "चामडी", "চামড়া", "ਚਮੜਾ", "ਚਮੜੇ", "ચામડા", "ଚମଡ଼ା", "தோல்", "తోలు", "ಚರ್ಮ", "തുകൽ", "چمڑا", "چمڑے"],
    "red": ["लाल", "रातो", "লাল", "ৰঙা", "ਲਾਲ", "લાલ", "ନାଲି", "சிவப்பு", "ఎరుపు", "ఎర్ర", "ಕೆಂಪು", "ചുവപ്പ്", "ചുവന്ന", "سرخ", "لال"],
    "blue": ["नीला", "नीले", "निळा", "निलो", "নীল", "ਨੀਲਾ", "વાદળી", "ନୀଳ", "நீல", "నీలం", "ನೀಲಿ", "നീല", "نیلا", "نیلے"],
    "green": ["हरा", "हरे", "हिरवा", "हरियो", "সবুজ", "সেউজীয়া", "ਹਰਾ", "લીલો", "લીલા", "ସବୁଜ", "பச்சை", "ఆకుపచ్చ", "ಹಸಿರು", "പച്ച", "ہرا"],
    "yellow": ["पीला", "पीले", "पिवळा", "पहेंलो", "হলুদ", "হালধীয়া", "ਪੀਲਾ", "પીળો", "પીળા", "ହଳଦିଆ", "மஞ்சள்", "పసుపు", "ಹಳದಿ", "മഞ്ഞ", "پیلا"],
    "white": ["सफ़ेद", "सफेद", "पांढरा", "सेतो", "সাদা", "বগা", "ਚਿੱਟਾ", "સફેદ", "ଧଳା", "வெள்ளை", "తెలుపు", "తెల్ల", "ಬಿಳಿ", "വെള്ള", "سفید"],
    "black": ["काला", "काले", "काळा", "कालो", "কালো", "ক'লা", "ਕਾਲਾ", "કાળો", "કાળા", "କଳା", "கருப்பு", "నలుపు", "నల్ల", "ಕಪ್ಪು", "കറുപ്പ്", "کالا", "سیاہ"],
    "pink": ["गुलाबी", "গোলাপী", "ਗੁਲਾਬੀ", "ગુલાબી", "ଗୋଲାପୀ", "இளஞ்சிவப்பு", "గులాబీ", "ಗುಲಾಬಿ", "റോസ്", "گلابی"],
    "orange": ["नारंगी", "केसरी", "भगवा", "কমলা", "ਸੰਤਰੀ", "કેસરી", "નારંગી", "ନାରଙ୍ଗୀ", "ஆரஞ்சு", "కాషాయ", "ಕೇಸರಿ", "ഓറഞ്ച്", "نارنجی"],
    "purple": ["बैंगनी", "जांभळा", "বেগুনি", "ਜਾਮਨੀ", "જાંબલી", "ବାଇଗଣି", "ஊதா", "ఊదా", "ನೇರಳೆ", "വയലറ്റ്", "جامنی", "بنفشی"],
    "brown": ["भूरा", "भूरे", "तपकिरी", "खैरो", "খয়েরি", "বাদামী", "ਭੂਰਾ", "ભૂરો", "பழுப்பு", "గోధుమ", "ಕಂದು", "തവിട്ട്", "بھورا"],
    "grey": ["स्लेटी", "धूसर", "खरानी", "ছাই", "ধূসৰ", "ਸਲੇਟੀ", "રાખોડી", "ଧୂସର", "சாம்பல்", "బూడిద", "ಬೂದು", "ചാര", "سرمئی", "خاکستری"],
    "golden": ["सुनहरा", "सुनहरी", "सोनेरी", "সোনালী", "ਸੁਨਹਿਰੀ", "સોનેરી", "ସୁନେଲି", "பொன்னிற", "സ്വർണനിറ", "سنہرا", "سنہری"],
    "maroon": ["मैरून", "कत्थई", "মেরুন", "ਮਹਿਰੂਨ", "મરૂન", "ମରୁନ", "மெரூன்", "మెరూన్", "ಮರೂನ್", "മെറൂൺ", "عنابی"],
}

COLOURS = {
    "red", "blue", "green", "yellow", "white", "black", "pink", "orange", "purple", "brown", "grey", "golden", "maroon",
}

_INVISIBLE = dict.fromkeys(map(ord, "​‌‍़়਼઼଼಼"))


def normalise(text: str) -> str:
    """Without nuktas or zero-width joiners, which people type or leave out, and in lower case."""
    return unicodedata.normalize("NFC", unicodedata.normalize("NFD", text).translate(_INVISIBLE)).casefold()


_ENTRIES = sorted(
    ((normalise(w), w, english) for english, words in WORDS.items() for w in words), key=lambda e: -len(e[0])
)
_WHOLE = {key: english for key, _, english in _ENTRIES}


def _lookup(token: str) -> tuple[str, str] | None:
    """The glossary word a token is, or starts with, and its English. Short words must match whole (চা isn't চাকি);
    longer ones may carry an ending (पितळेचा, স্টিলের, ಸ್ಟೀಲ್ನ)."""
    word = normalise(token)
    if not word or word.isascii():
        return None  # English words need no note
    for key, written, english in _ENTRIES:
        if word == key or (len(key) >= 3 and word.startswith(key)):
            return written, english
    return None


def _tokens(text: str) -> list[str]:
    return [t for t in re.split(r"[\s,.;:!?()\[\]/|—–-]+", text) if t]


def notes(text: str) -> list[str]:
    """"word = meaning" for each material or colour in the text."""
    found: dict[str, str] = {}
    for token in _tokens(text):
        if hit := _lookup(token):
            found.setdefault(token, hit[1])
    return [f"{word} = {english}" for word, english in found.items()]


def colour(word: str) -> str | None:
    """The English name of the colour `word` is, written in one of the languages here or in English, else None."""
    key = normalise(word.strip())
    english = key if key in COLOURS else _WHOLE.get(key)
    return english if english in COLOURS else None


def material(word: str) -> str | None:
    """The English for a material word here, which may carry an ending (पितळेचा → brass), else None."""
    hit = _lookup(word)
    return hit[1] if hit and hit[1] not in COLOURS else None


def native(text: str, english: str) -> str | None:
    """The word in `text` that means `english`, as the glossary spells it (Steel → स्टील in "स्टीलची बाटली")."""
    wanted = set(english.lower().split())
    for token in _tokens(text):
        hit = _lookup(token)
        if hit and wanted <= set(hit[1].split()):
            return hit[0]
    return None
