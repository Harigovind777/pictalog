# Pictalog

Turn any product list — a spreadsheet, CSV, Word file, PDF, or a photo of a printed price list — into a clean,
shareable catalog with a realistic photo for every product and every size or colour.

- **Server** (`pictalog/`): accounts, uploads, reading tidy files, catalogs, share links, PDF export, and a job queue.
- **Image helper** (`pictalog_helper/`): runs on a Mac with Ollama. It takes jobs from the server, makes product photos
  with a local image model (FLUX.2 Klein by default), and reads messy documents and scans with local AI.
- **App** (`web/`): React app used in the browser, and later wrapped for desktop, Android and iOS.

While it's free, images are only made while the Mac with the helper is on. Uploads wait in a queue otherwise.

## Run it on this Mac

Needs [uv](https://docs.astral.sh/uv/), Node 20+, and Homebrew's `ollama` (with `mlx-c`, which it pulls in).

```bash
uv sync
npm --prefix web install
ollama pull x/flux2-klein:4b   # product photos
ollama pull qwen3:4b           # reading free-text documents
ollama pull glm-ocr            # reading photos and scans
./scripts/dev.sh               # server, app and image helper; open http://localhost:5173
```

`scripts/dev.sh` starts its own Ollama on port 11435 with `OLLAMA_LIBRARY_PATH=/opt/homebrew/lib`. Without that
setting Homebrew's Ollama can't load image models (`libmlxc.dylib not found`).

Try it with the files in `samples/` (rebuild them with `uv run python scripts/make_samples.py`).

## Settings

Server (`PICTALOG_…`): `DATABASE_URL`, `STORAGE_DIR`, `SECRET_KEY`, `WORKER_TOKEN`, `MAX_UPLOAD_MB` (25).

Image helper (`PICTALOG_HELPER_…`): `SERVER_URL`, `WORKER_TOKEN`, `OLLAMA_URL`, `IMAGE_MODEL`, `WIDTH`/`HEIGHT` (768),
`STEPS` (2 is about twice as fast with little visible difference), `TEXT_MODEL`, `OCR_MODEL`.

## Tests

```bash
uv run pytest            # server and helper
npm --prefix web test    # app logic
node web/e2e/flow.mjs /tmp/shots samples/apparel.xlsx   # click through the real app (needs dev.sh running)
```

Design: `docs/superpowers/specs/2026-10-17-pictalog-design.md`. Notes from testing the AI models: `spike/NOTES.md`.
