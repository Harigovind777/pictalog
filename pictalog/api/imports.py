import uuid
from pathlib import PurePath

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session

from pictalog.api.catalogs import get_owned_catalog
from pictalog.api.deps import read_upload
from pictalog.auth import current_user
from pictalog.catalog.sync import apply_items, diff_items
from pictalog.db import get_db
from pictalog.jobs import enqueue_extract
from pictalog.models import Import, User
from pictalog.parsing.detect import UnsupportedFile, detect_kind
from pictalog.parsing.mapping import TableMatch, find_table
from pictalog.parsing.rows import rows_to_items
from pictalog.parsing.tables import extract_text, read_tables
from pictalog.schemas import ApplyIn, CatalogOut, ExtractedItem, ImportOut, MappingIn

router = APIRouter(prefix="/api")

UNREADABLE = "We couldn't open this file. It may be damaged or password-protected — try saving it again and re-uploading."
NOTHING_FOUND = "We couldn't find any products in this file."


def get_owned_import(db: Session, user: User, import_id: int) -> Import:
    imp = db.get(Import, import_id)
    if imp is None or imp.catalog.user_id != user.id:
        raise HTTPException(404, "Upload not found.")
    return imp


def import_out(db: Session, imp: Import) -> ImportOut:
    items = [ExtractedItem(**i) for i in imp.items]
    diff = diff_items(db, imp.catalog, items).summary() if imp.status == "ready_for_review" else None
    return ImportOut(
        id=imp.id,
        catalog_id=imp.catalog_id,
        status=imp.status,
        method=imp.method,
        filename=imp.filename,
        headers=imp.headers,
        mapping=imp.mapping,
        items=items,
        diff=diff,
        error=imp.error,
    )


def _dump(items: list[ExtractedItem]) -> list[dict]:
    return [i.model_dump() for i in items]


@router.post("/catalogs/{catalog_id}/imports", status_code=201)
async def upload_import(
    catalog_id: int,
    file: UploadFile,
    request: Request,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> ImportOut:
    catalog = get_owned_catalog(db, user, catalog_id)
    filename = PurePath(file.filename or "upload").name
    try:
        kind = detect_kind(filename)
    except UnsupportedFile as e:
        raise HTTPException(415, str(e)) from None
    data = await read_upload(file, request)

    try:
        tables = read_tables(kind, data)
        text = extract_text(kind, data)
    except Exception:
        raise HTTPException(400, UNREADABLE) from None

    match = find_table(tables)
    if match is None:
        if kind in ("spreadsheet", "csv", "json"):
            text = "\n".join(" | ".join(c for c in row if c) for table in tables for row in table if any(row))
        # Photos and scanned PDFs have no text yet: the helper reads the picture itself.
        if kind not in ("image", "pdf") and not text.strip():
            raise HTTPException(400, NOTHING_FOUND)

    file_key = f"uploads/{uuid.uuid4().hex}/{filename}"
    request.app.state.storage.save(file_key, data, file.content_type or "application/octet-stream")
    imp = Import(catalog=catalog, filename=filename, file_key=file_key, kind=kind)
    if match is not None:
        imp.method, imp.status = "table", "ready_for_review"
        imp.headers, imp.rows, imp.mapping = match.headers, match.rows, match.mapping
        imp.items = _dump(rows_to_items(match))
        db.add(imp)
    else:
        imp.method, imp.status = "ai", "needs_ai"
        db.add(imp)
        db.flush()
        enqueue_extract(db, imp, text.strip() or None)
    db.commit()
    return import_out(db, imp)


@router.get("/imports/{import_id}")
def get_import(import_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)) -> ImportOut:
    return import_out(db, get_owned_import(db, user, import_id))


@router.put("/imports/{import_id}/mapping")
def set_mapping(
    import_id: int, body: MappingIn, user: User = Depends(current_user), db: Session = Depends(get_db)
) -> ImportOut:
    imp = get_owned_import(db, user, import_id)
    if imp.method != "table" or imp.status != "ready_for_review":
        raise HTTPException(409, "Columns can only be changed on a spreadsheet or table upload that hasn't been applied.")
    unknown = set(body.mapping) - set(imp.headers)
    if unknown:
        raise HTTPException(422, f"Unknown column: {sorted(unknown)[0]}")
    mapping = {**imp.mapping, **body.mapping}
    used = [f for f in mapping.values() if f]
    if len(used) != len(set(used)):
        raise HTTPException(422, "Each kind of information can only come from one column.")
    imp.mapping = mapping
    imp.items = _dump(rows_to_items(TableMatch(headers=imp.headers, rows=imp.rows, mapping=mapping)))
    db.commit()
    return import_out(db, imp)


@router.post("/imports/{import_id}/apply")
def apply_import(
    import_id: int, body: ApplyIn, user: User = Depends(current_user), db: Session = Depends(get_db)
) -> CatalogOut:
    imp = get_owned_import(db, user, import_id)
    if imp.status != "ready_for_review":
        raise HTTPException(409, "This upload has already been applied or isn't ready yet.")
    imp.items = _dump(body.items)
    imp.status = "applied"
    apply_items(db, imp.catalog, body.items)
    return CatalogOut.of(imp.catalog)
