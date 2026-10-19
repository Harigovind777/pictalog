# Pictalog

Turn any product list — a spreadsheet, CSV, Word file, PDF, or a photo of a printed price list — into a clean,
shareable catalog with a realistic photo for every product and every size or colour.

- **Server** (`pictalog/`): accounts, uploads, reading tidy files, catalogs, share links, PDF export, and a job queue.
- **Image helper** (`pictalog_helper/`): runs on a Mac with Ollama. It takes jobs from the server, makes product photos
  with a local image model (FLUX.2 Klein by default), and reads messy documents and scans with local AI.
- **App** (`web/`): React app used in the browser, and later wrapped for desktop, Android and iOS.

While it's free, images are only made while the Mac with the helper is on. Uploads wait in a queue otherwise.

## Run it on this Mac

Needs [uv](https://docs.astral.sh/uv/), Node 20+, and Tesseract with its language packs, which reads photos of price
lists in India's scripts: `brew install tesseract tesseract-lang`.

```bash
uv sync
npm --prefix web install
./scripts/install-ollama.sh    # Ollama 0.32.5 and the models: FLUX.2 Klein (photos), Qwen 3.5 4B (reading)
./scripts/dev.sh               # server, app and image helper; open http://localhost:5173
```

`scripts/dev.sh` starts its own Ollama, the 0.32.5 that `install-ollama.sh` puts in `~/.local/share/pictalog`, on port
11435. Later Ollama releases can't make images ("image generation models are not currently supported"), so don't
point Pictalog at Homebrew's or the Ollama app's copy, which update themselves.

This folder sits in iCloud-synced Documents. The Python environment, `web/node_modules` and the app's `data` (database,
photos, uploads) live in `.venv.nosync`, `web/node_modules.nosync` and `data.nosync`, which iCloud doesn't sync; `.venv`,
`web/node_modules` and `data` are links to them. On a fresh clone: `UV_PROJECT_ENVIRONMENT=.venv.nosync uv sync &&
ln -s .venv.nosync .venv`, and the same pattern for the other two if the clone is inside iCloud.

Try it with the files in `samples/` (rebuild them with `uv run python scripts/make_samples.py`).

## India's languages

A product list can be in English or any of India's languages, and the catalog keeps the shop's words in their own
script; only the description given to the photo model is English.

- **Spreadsheets, CSV and Word tables** are read without AI in every script: column names in each language
  (`pictalog/parsing/headings.py`), prices in any Indian digits, Excel's "Unicode Text" files.
- **Typed lists and scans** are read on the Mac by Qwen 3.5. For photos and scans it looks at the page itself, with
  Tesseract's spelling of the words as a hint (`pictalog_helper/reader.py` says why). Each row it returns is then
  tidied: a colour given as the size, a price repeated on the name and the like are put right
  (`pictalog_helper/tidy.py`).
- **Santali (Ol Chiki) and Manipuri (Meetei Mayek)** work in spreadsheets and, less reliably, in typed lists. No local
  model reads those scripts from a photo yet.
- PDFs whose Indian-script text doesn't survive extraction are read as pictures. The app and the PDF export draw every
  script with Noto fonts.

`samples/languages/` has the same four products in 16 languages as a spreadsheet, a typed list and a photo.
`uv run python scripts/eval_languages.py` scores how accurately each is read (needs `dev.sh`'s Ollama running);
results and the models tried are in `spike/NOTES.md`, decisions in `docs/superpowers/specs/2026-10-18-indian-languages.md`.

## Run it as an iPhone app (Xcode)

The iOS app (`web/ios/`, made with Capacitor) is the same app inside a native shell. With `./scripts/dev.sh` running:

```bash
npm --prefix web run ios       # build the app and copy it into the Xcode project (run again after changes)
open web/ios/App/App.xcodeproj  # in Xcode, pick the iPhone simulator and press Run
```

The app reaches the server at `http://localhost:8000`, which on the simulator is this Mac (`web/.env.ios`). A real
iPhone needs the server's network or hosted address there instead. Use the iOS 27.0 simulators (iPhone 17 and others);
the iOS 27.1 runtime on this Mac only runs the iPhone Duo.

## Settings

Server (`PICTALOG_…`): `DATABASE_URL`, `STORAGE_DIR`, `SECRET_KEY`, `WORKER_TOKEN`, `MAX_UPLOAD_MB` (25).

Image helper (`PICTALOG_HELPER_…`): `SERVER_URL`, `WORKER_TOKEN`, `OLLAMA_URL`, `IMAGE_MODEL`, `WIDTH`/`HEIGHT` (768),
`STEPS` (2 is about twice as fast with little visible difference), `TEXT_MODEL` (`qwen3.5:4b`), `VISION` (on: the text
model reads photos and scans itself), `TESSERACT` (on, when installed), `OCR_MODEL` (only with `VISION` off).

## Tests

```bash
uv run pytest            # server and helper
npm --prefix web test    # app logic
node web/e2e/flow.mjs /tmp/shots samples/apparel.xlsx   # click through the real app (needs dev.sh running)
```

Design: `docs/superpowers/specs/2026-10-17-pictalog-design.md`. Notes from testing the AI models: `spike/NOTES.md`.

The look is black and white, with colour kept for the product photos alone: photos sit on grey studio paper and
develop from black-and-white into colour as they come into view (tokens in `web/src/index.css`). The app speaks in
Mona Sans; a catalog's own words (catalog and product names) are set in Bodoni Moda, like a printed lookbook.
Catalogs sit on a shelf of magazine-style covers; screens slide like a phone app and a cover grows into its catalog's
page (browser view transitions, `web/src/lib/page-transitions.ts`); each product's sizes and colours are photos you
swipe through (`VariantSlider`). Each screen's data loads before it slides in, and touching a cover starts loading
its catalog. Animated pieces come
from [Aceternity UI](https://ui.aceternity.com/components), added with `npx shadcn@latest add @aceternity/<name>` into
`web/src/components/ui/` and adapted there (each notes its changes). The apps open with a short intro
(`web/public/intro/`, switched on by `VITE_INTRO=on` in `web/.env.ios`; add `?intro` to any web address to preview it).
