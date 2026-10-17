from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from well_product.costing.engine import (
    BomLineInput,
    CostBreakdown,
    ExtraCostInput,
    ProductCostInput,
    calculate_product_cost,
)
from well_product.models import Product, ProductExtraCost, ProductMaterial
from well_product.services import product_images as image_service
from well_product.units import ExtraCostKind, MaterialCategory


def list_products(session: Session) -> list[Product]:
    return list(
        session.scalars(
            select(Product)
            .options(
                selectinload(Product.customer),
                selectinload(Product.materials).selectinload(
                    ProductMaterial.raw_material
                ),
                selectinload(Product.extra_costs),
                selectinload(Product.images),
            )
            .order_by(Product.name)
        ).all()
    )


def get_product(session: Session, product_id: int) -> Product | None:
    return session.scalar(
        select(Product)
        .where(Product.id == product_id)
        .options(
            selectinload(Product.customer),
            selectinload(Product.materials).selectinload(
                ProductMaterial.raw_material
            ),
            selectinload(Product.extra_costs),
            selectinload(Product.images),
        )
    )


def effective_rate(line: ProductMaterial) -> Decimal:
    if line.rate_override is not None:
        return line.rate_override
    return line.raw_material.rate


def product_to_cost_input(product: Product) -> ProductCostInput:
    bom: list[BomLineInput] = []
    for line in sorted(product.materials, key=lambda m: (m.category, m.sort_order, m.id)):
        bom.append(
            BomLineInput(
                label=line.raw_material.name,
                category=MaterialCategory(line.category),
                rate=effective_rate(line),
                average_qty=line.average_qty,
                waste_pct=line.waste_pct,
            )
        )
    extras = tuple(
        ExtraCostInput(
            kind=ExtraCostKind(e.kind),
            name=e.name,
            amount=e.amount,
        )
        for e in sorted(product.extra_costs, key=lambda x: (x.sort_order, x.id))
    )
    return ProductCostInput(
        exchange_rate=product.exchange_rate,
        production_loss_pct=product.production_loss_pct,
        government_tax_pct=product.government_tax_pct,
        commission_pct=product.commission_pct,
        factory_overhead_pct=product.factory_overhead_pct,
        profit_pct=product.profit_pct,
        pricing_adjustment_pkr=product.pricing_adjustment_pkr,
        bom_lines=tuple(bom),
        extra_costs=extras,
    )


def compute_product_cost(product: Product) -> CostBreakdown:
    return calculate_product_cost(product_to_cost_input(product))


def create_product(
    session: Session,
    *,
    name: str,
    article_no: str | None,
    customer_id: int | None,
    special_note: str | None,
    exchange_rate: Decimal,
    production_loss_pct: Decimal,
    government_tax_pct: Decimal,
    commission_pct: Decimal,
    factory_overhead_pct: Decimal,
    profit_pct: Decimal,
    pricing_adjustment_pkr: Decimal,
    costing_mode: str,
) -> Product:
    product = Product(
        name=name.strip(),
        article_no=article_no.strip() if article_no else None,
        customer_id=customer_id,
        special_note=special_note,
        exchange_rate=exchange_rate,
        production_loss_pct=production_loss_pct,
        government_tax_pct=government_tax_pct,
        commission_pct=commission_pct,
        factory_overhead_pct=factory_overhead_pct,
        profit_pct=profit_pct,
        pricing_adjustment_pkr=pricing_adjustment_pkr,
        costing_mode=costing_mode,
    )
    session.add(product)
    session.flush()
    return product


def update_product_header(
    session: Session,
    product: Product,
    *,
    name: str,
    article_no: str | None,
    customer_id: int | None,
    special_note: str | None,
    exchange_rate: Decimal,
    production_loss_pct: Decimal,
    government_tax_pct: Decimal,
    commission_pct: Decimal,
    factory_overhead_pct: Decimal,
    profit_pct: Decimal,
    pricing_adjustment_pkr: Decimal,
    costing_mode: str,
) -> Product:
    product.name = name.strip()
    product.article_no = article_no.strip() if article_no else None
    product.customer_id = customer_id
    product.special_note = special_note
    product.exchange_rate = exchange_rate
    product.production_loss_pct = production_loss_pct
    product.government_tax_pct = government_tax_pct
    product.commission_pct = commission_pct
    product.factory_overhead_pct = factory_overhead_pct
    product.profit_pct = profit_pct
    product.pricing_adjustment_pkr = pricing_adjustment_pkr
    product.costing_mode = costing_mode
    session.flush()
    return product


def replace_product_materials(
    session: Session,
    product: Product,
    lines: list[dict],
) -> None:
    for existing in list(product.materials):
        session.delete(existing)
    session.flush()
    for idx, row in enumerate(lines):
        session.add(
            ProductMaterial(
                product_id=product.id,
                raw_material_id=row["raw_material_id"],
                average_qty=row["average_qty"],
                waste_pct=row["waste_pct"],
                category=row["category"],
                rate_override=row.get("rate_override"),
                sort_order=row.get("sort_order", idx),
            )
        )
    session.flush()


def replace_product_extra_costs(
    session: Session,
    product: Product,
    lines: list[dict],
) -> None:
    for existing in list(product.extra_costs):
        session.delete(existing)
    session.flush()
    for idx, row in enumerate(lines):
        session.add(
            ProductExtraCost(
                product_id=product.id,
                kind=row["kind"],
                name=row["name"],
                amount=row["amount"],
                sort_order=row.get("sort_order", idx),
            )
        )
    session.flush()


def delete_product(session: Session, product: Product) -> None:
    product_id = product.id
    image_service.remove_product_media_dir(product_id)
    session.delete(product)


def duplicate_product(
    session: Session,
    source: Product,
    *,
    name: str,
    article_no: str | None,
    customer_id: int | None,
) -> Product:
    clone = Product(
        name=name.strip(),
        article_no=article_no.strip() if article_no else None,
        customer_id=customer_id,
        special_note=source.special_note,
        exchange_rate=source.exchange_rate,
        production_loss_pct=source.production_loss_pct,
        government_tax_pct=source.government_tax_pct,
        commission_pct=source.commission_pct,
        factory_overhead_pct=source.factory_overhead_pct,
        profit_pct=source.profit_pct,
        pricing_adjustment_pkr=source.pricing_adjustment_pkr,
        costing_mode=source.costing_mode,
    )
    session.add(clone)
    session.flush()
    for m in sorted(source.materials, key=lambda x: x.sort_order):
        session.add(
            ProductMaterial(
                product_id=clone.id,
                raw_material_id=m.raw_material_id,
                average_qty=m.average_qty,
                waste_pct=m.waste_pct,
                category=m.category,
                rate_override=m.rate_override,
                sort_order=m.sort_order,
            )
        )
    for e in sorted(source.extra_costs, key=lambda x: x.sort_order):
        session.add(
            ProductExtraCost(
                product_id=clone.id,
                kind=e.kind,
                name=e.name,
                amount=e.amount,
                sort_order=e.sort_order,
            )
        )
    session.flush()
    source_with_images = get_product(session, source.id)
    if source_with_images is not None and source_with_images.images:
        image_service.copy_images_to_product(session, source.id, clone.id)
    loaded = get_product(session, clone.id)
    if loaded is None:
        raise RuntimeError("Failed to load duplicated product")
    return loaded
