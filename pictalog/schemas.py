from collections import Counter
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, EmailStr, Field

from pictalog.models import Catalog, Product, User, Variant


def file_url(key: str | None) -> str | None:
    return f"/api/files/{key}" if key else None


class SignupIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=200)
    company_name: str = Field(min_length=1, max_length=200)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    company_name: str = Field(min_length=1, max_length=200)


class UserOut(BaseModel):
    id: int
    email: str
    company_name: str
    logo_url: str | None

    @classmethod
    def of(cls, user: User) -> "UserOut":
        return cls(id=user.id, email=user.email, company_name=user.company_name, logo_url=file_url(user.logo_key))


class AuthOut(BaseModel):
    token: str
    user: UserOut


class CatalogIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    currency: str = Field(default="", max_length=8)


class CatalogUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    currency: str | None = Field(default=None, max_length=8)


class CatalogSummary(BaseModel):
    id: int
    name: str
    currency: str
    product_count: int
    variant_count: int
    updated_at: datetime

    @classmethod
    def of(cls, catalog: Catalog) -> "CatalogSummary":
        return cls(
            id=catalog.id,
            name=catalog.name,
            currency=catalog.currency,
            product_count=len(catalog.products),
            variant_count=sum(len(p.variants) for p in catalog.products),
            updated_at=catalog.updated_at,
        )


class VariantOut(BaseModel):
    id: int
    sku: str | None
    size: str | None
    colour: str | None
    material: str | None
    price_text: str | None
    price_value: Decimal | None
    extra: dict[str, str]
    image_url: str | None
    thumb_url: str | None
    image_status: str
    image_source: str

    @classmethod
    def of(cls, v: Variant) -> "VariantOut":
        return cls(
            id=v.id,
            sku=v.sku,
            size=v.size,
            colour=v.colour,
            material=v.material,
            price_text=v.price_text,
            price_value=v.price_value,
            extra=v.extra or {},
            image_url=file_url(v.image_key) or v.image_url_source,
            thumb_url=file_url(v.thumb_key) or v.image_url_source,
            image_status=v.image_status,
            image_source=v.image_source,
        )


class ProductOut(BaseModel):
    id: int
    name: str | None
    brand: str | None
    category: str | None
    description: str | None
    variants: list[VariantOut]

    @classmethod
    def of(cls, p: Product) -> "ProductOut":
        return cls(
            id=p.id,
            name=p.name,
            brand=p.brand,
            category=p.category,
            description=p.description,
            variants=[VariantOut.of(v) for v in p.variants],
        )


class CatalogOut(BaseModel):
    id: int
    name: str
    currency: str
    share_enabled: bool
    share_token: str | None
    products: list[ProductOut]
    counts: dict[str, int]

    @classmethod
    def of(cls, catalog: Catalog) -> "CatalogOut":
        counts = Counter(v.image_status for p in catalog.products for v in p.variants)
        return cls(
            id=catalog.id,
            name=catalog.name,
            currency=catalog.currency,
            share_enabled=catalog.share_enabled,
            share_token=catalog.share_token,
            products=[ProductOut.of(p) for p in catalog.products],
            counts=dict(counts),
        )


ItemField = Literal[
    "name", "sku", "price", "size", "colour", "material", "brand", "category", "description", "image_url"
]


class ExtractedItem(BaseModel):
    """One catalog row (one variant) as read from a file. Shared JSON shape with the image helper."""

    name: str | None = None
    sku: str | None = None
    price_text: str | None = None
    size: str | None = None
    colour: str | None = None
    material: str | None = None
    brand: str | None = None
    category: str | None = None
    description: str | None = None
    image_url: str | None = None
    extra: dict[str, str] = {}
