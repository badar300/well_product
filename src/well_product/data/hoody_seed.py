"""Apply or remove the frozen Hoody sheet seed (materials + product + photos)."""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from well_product.data.hoody_seed_snapshot import (
    BOM_LINES,
    HOODY_ARTICLE_NO,
    HOODY_SEED_NOTE_PREFIX,
    MATERIAL_ROWS,
    MEDIA_DIR,
    PRODUCT_META,
    SLOT_IMAGES,
)
from well_product.models import Product, RawMaterial
from well_product.services import materials as material_service
from well_product.services import product_images as image_service
from well_product.services import products as product_service
from well_product.units import CostingMode, ProductImageKind


def _material_note(section: str) -> str:
    return f"{HOODY_SEED_NOTE_PREFIX} · {section}"


def upsert_hoody_materials(session: Session) -> None:
    for row in MATERIAL_ROWS:
        name = row["name"]
        unit = row["unit"]
        rate = Decimal(row["rate"])
        notes = _material_note(row["section"])
        existing = session.scalar(select(RawMaterial).where(RawMaterial.name == name))
        if existing is None:
            material_service.create_material(
                session, name=name, unit=unit, rate=rate, notes=notes
            )
        else:
            material_service.update_material(
                session, existing, name=name, unit=unit, rate=rate, notes=notes
            )


def import_hoody_product(session: Session) -> int:
    materials_by_name = {
        m.name: m.id for m in session.scalars(select(RawMaterial)).all()
    }
    missing = [
        line["material_name"]
        for line in BOM_LINES
        if line["material_name"] not in materials_by_name
    ]
    if missing:
        raise RuntimeError(
            "Hoody seed missing raw materials in database: "
            + ", ".join(missing[:5])
            + (f" … (+{len(missing) - 5} more)" if len(missing) > 5 else "")
        )

    existing = session.scalar(
        select(Product).where(Product.article_no == HOODY_ARTICLE_NO)
    )
    if existing is not None:
        product_service.delete_product(session, existing)
        session.flush()

    meta = PRODUCT_META
    product = product_service.create_product(
        session,
        name=meta["name"],
        article_no=meta["article_no"],
        customer_id=None,
        special_note=meta["special_note"],
        exchange_rate=meta["exchange_rate"],
        production_loss_pct=meta["production_loss_pct"],
        government_tax_pct=meta["government_tax_pct"],
        commission_pct=meta["commission_pct"],
        factory_overhead_pct=meta["factory_overhead_pct"],
        profit_pct=meta["profit_pct"],
        pricing_adjustment_pkr=meta["pricing_adjustment_pkr"],
        costing_mode=CostingMode.FULL.value,
    )
    product_id = product.id

    material_lines = [
        {
            "raw_material_id": materials_by_name[str(line["material_name"])],
            "average_qty": line["average_qty"],
            "waste_pct": line["waste_pct"],
            "category": line["category"],
            "rate_override": None,
            "sort_order": line["sort_order"],
        }
        for line in BOM_LINES
    ]
    product_service.replace_product_materials(session, product, material_lines)
    product_service.replace_product_extra_costs(session, product, [])

    for kind_value, filename in SLOT_IMAGES:
        source = MEDIA_DIR / filename
        if not source.is_file():
            raise FileNotFoundError(f"Hoody seed image missing: {source}")
        kind = ProductImageKind(kind_value)
        image_service.set_slot_image(session, product_id, kind, source)

    session.flush()
    return product_id


def apply_hoody_seed(session: Session) -> None:
    """Insert Hoody sheet materials and product if not already present."""
    existing = session.scalar(
        select(Product).where(Product.article_no == HOODY_ARTICLE_NO)
    )
    if existing is not None:
        return
    upsert_hoody_materials(session)
    import_hoody_product(session)


def remove_hoody_seed(session: Session) -> None:
    """Remove Hoody seed product, materials, and seed-tagged notes."""
    product = session.scalar(
        select(Product).where(Product.article_no == HOODY_ARTICLE_NO)
    )
    if product is not None:
        product_service.delete_product(session, product)
        session.flush()

    seed_names = {row["name"] for row in MATERIAL_ROWS}
    for material in session.scalars(select(RawMaterial)).all():
        if material.name not in seed_names:
            continue
        note = material.notes or ""
        if not note.startswith(HOODY_SEED_NOTE_PREFIX):
            continue
        session.execute(delete(RawMaterial).where(RawMaterial.id == material.id))
    session.flush()
