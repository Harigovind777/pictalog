# Pictalog — design

Date: 2026-10-17. Status: approved in chat ("ok this one is good do this", "ok total its ok now start building").
Items marked *(Claude's call)* were not discussed with the user and can be changed.

## Intent

Companies keep their product catalog as spreadsheets and documents with no product photos. Pictalog takes whatever
catalog file a company has, turns it into a clean, shareable product catalog, and gives every product — and every
size/colour variant — a realistic AI-generated photo.

The user wants it free to run now and "paid later", so the image AI runs on the user's own Mac today and must be
swappable for a paid image API later without changing the app.

## Goals

1. **Accounts.** A company signs up with email + password and only ever sees its own catalogs.
2. **Any catalog file.** Excel (.xlsx/.xls/.xlsm/.ods), CSV/TSV, JSON, Word (.docx), PDF (text and tables),
   plain text, and scans/photos of printed catalog pages (.png/.jpg/.heic, scanned PDFs).
3. **Automatic understanding.** The app finds the product name, price, size, colour, category, description, SKU,
   material, brand and image-link fields even when headings are worded differently, or when the document is free
   text. The user always sees a **check screen** to fix the mapping/extracted rows before images are made.
4. **One image per variant.** Every row (each size, colour, …) gets its own image. Size and colour go into the image
   description so a 500 ml bottle and a 2 L bottle differ. Variants of one product share a seed so they look like
   the same product.
5. **Realistic images.** Clean studio product photo on a plain background, generated locally with Z-Image Turbo via
   Ollama.
6. **"If not available, leave it."** If a row has too little detail for a believable photo (e.g. only a code, no
   name/description), its image slot stays empty with a "Not enough detail" note. The user can upload a photo or
   force a generation. Any image can be regenerated. If the sheet already provides an image link, that image is used
   instead of generating one.
7. **Updates.** Uploading a newer version of a catalog shows what's new / changed / removed, then applies it. Only
   new or visually-changed products get new images (a price change does not regenerate).
8. **Output.** Searchable catalog page with category filter and variant switcher, a public share link (no login
   needed to view; can be turned off), and a PDF download.
9. **Everywhere.** Web (browser), desktop (macOS, Windows), Android and iOS — one shared UI.
10. **Hosted online** on a free tier, with the user's Mac as the "image helper".

## Non-goals (for now)

- Training our own image model (we plug in an existing one).
- Paid image APIs (designed for, not built).
- Publishing to the App Store / Play Store (needs paid developer accounts). Apps run in simulators/emulators and on
  the user's own devices.
- Team members / roles inside a company account *(Claude's call)*.
- Pictures embedded inside Excel/Word/PDF cells being matched to rows *(Claude's call)*.

## Anti-goals

- Fake-looking or wrong images. An empty slot is better than a misleading photo.
- A company seeing another company's data.
- Losing a user's manual edits or uploaded photos when they upload a newer sheet.

## Architecture (agreed with user)

```
 Web / Desktop (Electron) / Android + iOS (Capacitor)   ← one React app
                     │  HTTPS, bearer token
                     ▼
            Pictalog server (FastAPI)  ── database + file storage
                     ▲
                     │  outbound polling, worker token
            Image helper on the user's Mac (Python)
              └─ Ollama: Z-Image Turbo (images), local LLM (messy docs), glm-ocr (scans)
```

- The **server** does logins, uploads, instant parsing of tidy files, catalog storage, sharing, PDF export and a job
  queue. It never needs a GPU.
- The **image helper** runs on the Mac, pulls queued jobs (generate image, read messy document), runs them through
  Ollama, and uploads results. Outbound connections only — nothing on the Mac is exposed to the internet.
- **Catch (accepted by user):** while free, images and messy-document reading only happen while the Mac is on and
  the helper is running. Jobs wait in the queue otherwise. The UI shows "Image helper: online / last seen …".
- **Paid later:** the image engine and document-reader are interfaces; a paid API implementation can run either in the
  helper or directly on the server.

## Technical decisions *(Claude's call unless noted)*

- **Server:** Python 3.12, FastAPI, SQLAlchemy 2 + Alembic. SQLite + local disk when running locally; Postgres +
  S3-compatible storage online. Same code, chosen by config.
- **Hosting target:** Render free web service (server + built web UI) and Supabase free tier (Postgres + Storage).
  Exact provider confirmed with the user at deploy time — it needs their accounts.
- **Auth:** email + password (argon2 hashes), bearer tokens (works the same in browser, Electron and mobile
  WebViews; avoids cross-origin cookie problems in Capacitor).
- **UI:** React + TypeScript + Vite + Tailwind + shadcn/ui. Built once, used by all clients. API base URL is
  configurable per client.
- **Desktop:** Electron wrapping the built UI (no extra system installs; Rust/Tauri not needed).
- **Mobile:** Capacitor wrapping the built UI. File picker and camera upload for photographing printed catalogs;
  native share sheet for share links and PDFs.
- **Parsing (server, instant):** pandas/openpyxl for spreadsheets, python-docx tables, pdfplumber tables. A file is
  "tidy" if a table with a recognisable header row is found.
- **Parsing (helper, AI):** free-text Word/PDF/TXT and anything without a usable table → local instruction LLM via
  Ollama returning JSON product rows (model chosen by testing on the M4; start with a ~4–8B Qwen instruct model).
  Scans and photos → glm-ocr (already installed) → same LLM step.
- **Column mapping:** synonym table first (e.g. price ← MRP, rate, cost, unit price), unknown columns kept as extra
  attributes shown on the product.
- **Variant splitting:** a size/colour cell holding a list ("S, M, L", "Red/Blue") becomes one variant per value.
- **"Not enough detail" rule:** generate only when there is a real product name or description (not just an
  SKU-like code).
- **Images:** prompt built from a template (name, brand, colour, material, size, category, description + studio
  photo wording). Stored as WebP with thumbnails. Default size chosen by measuring speed/quality on the M4
  (target ≤ ~45 s per image).
- **Update matching:** by SKU when present, otherwise by normalised name + variant attributes.
- **PDF:** generated on the server with ReportLab (pure Python, works on free hosts).
- **Small details:** a company has many catalogs and can delete them; the company name (from sign-up) and an
  optional logo head the catalog and PDF; prices are kept exactly as written plus a parsed number when possible,
  with a per-catalog currency symbol; uploads are capped at 25 MB; no password-reset email yet (needs an email
  service — later).
- **Project location:** `~/Developer/Pictalog` — not `~/Documents`, which is iCloud-synced and breaks builds and
  code signing on this Mac.

## Build order

1. Spike: confirm Ollama image generation API, speed and realism on the M4.
2. Server + web UI working locally end to end (login → upload → check → catalog → images via local helper → share →
   PDF).
3. Desktop (Electron), Android and iOS shells on the same UI, run in simulators/emulators.
4. Put the server online (needs the user's hosting accounts).

## Environment facts

- Mac: Apple M4, 16 GB RAM, ~120 GB free. Python 3.12 + uv, Node 26, Ollama 0.18.2 (has `qwen2.5-coder`, `glm-ocr`).
- iOS needs Xcode from the App Store (user installing). Android SDK + emulator + JDK 21 installed via Homebrew.
- git identity: Harigovind777 / hmk94302@gmail.com.
