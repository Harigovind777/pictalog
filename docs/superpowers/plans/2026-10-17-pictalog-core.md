# Pictalog Core Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A working local Pictalog: sign up → upload any catalog file → check screen → catalog with realistic
per-variant images made by the Mac image helper → share link → PDF.

**Architecture:** FastAPI server (SQLite + local disk for now) with a DB-backed job queue; a separate Python image
helper polls the server and runs Ollama (image model, text LLM, glm-ocr); one React UI talks to the server with a
bearer token. Desktop/mobile shells and hosting are later plans (`…-shells.md`, `…-deploy.md`).

**Tech Stack:** Python 3.12, uv, FastAPI, SQLAlchemy 2, pydantic-settings, PyJWT, argon2-cffi, pandas, openpyxl,
xlrd, odfpy, python-docx, pdfplumber, Pillow, ReportLab, httpx, pypdfium2, pillow-heif, pytest · React 19 + TS +
Vite, Tailwind v4, shadcn/ui, react-router, @tanstack/react-query, Vitest · Ollama 0.18.2.

**Spec:** `docs/superpowers/specs/2026-10-17-pictalog-design.md`

## Global Constraints

- Repo root `~/Developer/Pictalog` (never under iCloud-synced `~/Documents`).
- Python ≥ 3.12 via `uv`; one `pyproject.toml` at repo root with packages `pictalog` (server) and `pictalog_helper`.
- Config via env vars prefixed `PICTALOG_`; dev defaults must work with zero setup.
- Uploads capped at **25 MB** (`413` above). Accepted: `.xlsx .xlsm .xls .ods .csv .tsv .json .docx .pdf .txt .md
  .png .jpg .jpeg .webp .heic`. Anything else `415` with the accepted list in the message (`.doc` → "save as .docx").
- Every catalog/import/variant endpoint returns **404** for another company's resource.
- Price changes never trigger image regeneration; uploaded photos are never replaced by an import.
- "Not enough detail" rows get no automatic image (`image_status="not_enough_detail"`).
- Images stored as WebP + 400 px thumbnail under storage keys `img/<uuid>.webp` / `img/<uuid>_t.webp`; only `img/`
  keys are publicly served.
- UI copy is plain English, no jargon ("Image helper", "Not enough detail", "Generate anyway").

## Review Focus

1. **Another company's IDs** in any URL → 404, never data. *(tests in Tasks 3, 7, 8)*
2. **Real-world messy spreadsheets:** title/logo rows above the header, blank rows, numbers read as `499.0`, several
   sheets → the header row is found, `499.0` shows as `499`, blank rows skipped. *(Tasks 4, 5)*
3. **Re-uploading an updated sheet:** price-only change keeps the image; an uploaded photo survives a visual change;
   removed rows disappear. *(Task 6)*
4. **Helper dies mid-job or is off:** a `running` job older than 10 min is requeued; after 3 attempts it is `failed`
   and the variant shows "failed"; UI says helper offline after 30 s silence. *(Task 8)*
5. **CSV from Excel in other locales:** UTF-8 with BOM, Latin-1, and `;` delimiters parse correctly. *(Task 4)*

---

## File Structure

```
pyproject.toml
pictalog/
  config.py        Settings
  db.py            engine/session, Base, get_db
  models.py        User, Catalog, Product, Variant, Import, Job, Heartbeat
  auth.py          password hashing, tokens, current_user dependency
  storage.py       Storage protocol + LocalStorage
  schemas.py       ExtractedItem + API response models
  parsing/cells.py    clean_cell()
  parsing/detect.py   file kind from filename
  parsing/tables.py   read_tables(): every tidy format → list[Table]; extract_text()
  parsing/mapping.py  synonyms, map_columns(), find_table()
  parsing/rows.py     rows_to_items(), split_variants()
  parsing/price.py    parse_price()
  catalog/detail.py   has_enough_detail()
  catalog/prompt.py   build_prompt(), seed_for()
  catalog/sync.py     match_key(), visual_hash(), diff_items(), apply_items()
  jobs.py          enqueue/claim/complete/fail/requeue_stale
  images.py        to_webp_pair()
  pdf.py           render_catalog_pdf()
  api/{auth_routes,catalogs,imports,variants,share,worker,files}.py
  main.py          create_app()
pictalog_helper/
  client.py        ServerClient
  engines.py       ImageEngine protocol, OllamaImageEngine
  reader.py        DocumentReader (OCR + LLM → items)
  run.py           main loop, `python -m pictalog_helper`
tests/server/…  tests/helper/…
spike/           throwaway scripts + NOTES.md
web/             React app (src/lib, src/pages, src/components)
scripts/dev.sh   start server + web + helper
```

---

### Task 1: Spike — image and text AI on the M4

Throwaway. Decides the image model, image size and text model. No tests.

**Files:** Create `spike/imagegen.py`, `spike/extract.py`, `spike/NOTES.md`, `spike/out/` (gitignored).

- [ ] **Step 1:** Confirm `ollama list` shows `x/flux2-klein:4b` and `x/z-image-turbo`; `ollama pull qwen3:8b`.
- [ ] **Step 2:** `spike/imagegen.py MODEL WIDTH HEIGHT`: POST `http://localhost:11434/api/generate`
  `{model, prompt, stream:false}` with width/height; print response keys (minus image data), decode the base64
  image to `spike/out/<model>-<w>-<n>.png`, print seconds. Find which request fields carry width/height/steps/seed and
  which response field carries the image.
- [ ] **Step 3:** Run 3 prompts built in the Task 6 template style (red cotton t-shirt size M; 1 L steel water bottle;
  white ceramic mug 350 ml) × both models × 768² and 1024². Note seconds/image and whether macOS swaps
  (`memory_pressure`).
- [ ] **Step 4:** `spike/extract.py`: send a messy 15-line free-text product list to `qwen3:8b` via `/api/chat` with
  `format=<JSON schema of a list of ExtractedItem>` and `think:false`; check every product comes back with correct
  fields. Send one photo of a printed price list through `glm-ocr` and print the text.
- [ ] **Step 5:** Write `spike/NOTES.md`: exact request/response shape, timings, chosen defaults. **Show the user the
  images side by side and let them pick the model.** Record their pick as `PICTALOG_HELPER_IMAGE_MODEL` default.
- [ ] **Step 6:** Commit `spike/*.py spike/NOTES.md` — `chore: spike local image and text models`.

---

### Task 2: Server skeleton and accounts

**Files:** Create `pyproject.toml`, `.gitignore`, `pictalog/{__init__,config,db,models,auth,schemas,main}.py`,
`pictalog/api/auth_routes.py`, `tests/server/conftest.py`, `tests/server/test_auth.py`.

**Interfaces — Produces:**
- `Settings(BaseSettings, env_prefix="PICTALOG_")`: `database_url="sqlite:///data/pictalog.db"`,
  `storage_dir=Path("data/files")`, `secret_key="dev-secret-change-me"`, `worker_token="dev-worker-token"`,
  `max_upload_mb=25`, `token_days=30`.
- `create_app(settings: Settings | None = None) -> FastAPI`; CORS allow all origins, no credentials; tables created
  on startup (Alembic arrives in the deploy plan).
- `get_db(request) -> Iterator[Session]`; `current_user` dependency → `User` or 401.
- Models (all ids `int`, timestamps UTC):
  - `User(email unique lowercased, password_hash, company_name, logo_key|None)`
  - `Catalog(user_id, name, currency="", share_enabled=False, share_token|None unique, created_at, updated_at)`
  - `Product(catalog_id, group_key, name, brand, category, description, position)`
  - `Variant(product_id, match_key, sku, size, colour, material, price_text, price_value: Decimal|None,
    extra: dict, image_url_source|None, image_key|None, thumb_key|None, image_source: none|generated|provided|uploaded,
    image_status: none|not_enough_detail|queued|generating|ready|failed, seed_offset=0, visual_hash, position)`
  - `Import(catalog_id, filename, file_key, kind, status: parsing|needs_ai|ready_for_review|applied|failed,
    method: table|ai|None, headers: list[str], rows: list[list[str]], mapping: dict[str, str|None],
    items: list[dict], error|None)`
  - `Job(kind: extract|image, status: queued|running|done|failed|cancelled, payload: dict, attempts=0,
    claimed_at|None, error|None, created_at)`
  - `Heartbeat(id=1, last_seen_at|None, engine|None)`
- Routes: `POST /api/auth/signup {email,password,company_name}` → `201 {token,user}` (password ≥ 8, duplicate email
  409); `POST /api/auth/login` → `{token,user}` / 401; `GET /api/auth/me`; `PATCH /api/auth/me {company_name}`.
  `UserOut = {id,email,company_name,logo_url|None}`.
- Test fixtures: `settings(tmp_path)`, `client` (TestClient), `signup(client, email) -> dict[str,str]` (auth headers).

- [ ] **Step 1: Failing tests** in `tests/server/test_auth.py`:
  - `test_signup_returns_token_and_user` — 201, `user.email == "a@x.com"` (sent as `"A@X.com"`), `token` non-empty.
  - `test_duplicate_email_409`, `test_short_password_422`.
  - `test_login_wrong_password_401`, `test_login_then_me` — `/me` with the token returns the same email.
  - `test_me_without_token_401`, `test_me_with_garbage_token_401`.
- [ ] **Step 2:** `uv sync && uv run pytest tests/server/test_auth.py` → fails (no module).
- [ ] **Step 3:** Implement. Tokens: HS256 JWT `{sub: user_id, exp}`; passwords: `argon2.PasswordHasher`.
- [ ] **Step 4:** `uv run pytest tests/server` → all pass.
- [ ] **Step 5:** Commit — `feat(server): accounts with email/password and bearer tokens`.

---

### Task 3: Catalogs, storage, public image files

**Files:** Create `pictalog/storage.py`, `pictalog/images.py`, `pictalog/api/catalogs.py`, `pictalog/api/files.py`;
modify `pictalog/main.py`, `pictalog/schemas.py`, `pictalog/api/auth_routes.py`; tests `tests/server/test_catalogs.py`,
`tests/server/test_images.py`.

**Interfaces — Produces:**
- `class Storage(Protocol)`: `save(key: str, data: bytes, content_type: str) -> None`, `read(key) -> bytes`,
  `delete(key) -> None`, `exists(key) -> bool`. `LocalStorage(root: Path)`. App holds `app.state.storage`.
- `to_webp_pair(data: bytes) -> tuple[bytes, bytes]` (full WebP q=90, thumbnail 400 px long side); raises
  `ValueError` on non-image bytes. `new_image_keys() -> tuple[str, str]` → `("img/<uuid>.webp","img/<uuid>_t.webp")`.
- `file_url(key: str|None) -> str|None` → `"/api/files/<key>"`.
- `CatalogSummary = {id,name,currency,product_count,variant_count,updated_at}`;
  `VariantOut = {id,sku,size,colour,material,price_text,price_value,extra,image_url,thumb_url,image_status,image_source}`
  (`image_url` = stored key URL, else `image_url_source`);
  `ProductOut = {id,name,brand,category,description,variants}`;
  `CatalogOut = {id,name,currency,share_enabled,share_token,products,counts: dict[image_status,int]}`.
- `get_owned_catalog(db, user, catalog_id) -> Catalog` (404 otherwise) — reused by Tasks 7–9.
- Routes: `GET/POST /api/catalogs`, `GET/PATCH/DELETE /api/catalogs/{id}`, `POST /api/auth/me/logo` (multipart),
  `GET /api/files/{key:path}` (only `img/` prefix, else 404; `Cache-Control: public, max-age=31536000`).

- [ ] **Step 1: Failing tests:**
  - `test_create_and_list_catalogs` — POST `{name:"Summer", currency:"₹"}` then GET list has one with `product_count==0`.
  - `test_other_company_gets_404` — B's GET/PATCH/DELETE on A's catalog → 404 each.
  - `test_delete_catalog_removes_it`.
  - `test_logo_upload_sets_logo_url` — `/me` `logo_url` starts with `/api/files/img/`, and GET that URL → 200 `image/webp`.
  - `test_files_rejects_non_img_keys` — `/api/files/uploads/x` → 404.
  - `test_to_webp_pair` — 1000×500 PNG → thumbnail width 400; `to_webp_pair(b"nope")` raises `ValueError`.
- [ ] **Step 2:** Run → fail. **Step 3:** Implement. **Step 4:** `uv run pytest tests/server` → pass.
- [ ] **Step 5:** Commit — `feat(server): catalogs, file storage, logo upload`.

---

### Task 4: Reading tidy files into tables

**Files:** Create `pictalog/parsing/{__init__,cells,detect,tables}.py`; tests `tests/server/parsing/test_tables.py`,
`tests/server/parsing/conftest.py` (builds fixture files in `tmp_path` with openpyxl, python-docx, ReportLab).

**Interfaces — Produces:**
- `FileKind = Literal["spreadsheet","csv","json","docx","pdf","text","image"]`;
  `detect_kind(filename: str) -> FileKind` raises `UnsupportedFile(message)` (message lists accepted types; `.doc`
  says "save it as .docx").
- `clean_cell(value: object) -> str` in `pictalog/parsing/cells.py` — None/NaN → `""`; float with integer value → no
  `.0`; datetime/date → ISO date; strip whitespace.
- `Table = list[list[str]]` (raw rows, header not yet known; every cell passed through `clean_cell`).
- `read_tables(kind: FileKind, data: bytes) -> list[Table]` — spreadsheet: every sheet (`pandas.read_excel(...,
  sheet_name=None, header=None, dtype=object)`); csv: sniff delimiter among `,;\t|`, decode `utf-8-sig` then `cp1252`
  then `latin-1`; json: a top-level list of objects, or the first list-of-objects value inside a top-level object →
  header row from the union of keys in first-seen order; docx: every table; pdf: `pdfplumber` tables per page,
  consecutive tables whose first row equals the previous table's header are merged; text/image → `[]`.
- `extract_text(kind, data) -> str` — docx paragraphs + table cells, pdf page text, text decoded; `""` for image or
  scanned PDF.

- [ ] **Step 1: Failing tests:**
  - `test_detect_kind` — `"x.XLSX"→spreadsheet`, `"a.heic"→image`; `"a.doc"` raises with `".docx"` in message;
    `"a.exe"` raises.
  - `test_xlsx_all_sheets` — 2-sheet workbook → 2 tables; cell `499.0` (float) reads as `"499"`; date cell reads
    `"2026-01-05"`.
  - `test_csv_semicolon_latin1` — `"Name;Price\nCafé crème;4,50\n".encode("latin-1")` → `[["Name","Price"],
    ["Café crème","4,50"]]`.
  - `test_csv_utf8_bom` — header first cell is `"Name"` not `"﻿Name"`.
  - `test_json_nested_list` — `{"products":[{"name":"Mug","price":5},{"name":"Cup","size":"S"}]}` → header
    `["name","price","size"]`, 3 rows total, missing cell `""`.
  - `test_docx_table_and_text` — docx with a paragraph and a 3×2 table → one table; `extract_text` contains both.
  - `test_pdf_table_merged_across_pages` — ReportLab gridded table split over 2 pages with repeated header → one
    table, header once.
- [ ] **Step 2:** Run → fail. **Step 3:** Implement. **Step 4:** Pass. **Step 5:** Commit —
  `feat(parsing): read spreadsheets, csv, json, word and pdf tables`.

---

### Task 5: Understanding columns and rows

**Files:** Create `pictalog/parsing/{mapping,rows,price}.py`, `pictalog/catalog/{__init__,detail}.py`; modify
`pictalog/schemas.py`; tests `tests/server/parsing/test_mapping.py`, `test_rows.py`, `tests/server/test_detail.py`.

**Interfaces — Produces:**
- `Field = Literal["name","sku","price","size","colour","material","brand","category","description","image_url"]`.
- `ExtractedItem(BaseModel)`: `name, sku, price_text, size, colour, material, brand, category, description,
  image_url: str|None = None`, `extra: dict[str,str] = {}`. (Shared JSON shape with the helper.)
- `FIELD_SYNONYMS: dict[Field, list[str]]` — at least: name←name, product, product name, item, item name, title,
  article, model; sku←sku, code, item code, product code, id, product id, article no, part no, barcode, ean, upc,
  style no; price←price, mrp, rate, cost, unit price, selling price, retail price, amount; size←size, sizes,
  dimension(s), volume, weight, net weight, capacity, pack size; colour←colour(s), color(s), shade, finish;
  material←material, fabric, composition; brand←brand, make, manufacturer; category←category, type, department,
  collection, group, product type, sub category; description←description, details, desc, features, specification,
  specs, notes; image_url←image, image url, image link, photo, picture, img, thumbnail.
- `map_columns(headers: list[str]) -> dict[str, Field|None]` — normalise (lowercase, non-alphanumerics → space,
  collapse); exact synonym match first, else longest synonym contained as whole words; each field assigned to the
  first header only.
- `TableMatch(headers: list[str], rows: list[list[str]], mapping)`; `find_table(tables) -> TableMatch|None` — scan
  the first 10 rows of each table for the row with the most mapped fields; needs ≥ 2 mapped fields including `name`
  or `description`; best-scoring table wins; data rows = rows after it, fully blank rows dropped.
- `parse_price(text: str) -> Decimal|None` — first number; `"₹1,299.00"→1299.00`, `"4,50 €"→4.50`,
  `"$12"→12`, `"on request"→None`.
- `rows_to_items(match: TableMatch) -> list[ExtractedItem]` — unmapped non-empty cells → `extra[header]`; then
  `split_variants`.
- `split_variants(item) -> list[ExtractedItem]` — split `size`/`colour` on `, / ; |` except a separator with digits on
  both sides (regex `\s*(?:(?<!\d)[,/;|]|[,/;|](?!\d))\s*`); both lists → every combination.
- `has_enough_detail(item) -> bool` — name equal to sku counts as no name; true iff name or description has a
  whitespace-separated token with no digits and ≥ 3 letters.

- [ ] **Step 1: Failing tests:**
  - `test_map_columns_synonyms` — `["Item Code","Product Name","MRP (₹)","Colour","Remarks"]` →
    `{sku, name, price, colour, None}`.
  - `test_map_columns_first_wins` — `["Price","Cost"]` → `{"Price":"price","Cost":None}`.
  - `test_find_table_skips_title_rows` — rows `[["ACME Pvt Ltd Catalogue 2026"],[""],["Name","Price","Size"],
    ["Mug","199","350 ml"],["","",""]]` → headers `["Name","Price","Size"]`, 1 data row.
  - `test_find_table_none_when_no_header` — `[["hello","world"]]` → `None`.
  - `test_rows_to_items_extra_and_split` — row `Name=Tee, Size="S, M, L", Colour="Red/Blue", Fit=Slim` → 6 items,
    each `extra=={"Fit":"Slim"}`.
  - `test_split_keeps_numbers` — size `"1,000 ml"` → 1 item; size `"6, 8"` → 2.
  - `test_parse_price` — the four cases above.
  - `test_has_enough_detail` — `"Cotton T-Shirt"`→True, `"SKU-10023"`→False, name None + description
    `"Blue ceramic mug"`→True, name `"A1234"`→False, name == sku `"MUG"`→False.
- [ ] **Step 2:** Run → fail. **Step 3:** Implement. **Step 4:** Pass. **Step 5:** Commit —
  `feat(parsing): column mapping, row extraction, variant splitting`.

---

### Task 6: Image prompts and catalog sync (new / changed / removed)

**Files:** Create `pictalog/catalog/{prompt,sync}.py`, `pictalog/jobs.py` (enqueue only here); tests
`tests/server/test_prompt.py`, `tests/server/test_sync.py`.

**Interfaces — Consumes:** models (Task 2), `ExtractedItem`, `has_enough_detail` (Task 5).
**Produces:**
- `build_prompt(product: Product, variant: Variant) -> str` — `"Professional studio product photograph of {name}"`
  + `" by {brand}"`, `" in {colour}"`, `" made of {material}"`, `", size {size}"`, `" ({category})"`,
  `". {description[:300]}"` when present, then `". Single product, centered, isolated on a seamless plain white
  background, soft even studio lighting, sharp focus, high detail, true-to-life colours, photorealistic e-commerce
  photo, no watermark."`
- `seed_for(group_key: str, offset: int) -> int` — `int(sha256(group_key).hexdigest()[:8], 16) + offset`.
- `group_key(item) -> str` — normalised `brand|name` (name falls back to description's first 60 chars).
- `match_key(item) -> str` — `"sku:"+norm(sku)` else `"nv:"+norm(name)|norm(size)|norm(colour)|norm(material)`.
- `visual_hash(item) -> str` — sha1 of name, brand, category, description, size, colour, material, image_url
  (not price, not extra).
- `Diff(new: list[ExtractedItem], changed: list[tuple[int, ExtractedItem, bool]], removed: list[int],
  unchanged: int)` — `changed` tuples are `(variant_id, item, visual_changed)`; `Diff.summary() -> dict` with counts and
  up to 20 names per list (for the UI).
- `diff_items(db, catalog, items) -> Diff`; `apply_items(db, catalog, items) -> Diff` — new → product (by group_key)
  + variant; image: `image_url` → `image_source="provided", image_status="ready"`; else enough detail → queue image
  job; else `not_enough_detail`. Changed → update fields; if visual changed and `image_source=="generated"` →
  requeue; `uploaded` stays. Removed → delete variant, then empty products. Positions follow file order.
- `enqueue_image(db, variant) -> Job` — cancels the variant's queued/running image jobs, sets
  `image_status="queued"`, payload `{variant_id, prompt, seed}`.

- [ ] **Step 1: Failing tests:**
  - `test_build_prompt_full` and `test_build_prompt_name_only` — exact strings.
  - `test_seed_shared_by_variants` — same group_key → same seed; offset 1 → seed+1.
  - `test_apply_new_items_queue_images` — 3 items (one SKU-only) → 2 variants `queued` with 2 queued jobs, 1
    `not_enough_detail`; items `Tee S`/`Tee M` share one product.
  - `test_apply_provided_image_url` — no job, `image_status=="ready"`.
  - `test_price_only_change_keeps_image` — reapply with new price → `price_value` updated, no new job.
  - `test_visual_change_requeues_generated_but_not_uploaded` — colour change: generated variant gets a new job;
    `image_source="uploaded"` variant keeps its `image_key` and no job.
  - `test_removed_rows_deleted` — reapply without one product → its variants and product gone; diff `removed` has it.
  - `test_match_by_sku_survives_rename` — same SKU, new name → `changed` not `new`+`removed`.
- [ ] **Step 2:** Run → fail. **Step 3:** Implement. **Step 4:** Pass. **Step 5:** Commit —
  `feat(catalog): image prompts and catalog sync`.

---

### Task 7: Import API (upload → check screen → apply)

**Files:** Create `pictalog/api/imports.py`; modify `pictalog/main.py`; test `tests/server/test_imports.py`.

**Interfaces — Consumes:** `detect_kind`, `read_tables`, `extract_text` (Task 4), `find_table`, `rows_to_items`,
`map_columns` (Task 5), `diff_items`, `apply_items` (Task 6), `get_owned_catalog` (Task 3), `jobs.enqueue_extract`
(Task 8 defines claim; this task adds `enqueue_extract(db, imp, text: str|None) -> Job` to `jobs.py`).
**Produces:**
- `ImportOut = {id,status,method,filename,headers,mapping,items,diff: dict|None,error}` — `diff` is
  `diff_items(...).summary()` when `status=="ready_for_review"`.
- `POST /api/catalogs/{id}/imports` (multipart `file`) → `201 ImportOut`. Over 25 MB → 413; bad type → 415. File saved
  at `uploads/<uuid>/<filename>`. Table found → `method="table"`, `ready_for_review`. Otherwise → `method="ai"`,
  `needs_ai`, extract job with payload `{import_id, text}` (`text` = `extract_text` or `None` for images/scans).
- `GET /api/imports/{id}`; `PUT /api/imports/{id}/mapping {mapping}` (table imports only, else 409) → rebuilt items;
  `POST /api/imports/{id}/apply {items: list[ExtractedItem]}` → `CatalogOut`, status `applied` (twice → 409).

- [ ] **Step 1: Failing tests:**
  - `test_upload_xlsx_ready_for_review` — items match the sheet, `diff.new` count == rows.
  - `test_upload_free_text_docx_needs_ai` — `status=="needs_ai"`, one queued extract job whose payload text contains
    the paragraph.
  - `test_upload_photo_needs_ai_without_text` — `.jpg` → payload `text is None`.
  - `test_upload_too_large_413`, `test_upload_doc_415_mentions_docx`.
  - `test_change_mapping_rebuilds_items` — map `"Remarks"` → `description`; items now have it.
  - `test_apply_creates_products_and_is_single_use` — then second apply → 409.
  - `test_other_company_import_404` — GET/PUT/apply on A's import by B → 404.
- [ ] **Step 2:** Run → fail. **Step 3:** Implement. **Step 4:** Pass. **Step 5:** Commit —
  `feat(server): import upload, mapping, review and apply`.

---

### Task 8: Job queue, worker API, image actions

**Files:** Modify `pictalog/jobs.py`; create `pictalog/api/worker.py`, `pictalog/api/variants.py`; tests
`tests/server/test_jobs.py`, `tests/server/test_worker_api.py`, `tests/server/test_variants.py`.

**Interfaces — Produces:**
- `claim_next(db, engine: str|None) -> Job|None` — first calls `requeue_stale(db, now)`; picks oldest queued job,
  `extract` before `image`; atomic `UPDATE … WHERE id=? AND status='queued'`; sets `running`, `claimed_at`,
  `attempts+=1`; image job → variant `generating`. Updates `Heartbeat`.
- `requeue_stale(db, now)` — `running` with `claimed_at` older than **10 min** → `queued`, or `failed` if
  `attempts >= 3` (variant `failed`).
- `complete_image(db, storage, job, png: bytes)`, `complete_extract(db, job, items: list[ExtractedItem])`,
  `fail_job(db, job, error)` — fail requeues while `attempts < 3`; a completed job that was cancelled meanwhile is
  ignored (204, nothing written).
- Worker routes (header `X-Worker-Token`, constant-time compare, else 401): `POST /api/worker/claim {engine}` → `200
  {id,kind,payload}` or `204`; `GET /api/worker/jobs/{id}/file`; `POST /api/worker/jobs/{id}/image` (multipart
  `file`); `POST /api/worker/jobs/{id}/items {items}`; `POST /api/worker/jobs/{id}/fail {error}`.
- `GET /api/helper/status` (user auth) → `{online: last_seen within 30 s, last_seen_at, engine}`.
- `POST /api/variants/{id}/regenerate` → `seed_offset += 1`, `enqueue_image` (works for `not_enough_detail` too —
  "Generate anyway"); `POST /api/variants/{id}/image` (multipart) → `image_source="uploaded"`, `ready`, pending jobs
  cancelled. Both return `VariantOut`, 404 for other companies.

- [ ] **Step 1: Failing tests:**
  - `test_claim_prefers_extract_jobs`, `test_claim_empty_returns_none`.
  - `test_stale_job_requeued_then_failed_after_3` — fake `now` 11 min later; third stale → job `failed`, variant
    `failed`.
  - `test_worker_requires_token` — missing/wrong → 401.
  - `test_worker_image_roundtrip` — claim → upload PNG → variant `ready`, `image_source=="generated"`, thumb exists.
  - `test_worker_items_roundtrip` — extract job → items posted → import `ready_for_review`, `method=="ai"`.
  - `test_completed_after_cancel_is_ignored` — upload photo while job running, then worker posts image → variant
    keeps uploaded image.
  - `test_helper_status_online_then_offline` — after claim online; with heartbeat 31 s old → offline.
  - `test_regenerate_bumps_seed_and_queues`, `test_upload_photo_cancels_jobs`, `test_variant_of_other_company_404`.
- [ ] **Step 2:** Run → fail. **Step 3:** Implement. **Step 4:** Pass. **Step 5:** Commit —
  `feat(server): job queue, image helper API, regenerate and photo upload`.

---

### Task 9: Sharing and PDF

**Files:** Create `pictalog/api/share.py`, `pictalog/pdf.py`; test `tests/server/test_share_pdf.py`.

**Interfaces — Produces:**
- `POST /api/catalogs/{id}/share {enabled}` → `{share_enabled, share_token}` (token `secrets.token_urlsafe(16)`, created
  once, kept when disabled).
- `GET /api/public/{token}` → `PublicCatalogOut = CatalogOut minus share_token + {company_name, logo_url}`; 404 if
  unknown or disabled.
- `render_catalog_pdf(catalog, user, storage, fetch=httpx.get) -> bytes` — A4; cover with logo, company name,
  catalog name, date; then 2×3 grid per page, one cell per variant: image (or grey box "No image"), product name,
  size/colour line, price (`currency` prefixed when `price_text` has no symbol). Provided image URLs fetched with a
  5 s timeout; failures render the grey box.
- `GET /api/catalogs/{id}/pdf`, `GET /api/public/{token}/pdf` → `application/pdf`,
  `Content-Disposition: attachment; filename="<catalog name>.pdf"`.

- [ ] **Step 1: Failing tests:** `test_share_toggle_and_public_view`, `test_public_404_when_disabled`,
  `test_pdf_has_one_cell_per_variant` (extract text with pdfplumber: every variant name appears; "No image" appears for
  a not_enough_detail variant), `test_pdf_survives_broken_image_url` (fetch raises → still a PDF).
- [ ] **Step 2:** Run → fail. **Step 3:** Implement. **Step 4:** Pass. **Step 5:** Commit —
  `feat(server): share links and PDF export`.

---

### Task 10: Image helper

**Files:** Create `pictalog_helper/{__init__,__main__,config,client,engines,reader,run}.py`; tests
`tests/helper/test_client.py`, `test_engines.py`, `test_reader.py`, `test_run.py` (all with `httpx.MockTransport`).

**Interfaces — Consumes:** worker routes (Task 8), `ExtractedItem` JSON shape (Task 5), Ollama shapes from
`spike/NOTES.md` (Task 1).
**Produces:**
- `HelperSettings(env_prefix="PICTALOG_HELPER_")`: `server_url="http://localhost:8000"`,
  `worker_token="dev-worker-token"`, `ollama_url="http://localhost:11434"`, `image_model` (from spike), `width`,
  `height` (from spike), `text_model="qwen3:8b"` (or spike pick), `ocr_model="glm-ocr"`, `poll_seconds=3`.
- `ServerClient(settings, transport=None)`: `claim() -> dict|None`, `download(job_id) -> bytes`,
  `send_image(job_id, png)`, `send_items(job_id, items: list[dict])`, `fail(job_id, error)`.
- `class ImageEngine(Protocol)`: `name: str`; `generate(prompt: str, seed: int) -> bytes` (PNG).
  `OllamaImageEngine(settings, transport=None)`.
- `DocumentReader(settings, transport=None)`: `read(text: str|None, file: bytes|None, filename: str|None) -> list[dict]`
  — text → chunks of ≤ 6000 chars split on line breaks → `/api/chat` with `format` = JSON schema `{items: [ExtractedItem
  fields]}`, `think:false`, `temperature 0` → concatenated; no text → images (HEIC via pillow-heif; PDF pages via
  pypdfium2 at 150 dpi) → `ocr_model` → text → same LLM path.
- `run_once(client, engine, reader) -> bool` (False when no job); `main()` loops, sleeps `poll_seconds` when idle,
  logs one line per job, any exception → `client.fail(job_id, str(e))` and continue.

- [ ] **Step 1: Failing tests:**
  - `test_client_sends_worker_token` — every request carries `X-Worker-Token`; claim 204 → `None`.
  - `test_ollama_engine_request_and_decode` — request body has prompt, seed, width, height per NOTES; returns the
    decoded PNG bytes.
  - `test_reader_chunks_and_merges` — 13 000-char text → 3 chat calls; items from all returned in order.
  - `test_reader_ocr_path_for_image` — no text + PNG → one OCR call then one chat call.
  - `test_run_once_image_job`, `test_run_once_extract_job`, `test_run_once_reports_failure` — engine raises →
    `fail` called with the message.
- [ ] **Step 2:** Run → fail. **Step 3:** Implement. **Step 4:** `uv run pytest tests/helper` pass.
- [ ] **Step 5:** Commit — `feat(helper): Mac image helper with Ollama image, OCR and text engines`.

---

### Task 11: Web app foundation and sign-in

**Files:** Create `web/` (Vite React TS, Tailwind v4, shadcn init; components button, input, label, card, badge,
dialog, dropdown-menu, select, switch, table, progress, skeleton, sonner, tabs), `web/src/lib/api.ts`,
`web/src/lib/auth.tsx`, `web/src/pages/{Login,Signup}.tsx`, `web/src/components/AppShell.tsx`,
`web/src/App.tsx`; test `web/src/lib/api.test.ts`.

**Interfaces — Produces:**
- `API_BASE = import.meta.env.VITE_API_BASE ?? ""` (dev: Vite proxies `/api` → `http://localhost:8000`).
- `getToken()/setToken(t|null)` (localStorage key `pictalog.token`, wrapped in try/catch);
  `api<T>(path, init?) -> Promise<T>` adds `Authorization: Bearer`, throws `ApiError(status, message)`, on 401 clears
  the token; `apiUpload<T>(path, file)`; `assetUrl(url|null)` prefixes `API_BASE` to `/api/...` URLs.
- Typed functions for every route in Tasks 2–9 (`signup, login, me, listCatalogs, createCatalog, getCatalog,
  updateCatalog, deleteCatalog, uploadImport, getImport, setMapping, applyImport, regenerate, uploadVariantPhoto,
  setShare, getPublic, helperStatus, pdfUrl, publicPdfUrl, uploadLogo`) with TS types mirroring the server schemas.
- `AuthProvider`/`useAuth()` → `{user, login, signup, logout}`; routes `/login`, `/signup`, protected `/`.
- `AppShell` header: logo/company name, `HelperStatus` badge placeholder, account menu (company name, logo, sign out).

- [ ] **Step 1: Failing tests** (Vitest, mocked `fetch`): `adds bearer header`, `401 clears token`,
  `ApiError carries server detail message`, `assetUrl prefixes API_BASE`.
- [ ] **Step 2:** `npm --prefix web test` → fail. **Step 3:** Implement. **Step 4:** Pass; `npm --prefix web run build`
  succeeds.
- [ ] **Step 5:** Commit — `feat(web): app shell, API client, sign in and sign up`.

---

### Task 12: Catalog screens

**Files:** Create `web/src/pages/{Catalogs,CatalogView}.tsx`, `web/src/components/{HelperStatus,ProductCard,
VariantSwitcher,ImageSlot,UploadButton,ShareDialog}.tsx`, `web/src/lib/catalog.ts`; test `web/src/lib/catalog.test.ts`.

**Interfaces — Produces:**
- `filterProducts(products, query, category|null) -> ProductOut[]` — case-insensitive over name, brand, description,
  sku, colour, size; `categories(products) -> string[]` sorted unique non-empty; `imageProgress(counts) -> {done,
  total}` where total excludes `none`/`not_enough_detail` and done = `ready`.
- Catalogs page: grid of catalogs, "New catalog" dialog (name, currency).
- CatalogView: header with name, image progress bar, Upload (new or updated file → navigates to check screen),
  Share dialog (switch + copy link `/c/<token>`), Download PDF, delete (confirm). Search box + category chips. Product
  cards: image (ImageSlot), name, brand, price, VariantSwitcher chips (size/colour) switching image and price.
  ImageSlot states: ready → image; queued/generating → shimmer + "Making image…" (+ "Waiting for image helper" if
  offline); not_enough_detail → empty box "Not enough detail" + "Generate anyway" / "Upload photo"; failed → "Couldn't
  make image" + Retry. Card menu: Regenerate, Upload photo. Polls `getCatalog` every 3 s while anything is queued or
  generating; `HelperStatus` polls every 10 s.

- [ ] **Step 1: Failing tests:** `filterProducts matches sku and colour`, `categories sorted unique`,
  `imageProgress ignores not_enough_detail`.
- [ ] **Step 2:** Run → fail. **Step 3:** Implement (use frontend-design guidance; product images are the hero:
  large square images, quiet chrome). **Step 4:** Tests pass; build succeeds.
- [ ] **Step 5:** Commit — `feat(web): catalog list and catalog view`.

---

### Task 13: Check screen and public catalog

**Files:** Create `web/src/pages/{ImportCheck,PublicCatalog}.tsx`, `web/src/components/{MappingRow,ItemsGrid,
DiffSummary}.tsx`; test `web/src/lib/items.test.ts` with `web/src/lib/items.ts`.

**Interfaces — Produces:**
- `updateItem(items, index, field, value) -> ExtractedItem[]` (immutable), `removeItem(items, index)`.
- ImportCheck (`/catalogs/:id/imports/:importId`): `parsing`/`needs_ai` → "Reading your file…" with helper status
  (offline → "Your Mac's image helper is off — it will read this file when it's back"), polls 3 s; `failed` → error +
  "Try another file"; `ready_for_review` → for table imports a mapping row (each column header with a field select,
  "Ignore" = null), editable items grid (rows not enough detail marked), DiffSummary (new / changed / removed counts,
  expandable names), "Apply" → catalog view.
- PublicCatalog (`/c/:token`): read-only CatalogView layout without edit actions, company logo/name, Download PDF;
  no login.

- [ ] **Step 1: Failing tests:** `updateItem does not mutate`, `removeItem removes only that row`.
- [ ] **Step 2:** Run → fail. **Step 3:** Implement. **Step 4:** Pass; build succeeds.
- [ ] **Step 5:** Commit — `feat(web): check screen and public catalog`.

---

### Task 14: Run it end to end

**Files:** Create `scripts/dev.sh`, `samples/` (generated test catalogs), `README.md`.

- [ ] **Step 1:** `scripts/dev.sh` starts `uvicorn pictalog.main:app --reload --port 8000` (factory), `npm --prefix web
  run dev`, and `uv run python -m pictalog_helper`; Ctrl-C stops all three.
- [ ] **Step 2:** Generate `samples/`: `apparel.xlsx` (title row, sizes "S, M, L", colours, prices, one SKU-only row),
  `kitchen.csv` (semicolon, Latin-1), `furniture.docx` (free text), `electronics.pdf` (table), `pricelist.jpg` (photo
  of a printed list rendered with Pillow).
- [ ] **Step 3:** In the browser (claude-in-chrome or built-in browser): sign up, upload each sample, fix one mapping,
  apply, watch images arrive, regenerate one, upload a photo for the SKU-only row, share link opens logged-out,
  download PDF. Re-upload `apparel.xlsx` with one price changed and one row removed → check counts, no image regenerated
  for the price change.
- [ ] **Step 4:** Fix anything found (each fix with a test). Full suites: `uv run pytest` and `npm --prefix web test`
  pass.
- [ ] **Step 5:** README: what it is, how to run (`scripts/dev.sh`), helper setup, samples. Commit —
  `docs: run instructions and sample catalogs`. Show the user screenshots of the real run.
