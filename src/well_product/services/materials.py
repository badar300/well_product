from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from well_product.models import Product, ProductMaterial, RawMaterial


class MaterialInUseError(Exception):
    """Raised when a raw material is referenced on a product BOM."""

    def __init__(self, product_names: list[str]) -> None:
        self.product_names = product_names
        names = ", ".join(product_names)
        super().__init__(
            f"This material is used on product BOM line(s) for: {names}. "
            "Remove it from those products first, then delete."
        )


def list_materials(session: Session) -> list[RawMaterial]:
    return list(
        session.scalars(select(RawMaterial).order_by(RawMaterial.name)).all()
    )


def get_material(session: Session, material_id: int) -> RawMaterial | None:
    return session.get(RawMaterial, material_id)


def product_names_using_material(session: Session, material_id: int) -> list[str]:
    rows = session.execute(
        select(Product.name)
        .join(ProductMaterial, ProductMaterial.product_id == Product.id)
        .where(ProductMaterial.raw_material_id == material_id)
        .distinct()
        .order_by(Product.name)
    ).all()
    return [name for (name,) in rows]


def create_material(
    session: Session,
    *,
    name: str,
    unit: str,
    rate: Decimal,
    notes: str | None = None,
) -> RawMaterial:
    material = RawMaterial(name=name.strip(), unit=unit, rate=rate, notes=notes)
    session.add(material)
    session.flush()
    return material


def update_material(
    session: Session,
    material: RawMaterial,
    *,
    name: str,
    unit: str,
    rate: Decimal,
    notes: str | None,
) -> RawMaterial:
    material.name = name.strip()
    material.unit = unit
    material.rate = rate
    material.notes = notes
    session.flush()
    return material


def delete_material(session: Session, material: RawMaterial) -> None:
    in_use = product_names_using_material(session, material.id)
    if in_use:
        raise MaterialInUseError(in_use)
    session.delete(material)
