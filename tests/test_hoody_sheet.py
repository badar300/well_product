from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest

from well_product.data.hoody_sheet import (
    load_hoody_cells,
    parse_hoody_bom,
    parse_hoody_product_meta,
)
from well_product.services import products as product_service
from well_product.database import init_db, session_scope

HOODY_XLSX = Path(
    "/Users/macbookpro/Downloads/Well Product - Cost Sheet for hoody ahmad sb (2).xlsx"
)


@pytest.fixture
def hoody_xlsx() -> Path:
    if not HOODY_XLSX.is_file():
        pytest.skip("Hoody xlsx not available")
    return HOODY_XLSX


def test_parse_hoody_meta_and_bom_count(hoody_xlsx: Path) -> None:
    cells = load_hoody_cells(hoody_xlsx)
    meta = parse_hoody_product_meta(cells)
    assert "Hoody Black Dryrider" in meta.name
    assert meta.article_no == "45996"
    assert meta.exchange_rate == Decimal("277")
    assert meta.factory_overhead_pct == Decimal("7")
    bom = parse_hoody_bom(cells)
    assert len(bom) == 33


def test_imported_hoody_grand_total_matches_sheet(hoody_xlsx: Path, tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("WELL_PRODUCT_DATA_DIR", str(tmp_path))
    from well_product.scripts.seed_hoody_materials import upsert_hoody_materials
    from well_product.data.hoody_materials import parse_hoody_full_sheet
    from well_product.scripts.seed_hoody_product import import_hoody_product

    engine = init_db()
    with session_scope(engine) as session:
        upsert_hoody_materials(session, parse_hoody_full_sheet(hoody_xlsx))
    product_id = import_hoody_product(hoody_xlsx)
    with session_scope(engine) as session:
        product = product_service.get_product(session, product_id)
        assert product is not None
        cost = product_service.compute_product_cost(product)
        assert abs(cost.grand_total_pkr - Decimal("7990.1448")) <= Decimal("0.001")
        assert len(product.images) >= 1
