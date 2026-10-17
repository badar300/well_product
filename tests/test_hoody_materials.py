from __future__ import annotations

from decimal import Decimal

from well_product.data.hoody_materials import normalize_unit


def test_normalize_unit_variants() -> None:
    assert normalize_unit("Mtr") == "MTR"
    assert normalize_unit("mtr") == "MTR"
    assert normalize_unit("no") == "NO"
    assert normalize_unit("No") == "NO"
    assert normalize_unit("PCS") == "PCS"
