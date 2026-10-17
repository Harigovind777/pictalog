# More accurate AI models — options (researched 2026-10-18, not yet tested)

What goes wrong today (see `NOTES.md`): FLUX.2 Klein 4B at 2 steps draws the wrong thing when it doesn't know a product
(green cardamom → green beans), adds parts (a mug with two handles), and smudges small printed text. The Mac gives
the GPU about 11.3 GB of its 16 GB, which rules out the bigger models.

## Free, on this Mac

| Option | Download | Fits 11.3 GB? | Licence | What it should fix |
|---|---|---|---|---|
| Klein 4B at **4 steps** (it is trained for 4; we use 2 for speed) | none | yes | Apache 2.0 | general detail and shape errors; ~+15–20 s per photo |
| **`x/flux2-klein:4b-fp8`** — the same model, less compressed than our 5.7 GB fp4 | 9.5 GB | probably (test) | Apache 2.0 | finer detail, fewer mangled shapes |
| **Check and retry** with a vision model, `qwen3-vl:4b` | 3.3 GB | yes (runs between photos) | Apache 2.0 | wrong objects: ask "is this a green cardamom pod, with one handle…?"; if not, try another seed (up to 2), then mark the product "needs your photo" instead of showing a wrong picture |
| `qwen3-vl:4b` for **reading price-list photos** directly (DocVQA ≈ 95) | same model | yes | Apache 2.0 | could replace the two-step glm-ocr → qwen3 reading with one step; test against `samples/pricelist.jpg` |

Not possible here: Klein **9B** (12 GB, and its licence is **non-commercial** — unusable once Pictalog is paid),
Z-Image Turbo (13 GB, already failed to load), Qwen-Image (20 B).

## Paid, for the "paid later" tier (per 1024² image; third-party price lists from Aug–Sep 2026, check before use)

| Service | ≈ price | Note |
|---|---|---|
| FLUX.2 [klein] 4B, hosted | $0.003 | the same model as now, no Mac needed |
| Seedream 5 Lite | $0.008 | cheap, good realism |
| FLUX.2 [pro] | $0.03 | first megapixel; +$0.015 per extra MP |
| Nano Banana 2 (Gemini Flash Image) | $0.035–0.067 | strong prompt-following; can work from a reference photo |
| GPT Image 2 | $0.03–0.21 | prices vary most |

A 1,000-variant catalog at $0.03 is about $30. Several of these accept a reference photo, which would allow
"upload one real photo, get studio shots of every colour".

## Suggested next step (≈ 1 hour, needs your go-ahead for ~13 GB of downloads)

1. Take 20 products from `samples/` including the known failures (cardamom, mug, teapot, tee with size M).
2. Make each with: today's setup · 4 steps · fp8 at 4 steps. Note seconds per photo and which ones are right.
3. Run the `qwen3-vl:4b` check over all of them and see whether it catches the wrong ones without flagging good ones.
4. Pick the combination; it is a settings change in the image helper (`PICTALOG_HELPER_IMAGE_MODEL`, `STEPS`) plus,
   for the check, a small step in `pictalog_helper/run.py`.

Sources: [Ollama flux2-klein tags](https://ollama.com/x/flux2-klein/tags) ·
[Ollama z-image-turbo tags](https://ollama.com/x/z-image-turbo/tags) ·
[Klein 4B vs 9B test](https://wiro.ai/blog/flux-2-klein-base-4b-vs-9b-5-prompt-image-test/) ·
[Klein 9B licence note](https://vercel.com/ai-gateway/models/flux-2-klein-9b) ·
[Qwen3-VL 4B vs 8B](https://codersera.com/blog/qwen3-vl-4b-vs-qwen3-vl-8b-benchmarks-vram-guide/) ·
[Local image models on a 16 GB Mac](https://localaimaster.com/blog/local-image-generation-mac) ·
[API prices (aireiter)](https://aireiter.com/blog/cheapest-image-generation-api) ·
[API prices (pixo)](https://pixo.video/blog/ai-image-generation-pricing)
