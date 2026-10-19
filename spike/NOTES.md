# Spike notes — local AI on the M4 (16 GB)

## Ollama image generation

- Homebrew's Ollama 0.18.2 needs **`OLLAMA_LIBRARY_PATH=/opt/homebrew/lib`** when started, or image models fail with
  `libmlxc.dylib not found` (the MLX library comes from Homebrew's `mlx-c`).
- Request: `POST /api/generate` with top-level fields
  `{"model", "prompt", "stream": false, "width", "height", "seed", "steps"}`.
- Response: `{"image": "<base64 PNG>", "done": true, "total_duration": ns, "load_duration": ns, ...}`;
  failures come back as `{"error": "..."}`.
- `seed` is honoured: the same seed gives a near-identical picture (tiny GPU differences, not byte-identical).
- `steps` is honoured.

### FLUX.2 Klein 4B (`x/flux2-klein:4b`, 5.7 GB, Apache 2.0)

| size | steps | seconds |
|------|-------|---------|
| 768² | default | 49–68 |
| 768² | 2 | 34 |
| 640² | default | 50 |

Realistic studio product shots (tee, bottle, mug). Failure seen: a mug with two handles.
**"size M" in the prompt printed an M on the shirt** → prompts now leave out letter sizes and ask for no added text.

### Z-Image Turbo (`x/z-image-turbo`, 13 GB) — doesn't fit

`model requires 11.9 GiB but only 11.3 GiB are available`: macOS lets the GPU use ~75% of 16 GB. Removed.
**Chosen: FLUX.2 Klein 4B, 768², 2 steps (~30 s per image).**

Weak spots seen: mugs with two handles; green cardamom pods drawn like green beans (the model doesn't know them).

## Text

- `qwen3:4b` is the *thinking* build: with `think: false` it still writes ~400 tokens of reasoning (~75 s). Use
  **`qwen3:4b-instruct`**: ~1 s for a product rewrite.
- Free-text Word file (4 products): 15 s, prices right. It invented product codes → codes not found in the text are
  dropped; placeholder values ("not specified") are dropped.
- Photo of a printed price list: `glm-ocr` (`/api/generate`, prompt "Text Recognition:", `images: [b64]`) then the same
  extraction: 4/4 products with sizes and prices.
- Image models mostly understand English: "Théière" (teapot) became a bottle. Each product is rewritten into a
  plain-English description starting with its everyday English name before the photo is made.

## India's languages (2026-10-18)

`scripts/eval_languages.py` reads the same four products (a red cotton saree, a 1-litre steel bottle, 250 g of tea,
a brass lamp) in 16 languages from a spreadsheet, a typed list, a photo of a printed list and a photo of a ruled table,
and scores name, price, size and colour (11 fields per language, 176 in all); "rewrite" checks the English photo
description names the right thing. The documents are made by `scripts/language_samples.py` (also in
`samples/languages/`). Numbers below are from runs with nothing else on the GPU unless marked.

### Reading typed lists (text model)

| Model | Fields right | Notes |
|---|---|---|
| `qwen3:4b-instruct` (before) | ≈42% (first 6 languages) | copied the name into the code, merged sizes into names, dropped prices; looped on Punjabi and Hindi until the cap (9 000+ tokens, ~15 min before the cap existed) |
| `qwen3.5:4b` | 159/176, 90% | misses: splits the material out of the name, takes the shop for the brand, once changed a letter |
| `gemma4:e4b` (6.6 GB) | — | returned only the first product with the JSON schema; too big to sit beside FLUX anyway |

Longer field descriptions in the instructions dropped Qwen 3.5 to 53% (prices went into the description). Small models
are fragile about wording; change the reading instructions only with this check run.

Tokens per character (Ollama prompt counts): qwen3 0.6–1.1 for Indian scripts (Odia, Manipuri worst) against ~2 for
English; Gemma 4 about twice as efficient. A 6 000-character Odia chunk was ~9 700 qwen3 tokens in a 4 096 window →
chunks of 2 000 characters for these scripts, `num_ctx` 8192, `num_predict` 4096.

### Reading photos (all 16 languages, photo of a printed list)

| How | Fields right |
|---|---|
| glm-ocr → Qwen 3.5 | 71/176, 40% (glm-ocr: "लाइमी सत्तोरी" for लक्ष्मी स्टोर्स, ₹ as है) |
| Qwen 3.5 looks at the photo, no hint | 120/176, 68%: every price right; Tamil, Kannada, Gujarati, Odia words garbled or switched script |
| Tesseract → Qwen 3.5 | 125/176, 71%: words exact; ₹ read as २, 2, 3, 4, %, * |
| Qwen 3.5 + Tesseract's text as a hint | 140/176, 80%: copies the hint's misread prices |
| Qwen 3.5 + Tesseract's words, numbers left out (8 languages, also tables) | 86% photos, 83% tables |

Nothing local reads Ol Chiki (Santali) or Meetei Mayek (Manipuri) from a picture: Gemma 4 wrote Odia and Devanagari
for them, glm-ocr Kannada and Myanmar. Tesseract has no data for them.

Tesseract notes: `brew install tesseract-lang` (tessdata_fast). Its own script detection (`--psm 0`) needs more text
than a price list and called Santali "Latin", so every script's data is tried and the most confident reading wins
(sparse mode, `--psm 11`, so ruled tables score fairly; line mode garbles them). It ends words with a zero-width
non-joiner and writes Malayalam chillus the old way (ണ്‍ for ൺ); both are cleaned.

### PDFs

pdfplumber on Chrome's and ReportLab's PDFs of Indian text: joined letters come out as `\x00` or private-use
characters (स्टील → "\x00ील"), vowel signs in drawing order (புடவை → புடைவ), so headings stop matching. Such PDFs are
read as pictures.

### Photo descriptions (English, for FLUX)

`qwen3:4b-instruct` 32/64 (50%): पीतल का दीया → "copper candle", Telugu cotton saree → "red earthenware pot". Qwen 3.5
with the old instructions 38/64 (59%), and it answered "black peppercorns" — the instructions' own example — for tea
it didn't know. Any whole example sentence gets copied like that ("a small round copper water pot" for tea, Santali
and Manipuri). With no example sentences and a glossary of materials and colours passed as notes
(`pictalog_helper/glossary.py`, "पीतल = brass"): 45/64 (70%), brass right everywhere. Still wrong: diya as
"candlestick", some tea and saree words; Santali and Manipuri get invented objects.

### Ollama

0.18.2 can't pull qwen3.5 or gemma4 ("requires a newer version"); 0.40.x can't make images ("image generation models
are not currently supported", removed after 0.32.5). 0.32.5 does both and bundles its MLX library (no
`OLLAMA_LIBRARY_PATH`). `scripts/install-ollama.sh` installs it apart from Homebrew's.

### Final (2026-10-19): what ships

`qwen3.5:4b`, vision on, Tesseract on; `uv run python scripts/eval_languages.py` with nothing else on the GPU
(`spike/eval-languages/final.txt`):

| | sheet | typed list | photo | ruled table | photo description |
|---|---|---|---|---|---|
| all 16 languages | 176/176 (100%) | 159/176 (90%) | 145/176 (82%) | 139/176 (79%) | 45/64 (70%) |
| without Santali, Manipuri | 154/154 | 144/154 (94%) | 137/154 (89%) | 133/154 (86%) | 45/56 (80%) |

Before: spreadsheets in Indian languages weren't recognised as tables at all (English only). The old models
(`qwen3:4b-instruct`, glm-ocr; `spike/eval-languages/before.txt`, stopped after 5 languages because they loop on
Indian text for 5–8 minutes a page), against the final setup on the same five (English, Hindi, Marathi, Nepali,
Bengali):

| | typed list | photo | ruled table | photo description |
|---|---|---|---|---|
| before | 24/55 (44%) | 5/55 (9%) | 5/55 (9%) | 14/20 |
| after | 51/55 (93%) | 51/55 (93%) | 54/55 (98%) | 16/20 |

Seconds per page on the M4 now: typed list ~25 s, photo ~40 s, ruled table ~35 s.

### Tidying the rows (2026-10-19)

The scores above let some slips through: a name counted as right with the colour, size or price still on it
("पितळेचा दिवा — ₹899"), and a colour counted when it was only in the name. The eval now needs the name with no words
added and the colour in its own field. Under that scoring, with `pictalog_helper/tidy.py` putting the words back
(`spike/eval-languages/tidy.txt`; "as read" is `final.txt`'s readings scored the new way, the same model answers):

| | typed list | photo | ruled table |
|---|---|---|---|
| as read, all 16 | 151/176 (86%) | 129/176 (73%) | 139/176 (79%) |
| tidied, all 16 | 168/176 (95%) | 152/176 (86%) | 142/176 (81%) |
| as read, without Santali, Manipuri | 136/154 (88%) | 121/154 (79%) | 133/154 (86%) |
| tidied, without Santali, Manipuri | 153/154 (99%) | 144/154 (94%) | 136/154 (88%) |

No language scored lower. What's left is the model's reading itself: Telugu photo prices missing, Kannada and
Assamese table names garbled, a Tamil letter changed (பாட்டல் for பாட்டில்), the shop taken as the brand when the
model misspells it.
