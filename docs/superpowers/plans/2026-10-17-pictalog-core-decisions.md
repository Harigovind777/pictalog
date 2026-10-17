# Pictalog core — decisions made during the build

Calls made while building the core plan (`2026-10-17-pictalog-core.md`), each with what it costs if wrong.

## Rulings

- **Setup:** work on branch `core` in place instead of a git worktree — brand-new repo, main holds only docs — cost if wrong: none, branch can be moved.
- **Task 1 (spike finding):** letter and bare-number sizes are left out of image prompts, and the studio wording asks for no added text, letters or numbers — "size M" printed an M on the shirt — cost if wrong: sizes like "Size 10" that do change how a product looks are dropped.
- **Setup:** run Task 1 (spike) after Task 2 — model downloads still in progress; Task 2 doesn't depend on the spike — cost if wrong: none.
- **Task 2:** signup helper is a fixture returning a function (not an importable helper) — keeps conftest un-imported — cost if wrong: none
- **Task 3:** added pictalog/api/deps.py (read_upload with 25 MB cap, store_image) not named in plan — shared by logo, imports and variant photo uploads — cost if wrong: none
- **Task 4:** decode_text() lives in parsing/cells.py beside clean_cell (shared by csv, text and AI-text paths); extract_text also returns text for csv/json — gives the AI reader something when no header is found — cost if wrong: none
- **Task 5:** plan's `Field` literal is named `ItemField` (in schemas.py) — avoids clashing with pydantic.Field — cost if wrong: one rename.
- **Task 5:** find_table renames blank/duplicate headers ("Column 4", "Price (2)") — mapping is keyed by header text, duplicates would overwrite each other — cost if wrong: none.
- **Task 6:** Variant.row_hash added; "changed" = row_hash differs — product-level fields are shared by variants, so comparing against them would flag rows forever — cost if wrong: none.
- **Task 6:** Job gets variant_id/import_id columns (payload still carries them for the helper) — lets cancel/lookup work without JSON queries on SQLite/Postgres — cost if wrong: none.
- **Task 6:** Diff gains removed_names; repeated identical rows get match_key suffix "#2"… — each row stays its own variant, re-upload of the same file is "unchanged" — cost if wrong: duplicate rows that reorder could swap images.
- **Task 6:** description-only rows use the description as the prompt subject (not repeated) — reads naturally — cost if wrong: none.
- **Task 7:** unreadable/corrupt files → 400 with a friendly message, empty documents → 400 "no products" (not an Import row with status failed) — user gets the answer immediately — cost if wrong: none; `failed` status is still used by the AI path.
- **Task 7:** spreadsheets/CSV/JSON with no recognisable header go to the AI as "a | b | c" text lines — otherwise such files would be rejected — cost if wrong: none.
- **Task 7:** mapping PUT merges a partial mapping, rejects unknown headers and a field used twice (422) — keeps one column per field — cost if wrong: none.
- **Task 8:** helper_status() lives in jobs.py, image saving shared via images.save_image(storage, data) — one place for WebP conversion — cost if wrong: none.
- **Task 8:** a fail/stale requeue sets the variant back to "queued"; completing a new image deletes the previous generated files — keeps UI honest and storage small — cost if wrong: none.
- **Task 8:** an extract job returning zero items marks the import failed ("couldn't find any products") — otherwise the check screen would be empty — cost if wrong: none.
- **Task 9:** bundle DejaVu Sans (free licence, pictalog/fonts) for the PDF — ReportLab's built-in fonts can't draw ₹ — cost if wrong: ~1.5 MB in repo; Indian scripts (Devanagari/Malayalam) still won't render in PDFs (deferred).
- **Task 9:** PDF fetches only http(s) image URLs from sheets; private-network blocking deferred to the deploy plan (SSRF guard needed before going online) — cost if wrong: SSRF risk once hosted.
- **Task 9:** non-ASCII catalog names get an RFC 5987 filename* in Content-Disposition — plain header can't carry them — cost if wrong: none.
- **Task 11:** one AuthPage component with mode login|signup instead of separate Login/Signup files — same layout, half the code — cost if wrong: none.
- **Task 11:** router is hash-based when VITE_ROUTER=hash (for the Electron shell loading file://), browser router otherwise — cost if wrong: none.
- **Task 11:** light theme only (studio-sweep palette, Schibsted Grotesk, amber = AI working) — product photos on white read best on a light backdrop — cost if wrong: dark-mode users get a light app.
- **Task 12:** VariantSwitcher is inline in ProductCard and search/filter/grid live in a shared CatalogBrowser (reused by the public page) — fewer files, one grid — cost if wrong: none.
- **Task 12:** added isWorking/priceLabel/variantLabel to lib/catalog.ts with tests; share link uses VITE_PUBLIC_URL (apps run on a local origin) — cost if wrong: none.
- **Task 13:** added hasEnoughDetail() to web/src/lib/items.ts mirroring the server rule, to mark rows on the check screen — cost if wrong: the dot could disagree with the server if one rule changes alone.
- **Task 13:** the check screen shows the first 150 rows with "Show all" — very long sheets stay responsive — cost if wrong: none.
- **Task 10:** CachingEngine reuses a picture for an identical (prompt, seed) — sizes S/M/L of one product share both, so one image instead of several — cost if wrong: none (regenerate bumps the seed).
- **Task 10:** added POST /api/worker/heartbeat + a helper heartbeat thread every 10 s — an image takes ~35–60 s, longer than the 30 s "online" window — cost if wrong: none.
- **Task 10:** text model default qwen3:4b (not 8b) — leaves memory for the image model on 16 GB — cost if wrong: weaker reading of messy documents; configurable.
- **Task 10:** test fakes live in tests/helper/fakes.py, not conftest — two conftest modules can't both be imported by name — cost if wrong: none.
- **Task 14:** helper rewrites each product into a plain-English visual description (qwen3) before generating — non-English names produced wrong objects (teapot → bottle) — cost if wrong: a few seconds per product, falls back to the original prompt.
- **Task 14:** browser verification uses Playwright headless (web/e2e) — claude-in-chrome/built-in browser tools aren't available in this session — cost if wrong: none.
- **Final:** default SECRET_KEY/WORKER_TOKEN, no login rate limit, PDF fetching image URLs from sheets (SSRF) — fine on a local Mac, must be fixed in the deploy plan before going online — cost if wrong: security exposure once hosted.

## Deferred (minor)

- web bundle > 500 kB — code-split routes later.
- CatalogOut lazy-loads products/variants (N+1 queries) — slow for very large catalogs on Postgres.
- replaced/uploaded image files and uploaded catalog files are never deleted from storage.
- PDF font has no Devanagari/Malayalam glyphs.
- local image model weak spots (two-handled mugs, cardamom pods) — paid model later; "Make a new image"/"Upload photo" meanwhile.
- web bundle > 500 kB.
