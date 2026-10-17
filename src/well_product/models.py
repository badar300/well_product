"""SQLAlchemy ORM models."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )


class Customer(Base, TimestampMixin):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(64))
    company: Mapped[str | None] = mapped_column(String(255))
    address: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)

    products: Mapped[list[Product]] = relationship(back_populates="customer")
    orders: Mapped[list[CustomerOrder]] = relationship(back_populates="customer")


class RawMaterial(Base, TimestampMixin):
    __tablename__ = "raw_materials"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    unit: Mapped[str] = mapped_column(String(16), nullable=False)
    rate: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)

    product_materials: Mapped[list[ProductMaterial]] = relationship(
        back_populates="raw_material",
        passive_deletes=True,
    )


class Product(Base, TimestampMixin):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    article_no: Mapped[str | None] = mapped_column(String(64), unique=True)
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id"))
    special_note: Mapped[str | None] = mapped_column(Text)
    exchange_rate: Mapped[Decimal] = mapped_column(
        Numeric(18, 4), nullable=False, default=Decimal("277")
    )
    production_loss_pct: Mapped[Decimal] = mapped_column(
        Numeric(8, 6), nullable=False, default=0
    )
    government_tax_pct: Mapped[Decimal] = mapped_column(
        Numeric(8, 6), nullable=False, default=0
    )
    commission_pct: Mapped[Decimal] = mapped_column(
        Numeric(8, 6), nullable=False, default=0
    )
    factory_overhead_pct: Mapped[Decimal] = mapped_column(
        Numeric(8, 6), nullable=False, default=0
    )
    profit_pct: Mapped[Decimal] = mapped_column(
        Numeric(8, 6), nullable=False, default=0
    )
    pricing_adjustment_pkr: Mapped[Decimal] = mapped_column(
        Numeric(18, 4), nullable=False, default=0
    )
    costing_mode: Mapped[str] = mapped_column(
        String(16), nullable=False, default="full"
    )

    customer: Mapped[Customer | None] = relationship(back_populates="products")
    materials: Mapped[list[ProductMaterial]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
    )
    extra_costs: Mapped[list[ProductExtraCost]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
    )
    orders: Mapped[list[CustomerOrder]] = relationship(back_populates="product")
    images: Mapped[list[ProductImage]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
    )


class ProductImage(Base, TimestampMixin):
    __tablename__ = "product_images"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
    )
    kind: Mapped[str] = mapped_column(String(16), nullable=False)
    relative_path: Mapped[str] = mapped_column(String(512), nullable=False)
    sort_order: Mapped[int] = mapped_column(default=0, nullable=False)

    product: Mapped[Product] = relationship(back_populates="images")


class ProductMaterial(Base, TimestampMixin):
    __tablename__ = "product_materials"
    __table_args__ = (
        UniqueConstraint("product_id", "raw_material_id", name="uq_product_material"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
    )
    raw_material_id: Mapped[int] = mapped_column(
        ForeignKey("raw_materials.id", ondelete="RESTRICT"),
        nullable=False,
    )
    average_qty: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    waste_pct: Mapped[Decimal] = mapped_column(
        Numeric(8, 6), nullable=False, default=0
    )  # whole percent (5 = 5% waste)
    category: Mapped[str] = mapped_column(
        String(32), nullable=False, default="accessory"
    )
    rate_override: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    sort_order: Mapped[int] = mapped_column(default=0, nullable=False)

    product: Mapped[Product] = relationship(back_populates="materials")
    raw_material: Mapped[RawMaterial] = relationship(back_populates="product_materials")


class ProductExtraCost(Base, TimestampMixin):
    __tablename__ = "product_extra_costs"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
    )
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    sort_order: Mapped[int] = mapped_column(default=0, nullable=False)

    product: Mapped[Product] = relationship(back_populates="extra_costs")


class CustomerOrder(Base, TimestampMixin):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)

    customer: Mapped[Customer] = relationship(back_populates="orders")
    product: Mapped[Product] = relationship(back_populates="orders")
    extra_costs: Mapped[list[OrderExtraCost]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
    )


class OrderExtraCost(Base, TimestampMixin):
    __tablename__ = "order_extra_costs"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    sort_order: Mapped[int] = mapped_column(default=0, nullable=False)

    order: Mapped[CustomerOrder] = relationship(back_populates="extra_costs")
