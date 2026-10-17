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
ollama pull qwen3:4b-instruct  # reading documents, plain-English product descriptions
ollama pull glm-ocr            # reading photos and scans
./scripts/dev.sh               # server, app and image helper; open http://localhost:5173
```

`scripts/dev.sh` starts its own Ollama on port 11435 with `OLLAMA_LIBRARY_PATH=/opt/homebrew/lib`. Without that
setting Homebrew's Ollama can't load image models (`libmlxc.dylib not found`).

This folder sits in iCloud-synced Documents. The Python environment, `web/node_modules` and the app's `data` (database,
photos, uploads) live in `.venv.nosync`, `web/node_modules.nosync` and `data.nosync`, which iCloud doesn't sync; `.venv`,
`web/node_modules` and `data` are links to them. On a fresh clone: `UV_PROJECT_ENVIRONMENT=.venv.nosync uv sync &&
ln -s .venv.nosync .venv`, and the same pattern for the other two if the clone is inside iCloud.

Try it with the files in `samples/` (rebuild them with `uv run python scripts/make_samples.py`).

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
`STEPS` (2 is about twice as fast with little visible difference), `TEXT_MODEL`, `OCR_MODEL`.

## Tests

```bash
uv run pytest            # server and helper
npm --prefix web test    # app logic
node web/e2e/flow.mjs /tmp/shots samples/apparel.xlsx   # click through the real app (needs dev.sh running)
```

Design: `docs/superpowers/specs/2026-10-17-pictalog-design.md`. Notes from testing the AI models: `spike/NOTES.md`.

The look is black and white, with colour kept for the product photos alone: photos sit on grey studio paper and
develop from black-and-white into colour as they come into view (tokens in `web/src/index.css`). Animated pieces come
from [Aceternity UI](https://ui.aceternity.com/components), added with `npx shadcn@latest add @aceternity/<name>` into
`web/src/components/ui/` and adapted there (each notes its changes). The apps open with a short intro
(`web/public/intro/`, switched on by `VITE_INTRO=on` in `web/.env.ios`; add `?intro` to any web address to preview it).
