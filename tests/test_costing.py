from __future__ import annotations

from decimal import Decimal

import pytest

from well_product.costing.engine import (
    BomLineInput,
    ExtraCostInput,
    ProductCostInput,
    calculate_product_cost,
)
from well_product.units import ExtraCostKind, MaterialCategory


def test_line_formula_waste_and_pkr() -> None:
    data = ProductCostInput(
        exchange_rate=Decimal("277"),
        bom_lines=(
            BomLineInput(
                label="Thread",
                category=MaterialCategory.ACCESSORY,
                rate=Decimal("260"),
                average_qty=Decimal("0.06"),
                waste_pct=Decimal("10"),
            ),
        ),
    )
    result = calculate_product_cost(data)
    line = result.sections[0].lines[0]
    assert line.waste_amount == Decimal("1.56")
    assert line.line_pkr == Decimal("17.16")


def test_factory_overhead_and_grand_total_hoody_scale() -> None:
    """Section totals match Hoody sheet manufacturing + 7% overhead + grand."""
    exchange = Decimal("277")
    lines = (
        BomLineInput("Fabric", MaterialCategory.FABRIC, Decimal("2947.4"), Decimal("1"), Decimal("0")),
        BomLineInput("Accessories", MaterialCategory.ACCESSORY, Decimal("2563.26"), Decimal("1"), Decimal("0")),
        BomLineInput("Packaging", MaterialCategory.PACKAGING, Decimal("63.765"), Decimal("1"), Decimal("0")),
        BomLineInput("Special", MaterialCategory.SPECIAL_OPERATION, Decimal("303"), Decimal("1"), Decimal("0")),
        BomLineInput("Labour", MaterialCategory.LABOUR, Decimal("1590"), Decimal("1"), Decimal("0")),
    )
    data = ProductCostInput(
        exchange_rate=exchange,
        factory_overhead_pct=Decimal("7"),
        bom_lines=lines,
    )
    result = calculate_product_cost(data)
    assert result.manufacturing_pkr == Decimal("7467.425")
    assert result.percent_overheads_pkr == Decimal("522.7198")
    assert result.grand_total_pkr == Decimal("7990.1448")
    assert result.grand_total_usd == Decimal("28.8453")


def test_selling_price_with_profit_and_cmt_adjustment() -> None:
    data = ProductCostInput(
        exchange_rate=Decimal("277"),
        profit_pct=Decimal("10"),
        pricing_adjustment_pkr=Decimal("1000"),
        bom_lines=(
            BomLineInput(
                "Labour",
                MaterialCategory.LABOUR,
                Decimal("100"),
                Decimal("1"),
                Decimal("0"),
            ),
        ),
    )
    result = calculate_product_cost(data)
    assert result.grand_total_pkr == Decimal("100")
    assert result.selling_price_pkr == Decimal("1110")


def test_fixed_logistic_extras_in_grand_total() -> None:
    data = ProductCostInput(
        exchange_rate=Decimal("277"),
        bom_lines=(
            BomLineInput(
                "Item",
                MaterialCategory.FABRIC,
                Decimal("50"),
                Decimal("1"),
                Decimal("0"),
            ),
        ),
        extra_costs=(
            ExtraCostInput(ExtraCostKind.LOGISTIC, "Freight", Decimal("1500")),
            ExtraCostInput(ExtraCostKind.OTHER, "Misc", Decimal("100")),
        ),
    )
    result = calculate_product_cost(data)
    assert result.fixed_logistic_pkr == Decimal("1500")
    assert result.fixed_other_pkr == Decimal("100")
    assert result.grand_total_pkr == Decimal("1650")


def test_empty_bom_yields_zero_grand_total() -> None:
    result = calculate_product_cost(
        ProductCostInput(exchange_rate=Decimal("277"), bom_lines=())
    )
    assert result.manufacturing_pkr == Decimal("0")
    assert result.grand_total_pkr == Decimal("0")
    assert result.selling_price_pkr == Decimal("0")


def test_exchange_rate_must_be_positive() -> None:
    with pytest.raises(ValueError):
        calculate_product_cost(ProductCostInput(exchange_rate=Decimal("0")))
