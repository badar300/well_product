"""Pure costing logic aligned with the Excel cost sheet."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from well_product.units import ExtraCostKind, MaterialCategory

ZERO = Decimal("0")
FOUR = Decimal("0.0001")
HUNDRED = Decimal("100")


def _pct_fraction(pct_points: Decimal) -> Decimal:
    """Convert stored whole percent (7) to multiplier fraction (0.07)."""
    return pct_points / HUNDRED


@dataclass(frozen=True)
class BomLineInput:
    label: str
    category: MaterialCategory
    rate: Decimal
    average_qty: Decimal
    waste_pct: Decimal  # whole percent, e.g. 5 means 5%


@dataclass(frozen=True)
class ExtraCostInput:
    kind: ExtraCostKind
    name: str
    amount: Decimal


@dataclass(frozen=True)
class ProductCostInput:
    exchange_rate: Decimal
    production_loss_pct: Decimal = ZERO  # whole percent, e.g. 7 = 7%
    government_tax_pct: Decimal = ZERO
    commission_pct: Decimal = ZERO
    factory_overhead_pct: Decimal = ZERO
    profit_pct: Decimal = ZERO
    pricing_adjustment_pkr: Decimal = ZERO
    bom_lines: tuple[BomLineInput, ...] = ()
    extra_costs: tuple[ExtraCostInput, ...] = ()


@dataclass(frozen=True)
class LineCostResult:
    label: str
    category: MaterialCategory
    waste_amount: Decimal
    line_pkr: Decimal
    line_usd: Decimal
    share_of_grand: Decimal


@dataclass(frozen=True)
class SectionCostResult:
    category: MaterialCategory
    waste_total: Decimal
    pkr_total: Decimal
    usd_total: Decimal
    share_of_grand: Decimal
    lines: tuple[LineCostResult, ...]


@dataclass(frozen=True)
class PercentOverheadResult:
    name: str
    pct: Decimal
    pkr: Decimal
    usd: Decimal
    share_of_grand: Decimal


@dataclass
class CostBreakdown:
    exchange_rate: Decimal
    sections: list[SectionCostResult] = field(default_factory=list)
    manufacturing_pkr: Decimal = ZERO
    manufacturing_usd: Decimal = ZERO
    percent_overheads: list[PercentOverheadResult] = field(default_factory=list)
    percent_overheads_pkr: Decimal = ZERO
    percent_overheads_usd: Decimal = ZERO
    fixed_logistic_pkr: Decimal = ZERO
    fixed_other_pkr: Decimal = ZERO
    fixed_extras_pkr: Decimal = ZERO
    fixed_extras_usd: Decimal = ZERO
    grand_total_pkr: Decimal = ZERO
    grand_total_usd: Decimal = ZERO
    selling_price_pkr: Decimal = ZERO
    selling_price_usd: Decimal = ZERO
    profit_pkr: Decimal = ZERO


def _usd(pkr: Decimal, exchange_rate: Decimal) -> Decimal:
    if exchange_rate <= ZERO:
        return ZERO
    return (pkr / exchange_rate).quantize(FOUR)


def _line_costs(
    line: BomLineInput, exchange_rate: Decimal, grand_pkr: Decimal
) -> LineCostResult:
    waste_frac = line.waste_pct / Decimal("100")
    waste = (line.average_qty * waste_frac * line.rate).quantize(FOUR)
    pkr = (line.average_qty * line.rate + waste).quantize(FOUR)
    share = (pkr / grand_pkr).quantize(FOUR) if grand_pkr > ZERO else ZERO
    return LineCostResult(
        label=line.label,
        category=line.category,
        waste_amount=waste,
        line_pkr=pkr,
        line_usd=_usd(pkr, exchange_rate),
        share_of_grand=share,
    )


def calculate_product_cost(data: ProductCostInput) -> CostBreakdown:
    if data.exchange_rate <= ZERO:
        raise ValueError("exchange_rate must be positive")

    # First pass: line PKR without share (grand unknown).
    raw_lines: list[tuple[BomLineInput, Decimal, Decimal]] = []
    for line in data.bom_lines:
        waste_frac = line.waste_pct / Decimal("100")
        waste = (line.average_qty * waste_frac * line.rate).quantize(FOUR)
        pkr = (line.average_qty * line.rate + waste).quantize(FOUR)
        raw_lines.append((line, waste, pkr))

    manufacturing_pkr = sum((pkr for _, _, pkr in raw_lines), ZERO).quantize(FOUR)

    percent_specs = (
        ("Production Loss", data.production_loss_pct),
        ("Government Tax", data.government_tax_pct),
        ("Commission", data.commission_pct),
        ("Factory Overhead", data.factory_overhead_pct),
    )
    percent_overheads_pkr = ZERO
    percent_rows: list[PercentOverheadResult] = []
    for name, pct in percent_specs:
        amount = (manufacturing_pkr * _pct_fraction(pct)).quantize(FOUR)
        percent_overheads_pkr += amount
        percent_rows.append(
            PercentOverheadResult(
                name=name,
                pct=pct,
                pkr=amount,
                usd=_usd(amount, data.exchange_rate),
                share_of_grand=ZERO,
            )
        )
    percent_overheads_pkr = percent_overheads_pkr.quantize(FOUR)

    fixed_logistic = sum(
        (e.amount for e in data.extra_costs if e.kind == ExtraCostKind.LOGISTIC),
        ZERO,
    ).quantize(FOUR)
    fixed_other = sum(
        (e.amount for e in data.extra_costs if e.kind == ExtraCostKind.OTHER),
        ZERO,
    ).quantize(FOUR)
    fixed_extras_pkr = (fixed_logistic + fixed_other).quantize(FOUR)

    grand_pkr = (
        manufacturing_pkr + percent_overheads_pkr + fixed_extras_pkr
    ).quantize(FOUR)
    grand_usd = _usd(grand_pkr, data.exchange_rate)

    # Section rollups with share of grand.
    section_map: dict[MaterialCategory, list[LineCostResult]] = {
        cat: [] for cat in MaterialCategory
    }
    for line, waste, pkr in raw_lines:
        share = (pkr / grand_pkr).quantize(FOUR) if grand_pkr > ZERO else ZERO
        section_map[line.category].append(
            LineCostResult(
                label=line.label,
                category=line.category,
                waste_amount=waste,
                line_pkr=pkr,
                line_usd=_usd(pkr, data.exchange_rate),
                share_of_grand=share,
            )
        )

    sections: list[SectionCostResult] = []
    for cat in MaterialCategory:
        lines = section_map[cat]
        if not lines:
            continue
        waste_total = sum((l.waste_amount for l in lines), ZERO).quantize(FOUR)
        pkr_total = sum((l.line_pkr for l in lines), ZERO).quantize(FOUR)
        sections.append(
            SectionCostResult(
                category=cat,
                waste_total=waste_total,
                pkr_total=pkr_total,
                usd_total=_usd(pkr_total, data.exchange_rate),
                share_of_grand=(pkr_total / grand_pkr).quantize(FOUR)
                if grand_pkr > ZERO
                else ZERO,
                lines=tuple(lines),
            )
        )

    percent_rows = [
        PercentOverheadResult(
            name=row.name,
            pct=row.pct,
            pkr=row.pkr,
            usd=row.usd,
            share_of_grand=(row.pkr / grand_pkr).quantize(FOUR)
            if grand_pkr > ZERO
            else ZERO,
        )
        for row in percent_rows
    ]

    selling_pkr = (
        grand_pkr * (Decimal("1") + _pct_fraction(data.profit_pct))
        + data.pricing_adjustment_pkr
    ).quantize(FOUR)
    profit_pkr = (selling_pkr - grand_pkr).quantize(FOUR)

    return CostBreakdown(
        exchange_rate=data.exchange_rate,
        sections=sections,
        manufacturing_pkr=manufacturing_pkr,
        manufacturing_usd=_usd(manufacturing_pkr, data.exchange_rate),
        percent_overheads=percent_rows,
        percent_overheads_pkr=percent_overheads_pkr,
        percent_overheads_usd=_usd(percent_overheads_pkr, data.exchange_rate),
        fixed_logistic_pkr=fixed_logistic,
        fixed_other_pkr=fixed_other,
        fixed_extras_pkr=fixed_extras_pkr,
        fixed_extras_usd=_usd(fixed_extras_pkr, data.exchange_rate),
        grand_total_pkr=grand_pkr,
        grand_total_usd=grand_usd,
        selling_price_pkr=selling_pkr,
        selling_price_usd=_usd(selling_pkr, data.exchange_rate),
        profit_pkr=profit_pkr,
    )
