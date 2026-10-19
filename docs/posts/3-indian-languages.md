---
title: Reading price lists in 15 Indian languages with a 4B model on a laptop
subtitle: What I measured, what broke, and why Tesseract and an LLM work better together than apart
tags: ai, nlp, ocr, llm, python
images:
  - samples/languages/tamil-pricelist.jpg  # the Tamil test price list
---

A shop in Chennai may well keep its price list in Tamil. One in Cuttack, in Odia; in Guwahati, Assamese; in
Ludhiana, Punjabi. If Pictalog is going to turn a shop's list into a catalog, it has to read that list in the shop's own language and
script, and keep the shop's words exactly as they wrote them.

And it has to do it on a 16 GB laptop, with models small enough to sit next to an image model (part 2 explains that
budget).

Here's how I measured it, and what moved the numbers.

## A test set before any prompt tweaking

Small models are fragile, so I wanted a number before changing anything. A script generates the same four
products (a red cotton saree, a 1-litre steel bottle, 250 g of tea and a brass lamp) in **16 languages** (English and 15 of India's), in four
formats:

- a spreadsheet
- a typed list
- a photo of a printed price list
- a photo of a ruled table

![A test price list in Tamil: a shop name, four products with prices in rupees, and a delivery line with a phone number.](samples/languages/tamil-pricelist.jpg)

Each language has 11 fields to get right (names, prices, sizes, colours), so **176 per format**. One command scores
everything. To be clear, these are generated test documents, not photos from real shops, so treat the numbers below as a best
case for real phone photos.

## Spreadsheets: no AI needed

The first surprise: spreadsheets in Indian languages weren't recognised as tables *at all*. The code only knew English
column names.

The fix was a dictionary, not a model. It holds column names in every language (and Indian-English bill words like
"Particulars", "Rs." and "Net Wt"), plus prices in any Indian digits: `₹ १,२९९`, `৳ ২৫০`, `۱۵۰ روپے`.

**Result: 176/176.** If a format has structure, use it before you reach for an LLM.

## Indian scripts cost 2–4× the tokens

Typed lists go to the language model, and the first thing that broke was the **context window**.

Tokenizers are trained mostly on English. Text in Indian scripts takes two to four times as many tokens per
character as English. A 6,000-character chunk of Odia came to about **9,700 tokens**, far past the 4,096-token window
I'd set. The model was silently reading only part of the list.

The fixes were plain arithmetic:

- If more than 30% of the letters aren't plain English letters, chunks are **2,000 characters** instead of 6,000.
- The context window went to **8,192 tokens**.
- Output is capped at **4,096 tokens**. The old model once generated 9,000 tokens on a single Hindi list, repeating
  itself, and could loop for 5–8 minutes on a page.

## Picking the model: 42% → 90%

| Model | Typed lists, fields right |
|---|---|
| `qwen3:4b-instruct` | ≈42% (first 6 languages) |
| `qwen3.5:4b` | 159/176 (90%) |
| `gemma4:e4b` | Returned only the first product, and too big to sit next to the image model |

The old model copied names into the product-code field, merged sizes into names and dropped prices. Qwen 3.5 mostly
didn't.

Then I tried to *help* it. I gave each field a longer, more careful description in the instructions. Accuracy dropped
from 90% to **53%**: prices started landing in the description field. I reverted it, and now nobody changes the
reading instructions without running the test set first.

## Photos: two readers that are wrong in opposite ways

Photos of printed lists were the hard part. I tried five setups:

| How the photo is read | Fields right |
|---|---|
| OCR model (glm-ocr) → Qwen 3.5 | 71/176 (40%) |
| Qwen 3.5 looks at the photo itself | 120/176 (68%) |
| Tesseract OCR → Qwen 3.5 | 125/176 (71%) |
| Qwen 3.5 looks at the photo + Tesseract's text as a hint | 140/176 (80%) |
| Same, but **Tesseract's numbers removed from the hint** | **86%** (first 8 languages) |

The last row came from noticing that the two readers fail in **opposite** ways:

- **Tesseract** spells Tamil, Kannada, Gujarati and Odia words exactly. But it reads the rupee sign `₹` as `२`, `2`,
  `3`, `4`, `%` or `*`, so `₹1,450` came out as `२1,450` and `₹899` as `*899`.
- **Qwen 3.5** reads every price and size right from the image. But it garbles words in those same scripts.

With Tesseract's full text as a hint, the model trusted the hint and copied its wrong prices. So now the hint keeps
Tesseract's **words** and blanks out its **numbers**, and the model reads the numbers from the image itself.

A few Tesseract details that cost me time:

- Its automatic script detection needs more text than a price list has, and it called Santali "Latin". Now every
  script's data is tried, and the most confident reading wins.
- Ruled tables need sparse mode (`--psm 11`). Line mode garbles them.
- It ends words with a zero-width non-joiner and writes some Malayalam letters the old way (ണ്‍ for ൺ). Both are
  cleaned up afterwards.

## The last mile: rules, not prompts

The remaining mistakes were the same in every language: a colour given as the size, the price repeated on the end
of the name, a size without its number. Instead of more prompt wording (see the 53% above), a small **tidy** step
fixes these with rules. It compares the fields with each other and with the text that was read, and it never adds a
word that isn't there.

I also made the scoring stricter: a name only counts if it has no extra words, and a colour only counts in the colour
field. Under that stricter scoring:

| All 16 languages | As read | Tidied |
|---|---|---|
| Typed list | 151/176 (86%) | **168/176 (95%)** |
| Photo of a printed list | 129/176 (73%) | **152/176 (86%)** |
| Photo of a ruled table | 139/176 (79%) | **142/176 (81%)** |

No language scored lower. Leaving out the two scripts covered in the next section, photos are at **94%** and typed
lists at **99%**.

On the five languages I measured first (English, Hindi, Marathi, Nepali, Bengali), reading a photo went from
**9% to 93%**. Each page takes about 40 seconds on the laptop.

## Where it doesn't work: Santali and Manipuri

Two of India's scripts, **Ol Chiki** (Santali) and **Meetei Mayek** (Manipuri), can't be read from a photo by any
local model I tried:

- Gemma 4 wrote Odia and Devanagari letters instead.
- glm-ocr wrote Kannada and Myanmar.
- Tesseract has no data for either script.

Spreadsheets in these scripts work, and typed lists partly work. Photos don't. If you know of an open OCR model that
reads Ol Chiki or Meetei Mayek, I'd love to hear about it.

## Takeaways

1. **Build the test set first.** One instruction change took accuracy from 90% to 53%, and I'd never have noticed
   without it.
2. **Budget tokens per script, not per character.** Indian scripts take 2–4× the tokens.
3. **Combine tools that fail differently.** Tesseract's words plus the LLM's numbers beat either one alone.
4. **Fix recurring slips with rules, not prompts.** Rules are testable and don't make other things worse.
5. **Say where it fails.** Two scripts still have no local model that reads them from a photo.

---

*Part 3 of a series on building Pictalog. Part 1: "I asked for a size M T-shirt. The AI printed an M on it." Part 2:
"A product-photo studio on a 16 GB MacBook."*
