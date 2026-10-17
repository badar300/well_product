from __future__ import annotations

from decimal import Decimal

from sqlalchemy import func, select

from well_product.data.hoody_seed import apply_hoody_seed, remove_hoody_seed
from well_product.data.hoody_seed_snapshot import HOODY_ARTICLE_NO, MATERIAL_ROWS
from well_product.database import init_db, session_scope
from well_product.models import Product, RawMaterial
from well_product.services import products as product_service


def test_hoody_seed_migration_snapshot(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("WELL_PRODUCT_DATA_DIR", str(tmp_path))
    engine = init_db()

    with session_scope(engine) as session:
        apply_hoody_seed(session)
        material_count = session.scalar(select(func.count()).select_from(RawMaterial))
        assert material_count == len(MATERIAL_ROWS)
        product = session.scalar(
            select(Product).where(Product.article_no == HOODY_ARTICLE_NO)
        )
        assert product is not None
        assert "Hoody" in product.name
        cost = product_service.compute_product_cost(product)
        assert abs(cost.grand_total_pkr - Decimal("7990.1448")) <= Decimal("0.001")
        assert len(product.images) == 2

    with session_scope(engine) as session:
        apply_hoody_seed(session)
        material_count_again = session.scalar(
            select(func.count()).select_from(RawMaterial)
        )
        assert material_count_again == len(MATERIAL_ROWS)

    with session_scope(engine) as session:
        remove_hoody_seed(session)
        assert session.scalar(select(Product).where(Product.article_no == HOODY_ARTICLE_NO)) is None
        remaining = session.scalar(select(func.count()).select_from(RawMaterial))
        assert remaining == 0
