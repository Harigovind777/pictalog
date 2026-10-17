from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import JSON, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from pictalog.db import Base


def utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    company_name: Mapped[str] = mapped_column(String(200))
    logo_key: Mapped[str | None] = mapped_column(String(255), default=None)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    catalogs: Mapped[list["Catalog"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Catalog(Base):
    __tablename__ = "catalogs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    currency: Mapped[str] = mapped_column(String(8), default="")
    share_enabled: Mapped[bool] = mapped_column(default=False)
    share_token: Mapped[str | None] = mapped_column(String(64), unique=True, default=None)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=utcnow, onupdate=utcnow)

    user: Mapped[User] = relationship(back_populates="catalogs")
    products: Mapped[list["Product"]] = relationship(
        back_populates="catalog", cascade="all, delete-orphan", order_by="Product.position"
    )
    imports: Mapped[list["Import"]] = relationship(back_populates="catalog", cascade="all, delete-orphan")


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    catalog_id: Mapped[int] = mapped_column(ForeignKey("catalogs.id"), index=True)
    group_key: Mapped[str] = mapped_column(String(400))
    name: Mapped[str | None] = mapped_column(String(400), default=None)
    brand: Mapped[str | None] = mapped_column(String(200), default=None)
    category: Mapped[str | None] = mapped_column(String(200), default=None)
    description: Mapped[str | None] = mapped_column(Text, default=None)
    position: Mapped[int] = mapped_column(default=0)

    catalog: Mapped[Catalog] = relationship(back_populates="products")
    variants: Mapped[list["Variant"]] = relationship(
        back_populates="product", cascade="all, delete-orphan", order_by="Variant.position"
    )


class Variant(Base):
    __tablename__ = "variants"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    match_key: Mapped[str] = mapped_column(String(600), index=True)
    sku: Mapped[str | None] = mapped_column(String(200), default=None)
    size: Mapped[str | None] = mapped_column(String(200), default=None)
    colour: Mapped[str | None] = mapped_column(String(200), default=None)
    material: Mapped[str | None] = mapped_column(String(200), default=None)
    price_text: Mapped[str | None] = mapped_column(String(100), default=None)
    price_value: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), default=None)
    extra: Mapped[dict] = mapped_column(JSON, default=dict)
    image_url_source: Mapped[str | None] = mapped_column(Text, default=None)
    image_key: Mapped[str | None] = mapped_column(String(255), default=None)
    thumb_key: Mapped[str | None] = mapped_column(String(255), default=None)
    # none | generated | provided | uploaded
    image_source: Mapped[str] = mapped_column(String(20), default="none")
    # none | not_enough_detail | queued | generating | ready | failed
    image_status: Mapped[str] = mapped_column(String(20), default="none")
    seed_offset: Mapped[int] = mapped_column(default=0)
    visual_hash: Mapped[str] = mapped_column(String(64), default="")
    position: Mapped[int] = mapped_column(default=0)

    product: Mapped[Product] = relationship(back_populates="variants")


class Import(Base):
    __tablename__ = "imports"

    id: Mapped[int] = mapped_column(primary_key=True)
    catalog_id: Mapped[int] = mapped_column(ForeignKey("catalogs.id"), index=True)
    filename: Mapped[str] = mapped_column(String(255))
    file_key: Mapped[str] = mapped_column(String(400))
    kind: Mapped[str] = mapped_column(String(20))
    # parsing | needs_ai | ready_for_review | applied | failed
    status: Mapped[str] = mapped_column(String(20), default="parsing")
    # table | ai
    method: Mapped[str | None] = mapped_column(String(10), default=None)
    headers: Mapped[list] = mapped_column(JSON, default=list)
    rows: Mapped[list] = mapped_column(JSON, default=list)
    mapping: Mapped[dict] = mapped_column(JSON, default=dict)
    items: Mapped[list] = mapped_column(JSON, default=list)
    error: Mapped[str | None] = mapped_column(Text, default=None)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    catalog: Mapped[Catalog] = relationship(back_populates="imports")


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    # extract | image
    kind: Mapped[str] = mapped_column(String(10))
    # queued | running | done | failed | cancelled
    status: Mapped[str] = mapped_column(String(10), default="queued", index=True)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    attempts: Mapped[int] = mapped_column(default=0)
    claimed_at: Mapped[datetime | None] = mapped_column(default=None)
    error: Mapped[str | None] = mapped_column(Text, default=None)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)


class Heartbeat(Base):
    __tablename__ = "heartbeat"

    id: Mapped[int] = mapped_column(primary_key=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(default=None)
    engine: Mapped[str | None] = mapped_column(String(200), default=None)
