# Pictalog — India's languages and reading accuracy

Date: 2026-10-18. Asked for in chat: "focus on the accuracy which our app has … every database will not be in english
so i need all indian languages which we can setup locally should be there". Everything below was Claude's call,
measured with `scripts/eval_languages.py` (numbers in `spike/NOTES.md`).

## What "supported" means

A shop's list can be in English or any of India's languages, and the catalog keeps the shop's own words in their own
script. Only the photo prompt is English (the image model only understands English).

| Script | Languages | Spreadsheet / CSV / Word table | Typed list | Photo or scan |
|---|---|---|---|---|
| Latin | English, Hindi or Tamil typed in English letters | yes | yes | yes |
| Devanagari | Hindi, Marathi, Nepali, Konkani, Maithili, Dogri, Bodo, Sanskrit | yes | yes | yes |
| Bengali–Assamese | Bengali, Assamese, Manipuri in Bengali script | yes | yes | yes |
| Gurmukhi, Gujarati, Odia | Punjabi, Gujarati, Odia | yes | yes | yes |
| Tamil, Telugu, Kannada, Malayalam | the four Dravidian languages | yes | yes | yes |
| Perso-Arabic | Urdu, Kashmiri, Sindhi | yes | yes | yes |
| Ol Chiki, Meetei Mayek | Santali, Manipuri | yes | partly | no: no local model reads these scripts from a picture |

## Decisions

- **Headings** (`pictalog/parsing/headings.py`): column names in every language above, plus Indian-English bill words
  (Particulars, Rs., Net Wt) and Hindi in English letters (Naam, Keemat). Compared after removing typing variations
  (nukta or not, zero-width joiners, Arabic or Persian letter forms). Tax columns (HSN, GST, Tax Rate) are never a
  field: an HSN code taken as a product code merged different products, and "GST Rate" was taken as the price.
- **Numbers and files:** prices in any Indian digits (₹ १,२९९, ৳ ২৫০, ۱۵۰ روپے); Excel's UTF-16 "Unicode Text"
  exports, read as tables; the Urdu comma splits variants.
- **PDFs whose Indian text doesn't survive extraction** (joined letters come out as nothing or private characters,
  vowel signs in drawing order) are read as pictures instead. Chrome's and ReportLab's PDFs both do this.
- **Reading model: Qwen 3.5 4B** (`qwen3.5:4b`, 3.3 GB), replacing qwen3:4b-instruct, which copied names into the
  code field, dropped prices and looped on Indian text until it timed out. Gemma 4 E4B returned only the first product
  and is 6.6 GB, too big to sit beside the 5.7 GB photo model (the helper alternates between them for every photo).
- **Photos and scans:** Tesseract (`brew install tesseract-lang`) spells words in Indian scripts exactly but reads ₹ as
  2, 3, 4 or %; Qwen 3.5 reads every number right but garbles Tamil, Kannada, Gujarati or Odia words. So Qwen 3.5
  looks at the page itself, with Tesseract's words as a hint and their numbers blanked out (`vision`). Tesseract reads
  each page with every script's data and keeps the reading it's clearly most sure of; when none is (Ol Chiki, Meetei
  Mayek), Qwen reads alone.
- **Tidying each row** (`pictalog_helper/tidy.py`, 2026-10-19): the model's slips are the same in every language: the
  colour given as the size or left on the name, the size or price repeated on the name, a size without its number, a
  material word taken off the front of the name, a material or colour in English. Rules put the words back by
  comparing the fields with each other and with the text read (OCR's words for a photo); they never add a word that
  isn't there. The eval now counts these as wrong (a name with words added, a colour outside the colour field).
- **Model limits:** an 8K context and a 4K output cap on reading (the old model generated 9 000 tokens on one Hindi
  list), smaller chunks for Indian scripts (two to four times the tokens per character of English), and a 120-token
  cap on photo descriptions.
- **Ollama 0.32.5, pinned** (`scripts/install-ollama.sh`): later releases dropped image generation, and Qwen 3.5 needs
  a release newer than the 0.18 that was installed.
- **Showing the words:** Noto Sans and Noto Serif for every script in the app (each downloads only when a page shows
  its letters) and in PDFs, where HarfBuzz joins the letters and Urdu runs right to left. Catalog headlines in these
  scripts get normal letter spacing and room for vowel signs (`textProps`, `web/src/lib/script.ts`).

## Not done

- The app's own words (buttons, labels) are English only; this is about the shops' data.
- Pages mixing two Indian scripts: Tesseract picks one script per page, so the hint is wrong for the other; the model
  still reads that part from the image.
- Legacy-font text (Kruti Dev and similar, typed as Latin letters drawn as Devanagari) isn't converted.
