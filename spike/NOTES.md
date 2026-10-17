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
