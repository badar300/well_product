from __future__ import annotations

from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from well_product.costing.engine import CostBreakdown
from well_product.ui.util import format_decimal
from well_product.units import MaterialCategory


# Scoped styles — avoids global APP_STYLE fighting label backgrounds on macOS.
COST_SUMMARY_STYLE = """
#CostSummaryPanel, #summaryShell, #summaryShell QLabel {
    background: transparent;
    border: none;
}
#summaryShell {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 14px;
}
#summaryHeading {
    color: #0f172a;
    font-size: 17px;
    font-weight: 700;
}
#summarySub {
    color: #64748b;
    font-size: 12px;
}
#summaryDivider {
    background-color: #e2e8f0;
    max-height: 1px;
    min-height: 1px;
    border: none;
}
#summaryRowTitle {
    color: #64748b;
    font-size: 11px;
    font-weight: 600;
}
#summaryRowPrimary {
    color: #0f172a;
    font-size: 18px;
    font-weight: 700;
}
#summaryRowSecondary {
    color: #475569;
    font-size: 12px;
}
#summaryBreakdownBox {
    background-color: #f1f5f9;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
}
#summaryBreakdownTitle {
    color: #475569;
    font-size: 11px;
    font-weight: 600;
}
#summaryBreakdownBody {
    color: #1e293b;
    font-size: 12px;
    line-height: 1.45;
}
#heroGrand, #heroGrand QLabel {
    background: transparent;
    border: none;
}
#heroGrand {
    background-color: #4f46e5;
    border-radius: 12px;
}
#heroSelling, #heroSelling QLabel {
    background: transparent;
    border: none;
}
#heroSelling {
    background-color: #0f766e;
    border-radius: 12px;
}
#heroTitle {
    color: #e0e7ff;
    font-size: 11px;
    font-weight: 600;
}
#heroSelling #heroTitle {
    color: #ccfbf1;
}
#heroPkr {
    color: #ffffff;
    font-size: 22px;
    font-weight: 700;
}
#heroUsd {
    color: #f8fafc;
    font-size: 14px;
    font-weight: 600;
}
#heroFoot {
    color: #ecfdf5;
    font-size: 12px;
}
#heroGrand #heroFoot {
    color: #e0e7ff;
}
"""


def _row_block(title: str) -> tuple[QLabel, QLabel, QLabel]:
    t = QLabel(title)
    t.setObjectName("summaryRowTitle")
    primary = QLabel("—")
    primary.setObjectName("summaryRowPrimary")
    secondary = QLabel("")
    secondary.setObjectName("summaryRowSecondary")
    secondary.setWordWrap(True)
    return t, primary, secondary


class CostSummaryPanel(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("CostSummaryPanel")
        self.setStyleSheet(COST_SUMMARY_STYLE)

        shell = QFrame()
        shell.setObjectName("summaryShell")

        heading = QLabel("Live cost summary")
        heading.setObjectName("summaryHeading")
        sub = QLabel("Updates as you edit BOM, rates, and overheads.")
        sub.setObjectName("summarySub")
        sub.setWordWrap(True)

        div1 = QFrame()
        div1.setObjectName("summaryDivider")
        div1.setFixedHeight(1)

        self._mfg_t, self._mfg_p, self._mfg_s = _row_block("Manufacturing")
        self._oh_t, self._oh_p, self._oh_s = _row_block("Percent overheads")
        self._fix_t, self._fix_p, self._fix_s = _row_block("Fixed extras")

        breakdown_box = QFrame()
        breakdown_box.setObjectName("summaryBreakdownBox")
        bd_title = QLabel("By section")
        bd_title.setObjectName("summaryBreakdownTitle")
        self._sections = QLabel("—")
        self._sections.setObjectName("summaryBreakdownBody")
        self._sections.setWordWrap(True)
        bd_layout = QVBoxLayout(breakdown_box)
        bd_layout.setContentsMargins(12, 10, 12, 10)
        bd_layout.setSpacing(6)
        bd_layout.addWidget(bd_title)
        bd_layout.addWidget(self._sections)

        self._grand = QFrame()
        self._grand.setObjectName("heroGrand")
        self._grand_title = QLabel("Grand total")
        self._grand_title.setObjectName("heroTitle")
        self._grand_pkr = QLabel("—")
        self._grand_pkr.setObjectName("heroPkr")
        self._grand_usd = QLabel("")
        self._grand_usd.setObjectName("heroUsd")
        grand_layout = QVBoxLayout(self._grand)
        grand_layout.setContentsMargins(14, 12, 14, 12)
        grand_layout.setSpacing(4)
        grand_layout.addWidget(self._grand_title)
        grand_layout.addWidget(self._grand_pkr)
        grand_layout.addWidget(self._grand_usd)

        self._selling = QFrame()
        self._selling.setObjectName("heroSelling")
        self._sell_title = QLabel("Selling price")
        self._sell_title.setObjectName("heroTitle")
        self._sell_pkr = QLabel("—")
        self._sell_pkr.setObjectName("heroPkr")
        self._sell_usd = QLabel("")
        self._sell_usd.setObjectName("heroUsd")
        self._sell_foot = QLabel("")
        self._sell_foot.setObjectName("heroFoot")
        sell_layout = QVBoxLayout(self._selling)
        sell_layout.setContentsMargins(14, 12, 14, 12)
        sell_layout.setSpacing(4)
        sell_layout.addWidget(self._sell_title)
        sell_layout.addWidget(self._sell_pkr)
        sell_layout.addWidget(self._sell_usd)
        sell_layout.addWidget(self._sell_foot)

        def add_row(layout: QVBoxLayout, t: QLabel, p: QLabel, s: QLabel) -> None:
            layout.addWidget(t)
            layout.addWidget(p)
            layout.addWidget(s)

        inner = QVBoxLayout(shell)
        inner.setContentsMargins(16, 16, 16, 16)
        inner.setSpacing(10)
        inner.addWidget(heading)
        inner.addWidget(sub)
        inner.addWidget(div1)
        add_row(inner, self._mfg_t, self._mfg_p, self._mfg_s)
        add_row(inner, self._oh_t, self._oh_p, self._oh_s)
        add_row(inner, self._fix_t, self._fix_p, self._fix_s)
        inner.addWidget(breakdown_box)
        inner.addWidget(self._grand)
        inner.addWidget(self._selling)
        inner.addStretch()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(shell)

    def set_breakdown(self, breakdown: CostBreakdown | None) -> None:
        if breakdown is None:
            for p, s in (
                (self._mfg_p, self._mfg_s),
                (self._oh_p, self._oh_s),
                (self._fix_p, self._fix_s),
            ):
                p.setText("—")
                s.setText("")
                s.hide()
            self._sections.setText("—")
            self._grand_pkr.setText("—")
            self._grand_usd.setText("")
            self._sell_pkr.setText("—")
            self._sell_usd.setText("")
            self._sell_foot.setText("")
            self._sell_foot.hide()
            return

        self._mfg_p.setText(f"{format_decimal(breakdown.manufacturing_pkr, 2)} PKR")
        self._mfg_s.setText(f"{format_decimal(breakdown.manufacturing_usd, 2)} USD")
        self._mfg_s.show()

        oh_parts = [
            f"{row.name} {format_decimal(row.pkr, 2)}"
            for row in breakdown.percent_overheads
            if row.pkr
        ]
        self._oh_p.setText(f"{format_decimal(breakdown.percent_overheads_pkr, 2)} PKR")
        oh_meta = ", ".join(oh_parts) if oh_parts else f"{format_decimal(breakdown.percent_overheads_usd, 2)} USD"
        self._oh_s.setText(oh_meta)
        self._oh_s.setVisible(bool(oh_meta))

        self._fix_p.setText(f"{format_decimal(breakdown.fixed_extras_pkr, 2)} PKR")
        self._fix_s.setText(
            f"Logistic {format_decimal(breakdown.fixed_logistic_pkr, 2)} · "
            f"Other {format_decimal(breakdown.fixed_other_pkr, 2)}"
        )
        self._fix_s.show()

        section_lines = []
        for sec in breakdown.sections:
            cat = sec.category
            label = (
                cat.name.replace("_", " ").title()
                if isinstance(cat, MaterialCategory)
                else str(cat).replace("_", " ").title()
            )
            section_lines.append(
                f"{label}: {format_decimal(sec.pkr_total, 2)} PKR "
                f"({format_decimal(sec.share_of_grand * 100, 1)}%)"
            )
        self._sections.setText(
            "\n".join(section_lines) if section_lines else "No BOM lines yet"
        )

        self._grand_pkr.setText(f"{format_decimal(breakdown.grand_total_pkr, 2)} PKR")
        self._grand_usd.setText(f"{format_decimal(breakdown.grand_total_usd, 2)} USD")
        self._sell_pkr.setText(f"{format_decimal(breakdown.selling_price_pkr, 2)} PKR")
        self._sell_usd.setText(f"{format_decimal(breakdown.selling_price_usd, 2)} USD")
        self._sell_foot.setText(f"Profit {format_decimal(breakdown.profit_pkr, 2)} PKR")
        self._sell_foot.show()
