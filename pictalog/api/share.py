import secrets
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from pictalog.api.catalogs import get_owned_catalog
from pictalog.auth import current_user
from pictalog.db import get_db
from pictalog.models import Catalog, User
from pictalog.pdf import render_catalog_pdf
from pictalog.schemas import CatalogOut, ProductOut, file_url

router = APIRouter(prefix="/api")


class ShareIn(BaseModel):
    enabled: bool


class ShareOut(BaseModel):
    share_enabled: bool
    share_token: str | None


class PublicCatalogOut(BaseModel):
    id: int
    name: str
    currency: str
    products: list[ProductOut]
    counts: dict[str, int]
    company_name: str
    logo_url: str | None


def _pdf_response(request: Request, catalog: Catalog) -> Response:
    data = render_catalog_pdf(catalog, catalog.user, request.app.state.storage)
    name = f"{catalog.name}.pdf"
    ascii_name = name.encode("ascii", "ignore").decode().replace('"', "") or "catalog.pdf"
    disposition = f'attachment; filename="{ascii_name}"'
    if ascii_name != name:
        disposition += f"; filename*=UTF-8''{quote(name)}"
    return Response(data, media_type="application/pdf", headers={"Content-Disposition": disposition})


def _shared_catalog(db: Session, token: str) -> Catalog:
    catalog = db.scalar(select(Catalog).where(Catalog.share_token == token))
    if catalog is None or not catalog.share_enabled:
        raise HTTPException(404, "This catalog isn't shared, or the link has been turned off.")
    return catalog


@router.post("/catalogs/{catalog_id}/share")
def set_share(catalog_id: int, body: ShareIn, user: User = Depends(current_user), db: Session = Depends(get_db)) -> ShareOut:
    catalog = get_owned_catalog(db, user, catalog_id)
    if body.enabled and not catalog.share_token:
        catalog.share_token = secrets.token_urlsafe(16)
    catalog.share_enabled = body.enabled
    db.commit()
    return ShareOut(share_enabled=catalog.share_enabled, share_token=catalog.share_token)


@router.get("/catalogs/{catalog_id}/pdf")
def catalog_pdf(catalog_id: int, request: Request, user: User = Depends(current_user), db: Session = Depends(get_db)) -> Response:
    return _pdf_response(request, get_owned_catalog(db, user, catalog_id))


@router.get("/public/{token}")
def public_catalog(token: str, db: Session = Depends(get_db)) -> PublicCatalogOut:
    catalog = _shared_catalog(db, token)
    out = CatalogOut.of(catalog)
    return PublicCatalogOut(
        id=out.id,
        name=out.name,
        currency=out.currency,
        products=out.products,
        counts=out.counts,
        company_name=catalog.user.company_name,
        logo_url=file_url(catalog.user.logo_key),
    )


@router.get("/public/{token}/pdf")
def public_pdf(token: str, request: Request, db: Session = Depends(get_db)) -> Response:
    return _pdf_response(request, _shared_catalog(db, token))
