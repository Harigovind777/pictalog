from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from pictalog.auth import current_user
from pictalog.db import get_db
from pictalog.models import Catalog, User
from pictalog.schemas import CatalogIn, CatalogOut, CatalogSummary, CatalogUpdate

router = APIRouter(prefix="/api/catalogs")


def get_owned_catalog(db: Session, user: User, catalog_id: int) -> Catalog:
    catalog = db.get(Catalog, catalog_id)
    if catalog is None or catalog.user_id != user.id:
        raise HTTPException(404, "Catalog not found.")
    return catalog


@router.get("")
def list_catalogs(user: User = Depends(current_user), db: Session = Depends(get_db)) -> list[CatalogSummary]:
    catalogs = db.scalars(
        select(Catalog).where(Catalog.user_id == user.id).order_by(Catalog.updated_at.desc())
    ).all()
    return [CatalogSummary.of(c) for c in catalogs]


@router.post("", status_code=201)
def create_catalog(body: CatalogIn, user: User = Depends(current_user), db: Session = Depends(get_db)) -> CatalogOut:
    catalog = Catalog(user_id=user.id, name=body.name.strip(), currency=body.currency.strip())
    db.add(catalog)
    db.commit()
    return CatalogOut.of(catalog)


@router.get("/{catalog_id}")
def get_catalog(catalog_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)) -> CatalogOut:
    return CatalogOut.of(get_owned_catalog(db, user, catalog_id))


@router.patch("/{catalog_id}")
def update_catalog(
    catalog_id: int, body: CatalogUpdate, user: User = Depends(current_user), db: Session = Depends(get_db)
) -> CatalogOut:
    catalog = get_owned_catalog(db, user, catalog_id)
    if body.name is not None:
        catalog.name = body.name.strip()
    if body.currency is not None:
        catalog.currency = body.currency.strip()
    db.commit()
    return CatalogOut.of(catalog)


@router.delete("/{catalog_id}", status_code=204)
def delete_catalog(catalog_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)) -> Response:
    db.delete(get_owned_catalog(db, user, catalog_id))
    db.commit()
    return Response(status_code=204)
