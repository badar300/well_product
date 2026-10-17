"""Import the complete Hoody product (BOM, pricing, images) from the Excel sheet."""

from __future__ import annotations

import argparse
from decimal import Decimal
from pathlib import Path

from sqlalchemy import select

from well_product.data.hoody_sheet import (
    extract_hoody_images,
    extract_image_to_temp,
    load_hoody_cells,
    parse_hoody_bom,
    parse_hoody_product_meta,
)
from well_product.database import init_db, session_scope
from well_product.models import Product, RawMaterial
from well_product.services import product_images as image_service
from well_product.services import products as product_service
from well_product.units import CostingMode, ProductImageKind


def _find_product_by_article(session, article_no: str) -> Product | None:
    return session.scalar(select(Product).where(Product.article_no == article_no))


def import_hoody_product(xlsx_path: Path) -> int:
    cells = load_hoody_cells(xlsx_path)
    meta = parse_hoody_product_meta(cells)
    bom = parse_hoody_bom(cells)
    images = extract_hoody_images(xlsx_path)

    engine = init_db()
    temp_files: list[Path] = []
    try:
        with session_scope(engine) as session:
            materials_by_name = {
                m.name: m.id for m in session.scalars(select(RawMaterial)).all()
            }
            missing = [line.material_name for line in bom if line.material_name not in materials_by_name]
            if missing:
                raise RuntimeError(
                    "Raw materials missing from database (run well-product-seed-hoody first): "
                    + ", ".join(missing[:5])
                    + (f" … (+{len(missing) - 5} more)" if len(missing) > 5 else "")
                )

            existing = _find_product_by_article(session, meta.article_no)
            if existing is not None:
                product_service.delete_product(session, existing)
                session.flush()

            product = product_service.create_product(
                session,
                name=meta.name,
                article_no=meta.article_no,
                customer_id=None,
                special_note=meta.special_note,
                exchange_rate=meta.exchange_rate,
                production_loss_pct=meta.production_loss_pct,
                government_tax_pct=meta.government_tax_pct,
                commission_pct=meta.commission_pct,
                factory_overhead_pct=meta.factory_overhead_pct,
                profit_pct=meta.profit_pct,
                pricing_adjustment_pkr=meta.pricing_adjustment_pkr,
                costing_mode=CostingMode.FULL.value,
            )
            product_id = product.id

            material_lines = [
                {
                    "raw_material_id": materials_by_name[line.material_name],
                    "average_qty": line.average_qty,
                    "waste_pct": line.waste_pct,
                    "category": line.category.value,
                    "rate_override": None,
                    "sort_order": line.sort_order,
                }
                for line in bom
            ]
            product_service.replace_product_materials(session, product, material_lines)
            product_service.replace_product_extra_costs(session, product, [])

            for img in images:
                temp = extract_image_to_temp(xlsx_path, img.media_path)
                temp_files.append(temp)
                if img.kind in (ProductImageKind.FRONT, ProductImageKind.BACK):
                    image_service.set_slot_image(
                        session, product_id, img.kind, temp
                    )
                else:
                    image_service.add_extra_image(session, product_id, temp)

            session.flush()
            return product_id
    finally:
        for p in temp_files:
            p.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Import Hoody product from Excel (BOM, rates, photos)."
    )
    parser.add_argument(
        "xlsx",
        type=Path,
        help="Path to Well Product Hoody .xlsx",
    )
    args = parser.parse_args()
    product_id = import_hoody_product(args.xlsx)
    print(f"Imported Hoody product id={product_id} from {args.xlsx}")


if __name__ == "__main__":
    main()
