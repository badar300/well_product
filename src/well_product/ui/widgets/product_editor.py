from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QTabWidget,
    QScrollArea,
    QTableWidget,
    QVBoxLayout,
    QWidget,
)

from sqlalchemy.engine import Engine

from well_product.costing.engine import (
    BomLineInput,
    ExtraCostInput,
    ProductCostInput,
    calculate_product_cost,
)
from well_product.database import session_scope
from well_product.models import Product, ProductImage
from well_product.services import customers as customer_service
from well_product.services import materials as material_service
from well_product.services import product_images as image_service
from well_product.services import products as product_service
from well_product.ui.styles import APP_STYLE
from well_product.ui.util import MaterialOption, configure_data_table, parse_decimal
from well_product.ui.widgets.cost_summary import CostSummaryPanel
from well_product.ui.widgets.product_image_panel import (
    ExtraImageEntry,
    ProductImagePanel,
)
from well_product.units import CostingMode, ExtraCostKind, MaterialCategory, ProductImageKind


class ProductEditorDialog(QDialog):
    saved = Signal(int)

    def __init__(
        self,
        engine: Engine,
        *,
        product: Product | None = None,
        clone_from: Product | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._engine = engine
        self._product = product
        self._clone_from = clone_from
        self._materials: list[MaterialOption] = []
        self._original_extra_entries: list[ExtraImageEntry] = []
        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(300)
        self._debounce.timeout.connect(self._refresh_cost_preview)

        self.setWindowTitle("Edit product" if product else "New product")
        self.setMinimumSize(1280, 850)
        self.resize(1280, 850)
        self.setStyleSheet(APP_STYLE)

        self._name = QLineEdit()
        self._article = QLineEdit()
        self._customer = QComboBox()
        self._note = QPlainTextEdit()
        self._note.setMaximumHeight(70)
        self._image_panel = ProductImagePanel()
        self._exchange = QDoubleSpinBox()
        self._exchange.setRange(0.0001, 1_000_000)
        self._exchange.setDecimals(4)
        self._exchange.setValue(277.0)
        self._mode = QComboBox()
        for mode in CostingMode:
            self._mode.addItem(mode.value.upper(), mode.value)

        self._pct_fields: dict[str, QDoubleSpinBox] = {}
        for key in (
            "production_loss_pct",
            "government_tax_pct",
            "commission_pct",
            "factory_overhead_pct",
            "profit_pct",
        ):
            spin = QDoubleSpinBox()
            spin.setRange(0, 100)
            spin.setDecimals(2)
            spin.setSingleStep(1)
            spin.setToolTip("Whole percent (e.g. 7 for 7%)")
            self._pct_fields[key] = spin

        self._pricing_adj = QDoubleSpinBox()
        self._pricing_adj.setRange(-1_000_000, 1_000_000)
        self._pricing_adj.setDecimals(2)

        self._bom_tables: dict[MaterialCategory, QTableWidget] = {}
        self._extras_table = QTableWidget(0, 3)
        self._extras_table.setHorizontalHeaderLabels(["Kind", "Name", "Amount PKR"])
        configure_data_table(self._extras_table, row_height=40, compact=True)

        self._summary = CostSummaryPanel()
        self._build_ui()
        self._load_reference_data()
        self._populate_from_source(product or clone_from)
        self._wire_change_handlers()
        self._refresh_cost_preview()

    def _build_ui(self) -> None:
        main_tabs = QTabWidget()

        # --- Overview ---
        overview = QWidget()
        overview_tab = QVBoxLayout(overview)
        overview_tab.setContentsMargins(0, 0, 0, 0)

        overview_scroll = QScrollArea()
        overview_scroll.setWidgetResizable(True)
        overview_scroll.setFrameShape(QFrame.Shape.NoFrame)
        overview_scroll.setObjectName("OverviewScroll")

        overview_inner = QWidget()
        overview_layout = QVBoxLayout(overview_inner)
        overview_layout.setSpacing(18)
        overview_layout.setContentsMargins(4, 4, 12, 12)

        details_box = QGroupBox("Product details")
        details_box.setProperty("class", "overview-section")
        details_grid = QGridLayout(details_box)
        details_grid.setHorizontalSpacing(16)
        details_grid.setVerticalSpacing(12)
        details_grid.addWidget(QLabel("Name *"), 0, 0, Qt.AlignmentFlag.AlignRight)
        details_grid.addWidget(self._name, 0, 1)
        details_grid.addWidget(QLabel("Article no."), 1, 0, Qt.AlignmentFlag.AlignRight)
        details_grid.addWidget(self._article, 1, 1)
        details_grid.addWidget(QLabel("Customer"), 2, 0, Qt.AlignmentFlag.AlignRight)
        details_grid.addWidget(self._customer, 2, 1)
        details_grid.setColumnStretch(1, 1)
        self._name.setMinimumHeight(36)
        self._article.setMinimumHeight(36)
        self._customer.setMinimumHeight(36)

        photos_box = QGroupBox("Photos")
        photos_box.setProperty("class", "overview-section")
        photos_layout = QVBoxLayout(photos_box)
        photos_layout.addWidget(self._image_panel)

        note_box = QGroupBox("Special note")
        note_box.setProperty("class", "overview-section")
        note_layout = QVBoxLayout(note_box)
        self._note.setMinimumHeight(72)
        self._note.setMaximumHeight(120)
        note_layout.addWidget(self._note)

        overview_layout.addWidget(details_box)
        overview_layout.addWidget(photos_box)
        overview_layout.addWidget(note_box)
        overview_layout.addStretch()

        overview_scroll.setWidget(overview_inner)
        overview_tab.addWidget(overview_scroll)
        main_tabs.addTab(overview, "Overview")

        # --- Materials (scroll + group boxes — QToolBox tabs break under QSS on macOS)
        materials = QWidget()
        materials_layout = QVBoxLayout(materials)
        materials_layout.setContentsMargins(0, 0, 0, 0)

        materials_hint = QLabel(
            "Bill of materials by category. Each section scrolls independently below."
        )
        materials_hint.setProperty("class", "hint")
        materials_hint.setWordWrap(True)

        bom_scroll = QScrollArea()
        bom_scroll.setWidgetResizable(True)
        bom_scroll.setFrameShape(QFrame.Shape.NoFrame)
        bom_scroll.setObjectName("MaterialBomScroll")

        bom_inner = QWidget()
        bom_sections = QVBoxLayout(bom_inner)
        bom_sections.setSpacing(16)
        bom_sections.setContentsMargins(4, 4, 8, 12)

        for cat in MaterialCategory:
            title = cat.name.replace("_", " ").title()
            section = QGroupBox(title)
            section.setProperty("class", "bom-section")
            table = QTableWidget(0, 5)
            table.setHorizontalHeaderLabels(
                ["Material", "Avg qty", "Waste %", "Rate override", ""]
            )
            table.setMinimumHeight(160)
            configure_data_table(table, row_height=40, compact=True)
            add_btn = QPushButton(f"Add {title} line")
            add_btn.clicked.connect(lambda _=False, c=cat: self._add_bom_row(c))
            section_layout = QVBoxLayout(section)
            section_layout.setSpacing(10)
            section_layout.addWidget(table)
            section_layout.addWidget(add_btn)
            bom_sections.addWidget(section)
            self._bom_tables[cat] = table

        bom_sections.addStretch()
        bom_scroll.setWidget(bom_inner)
        materials_layout.addWidget(materials_hint)
        materials_layout.addWidget(bom_scroll, stretch=1)
        main_tabs.addTab(materials, "Materials")

        # --- Pricing ---
        pricing = QWidget()
        pricing_tab = QVBoxLayout(pricing)
        pricing_tab.setContentsMargins(0, 0, 0, 0)

        pricing_scroll = QScrollArea()
        pricing_scroll.setWidgetResizable(True)
        pricing_scroll.setFrameShape(QFrame.Shape.NoFrame)
        pricing_scroll.setObjectName("PricingScroll")

        pricing_inner = QWidget()
        pricing_layout = QVBoxLayout(pricing_inner)
        pricing_layout.setSpacing(18)
        pricing_layout.setContentsMargins(4, 4, 12, 12)

        def _fl(text: str) -> QLabel:
            lbl = QLabel(text)
            lbl.setProperty("class", "field-label")
            lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            return lbl

        rate_box = QGroupBox("Rates")
        rate_box.setProperty("class", "overview-section")
        rate_grid = QGridLayout(rate_box)
        rate_grid.setHorizontalSpacing(12)
        rate_grid.setVerticalSpacing(12)
        rate_grid.addWidget(_fl("Exchange rate (PKR/USD)"), 0, 0)
        rate_grid.addWidget(self._exchange, 0, 1)
        rate_grid.addWidget(_fl("Costing mode"), 0, 2)
        rate_grid.addWidget(self._mode, 0, 3)
        rate_grid.setColumnStretch(1, 1)
        rate_grid.setColumnStretch(3, 1)
        pricing_layout.addWidget(rate_box)

        oh_box = QGroupBox("Overheads & profit")
        oh_box.setProperty("class", "overview-section")
        oh_grid = QGridLayout(oh_box)
        oh_grid.setHorizontalSpacing(12)
        oh_grid.setVerticalSpacing(12)
        oh_fields = (
            ("Production loss %", "production_loss_pct"),
            ("Government tax %", "government_tax_pct"),
            ("Commission %", "commission_pct"),
            ("Factory overhead %", "factory_overhead_pct"),
            ("Profit %", "profit_pct"),
            ("Pricing adjustment PKR", None),
        )
        for row, (label, key) in enumerate(oh_fields):
            r, c = row // 2, (row % 2) * 2
            oh_grid.addWidget(_fl(label), r, c)
            widget = self._pricing_adj if key is None else self._pct_fields[key]
            oh_grid.addWidget(widget, r, c + 1)
        oh_grid.setColumnStretch(1, 1)
        oh_grid.setColumnStretch(3, 1)
        pricing_layout.addWidget(oh_box)

        policy = QLabel(
            "Suggested profit by order qty (manual): 100–1000 → 25%, "
            "1001–5000 → 20%, 5001–10000 → 15%, 10001–20000 → 10%, 20001+ → 7%"
        )
        policy.setWordWrap(True)
        policy.setProperty("class", "hint")
        policy_frame = QFrame()
        policy_frame.setProperty("class", "info-box")
        policy_layout = QVBoxLayout(policy_frame)
        policy_layout.setContentsMargins(12, 10, 12, 10)
        policy_layout.addWidget(policy)
        pricing_layout.addWidget(policy_frame)

        extras_box = QGroupBox("Fixed extras (logistic / other)")
        extras_box.setProperty("class", "overview-section")
        extras_layout = QVBoxLayout(extras_box)
        extras_layout.setSpacing(10)
        add_extra = QPushButton("Add extra cost")
        add_extra.clicked.connect(self._add_extra_row)
        extras_layout.addWidget(self._extras_table)
        extras_layout.addWidget(add_extra)
        pricing_layout.addWidget(extras_box)
        pricing_layout.addStretch()

        pricing_scroll.setWidget(pricing_inner)
        pricing_tab.addWidget(pricing_scroll)
        main_tabs.addTab(pricing, "Pricing")

        body = QHBoxLayout()
        body.addWidget(main_tabs, stretch=65)
        body.addWidget(self._summary, stretch=35)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)

        root = QVBoxLayout(self)
        root.addLayout(body)
        root.addWidget(buttons)

    def _load_reference_data(self) -> None:
        with session_scope(self._engine) as session:
            self._materials = [
                MaterialOption(
                    id=m.id,
                    name=m.name,
                    unit=m.unit,
                    rate=m.rate,
                )
                for m in material_service.list_materials(session)
            ]
            customer_rows = [
                (c.id, c.name) for c in customer_service.list_customers(session)
            ]
        self._customer.clear()
        self._customer.addItem("(None)", None)
        for cid, cname in customer_rows:
            self._customer.addItem(cname, cid)

    def _load_images_from_product(self, source: Product) -> None:
        front_path: Path | None = None
        back_path: Path | None = None
        extras: list[ExtraImageEntry] = []
        for img in sorted(source.images, key=lambda i: (i.kind, i.sort_order, i.id)):
            abs_path = image_service.resolve_absolute(img.relative_path)
            if img.kind == ProductImageKind.FRONT.value:
                front_path = abs_path if abs_path.is_file() else None
            elif img.kind == ProductImageKind.BACK.value:
                back_path = abs_path if abs_path.is_file() else None
            elif img.kind == ProductImageKind.EXTRA.value:
                if abs_path.is_file():
                    extras.append(ExtraImageEntry(image_id=img.id, path=abs_path))
        self._original_extra_entries = list(extras)
        self._image_panel.load_images(front=front_path, back=back_path, extras=extras)

    def _populate_from_source(self, source: Product | None) -> None:
        if source is None:
            self._image_panel.load_images(front=None, back=None, extras=[])
            return
        if self._product is None and self._clone_from:
            self._name.setText(f"{source.name} (copy)")
            self._article.clear()
        else:
            self._name.setText(source.name)
            self._article.setText(source.article_no or "")
        self._note.setPlainText(source.special_note or "")
        idx = self._customer.findData(source.customer_id)
        self._customer.setCurrentIndex(max(0, idx))
        self._exchange.setValue(float(source.exchange_rate))
        mode_idx = self._mode.findData(source.costing_mode)
        self._mode.setCurrentIndex(max(0, mode_idx))
        self._pct_fields["production_loss_pct"].setValue(
            float(source.production_loss_pct)
        )
        self._pct_fields["government_tax_pct"].setValue(float(source.government_tax_pct))
        self._pct_fields["commission_pct"].setValue(float(source.commission_pct))
        self._pct_fields["factory_overhead_pct"].setValue(
            float(source.factory_overhead_pct)
        )
        self._pct_fields["profit_pct"].setValue(float(source.profit_pct))
        self._pricing_adj.setValue(float(source.pricing_adjustment_pkr))

        for line in sorted(source.materials, key=lambda m: m.sort_order):
            cat = MaterialCategory(line.category)
            self._add_bom_row(
                cat,
                raw_material_id=line.raw_material_id,
                average_qty=line.average_qty,
                waste_pct=line.waste_pct,
                rate_override=line.rate_override,
            )
        for extra in sorted(source.extra_costs, key=lambda e: e.sort_order):
            self._add_extra_row(
                kind=extra.kind,
                name=extra.name,
                amount=extra.amount,
            )
        if source.images:
            self._load_images_from_product(source)
        elif self._clone_from and source.id:
            with session_scope(self._engine) as session:
                loaded = product_service.get_product(session, source.id)
            if loaded is not None and loaded.images:
                self._load_images_from_product(loaded)

    def _wire_change_handlers(self) -> None:
        self._name.textChanged.connect(self._schedule_preview)
        self._exchange.valueChanged.connect(self._schedule_preview)
        self._pricing_adj.valueChanged.connect(self._schedule_preview)
        for spin in self._pct_fields.values():
            spin.valueChanged.connect(self._schedule_preview)

    def _schedule_preview(self) -> None:
        self._debounce.start()

    def _material_combo(self, selected_id: int | None = None) -> QComboBox:
        combo = QComboBox()
        for m in self._materials:
            combo.addItem(f"{m.name} ({m.unit}) @ {m.rate}", m.id)
        if selected_id is not None:
            idx = combo.findData(selected_id)
            combo.setCurrentIndex(max(0, idx))
        combo.currentIndexChanged.connect(self._schedule_preview)
        return combo

    def _add_bom_row(
        self,
        category: MaterialCategory,
        *,
        raw_material_id: int | None = None,
        average_qty: Decimal | None = None,
        waste_pct: Decimal | None = None,
        rate_override: Decimal | None = None,
    ) -> None:
        table = self._bom_tables[category]
        row = table.rowCount()
        table.insertRow(row)
        combo = self._material_combo(raw_material_id)
        avg = QLineEdit(str(average_qty) if average_qty is not None else "1")
        waste = QLineEdit(str(waste_pct) if waste_pct is not None else "0")
        waste.setPlaceholderText("5")
        waste.setToolTip("Waste as a whole percent (e.g. 5 for 5%)")
        override = QLineEdit(
            str(rate_override) if rate_override is not None else ""
        )
        remove = QPushButton("Remove")
        remove.setProperty("class", "secondary")
        remove.clicked.connect(lambda: self._remove_table_row(table, remove))
        for w in (avg, waste, override):
            w.textChanged.connect(self._schedule_preview)
        table.setCellWidget(row, 0, combo)
        table.setCellWidget(row, 1, avg)
        table.setCellWidget(row, 2, waste)
        table.setCellWidget(row, 3, override)
        table.setCellWidget(row, 4, remove)
        self._schedule_preview()

    def _add_extra_row(
        self,
        *,
        kind: str | None = None,
        name: str = "",
        amount: Decimal | None = None,
    ) -> None:
        table = self._extras_table
        row = table.rowCount()
        table.insertRow(row)
        kind_combo = QComboBox()
        for k in ExtraCostKind:
            kind_combo.addItem(k.value.title(), k.value)
        if kind:
            idx = kind_combo.findData(kind)
            kind_combo.setCurrentIndex(max(0, idx))
        name_edit = QLineEdit(name)
        amount_edit = QLineEdit(str(amount) if amount is not None else "0")
        kind_combo.currentIndexChanged.connect(self._schedule_preview)
        name_edit.textChanged.connect(self._schedule_preview)
        amount_edit.textChanged.connect(self._schedule_preview)
        table.setCellWidget(row, 0, kind_combo)
        table.setCellWidget(row, 1, name_edit)
        table.setCellWidget(row, 2, amount_edit)
        self._schedule_preview()

    def _remove_table_row(self, table: QTableWidget, button: QPushButton) -> None:
        for r in range(table.rowCount()):
            if table.cellWidget(r, table.columnCount() - 1) is button:
                table.removeRow(r)
                break
        self._schedule_preview()

    def _collect_bom_lines(self) -> list[BomLineInput]:
        lines: list[BomLineInput] = []
        for cat, table in self._bom_tables.items():
            for r in range(table.rowCount()):
                combo = table.cellWidget(r, 0)
                avg_w = table.cellWidget(r, 1)
                waste_w = table.cellWidget(r, 2)
                override_w = table.cellWidget(r, 3)
                if not combo or not avg_w or not waste_w or not override_w:
                    continue
                material_id = combo.currentData()
                material = next((m for m in self._materials if m.id == material_id), None)
                if material is None:
                    continue
                avg = parse_decimal(avg_w.text(), Decimal("0"))
                waste = parse_decimal(waste_w.text(), Decimal("0"))
                override_text = override_w.text().strip()
                rate = (
                    parse_decimal(override_text)
                    if override_text
                    else material.rate
                )
                if avg is None or waste is None or rate is None:
                    continue
                lines.append(
                    BomLineInput(
                        label=material.name,
                        category=cat,
                        rate=rate,
                        average_qty=avg,
                        waste_pct=waste,
                    )
                )
        return lines

    def _collect_extras(self) -> list[ExtraCostInput]:
        extras: list[ExtraCostInput] = []
        table = self._extras_table
        for r in range(table.rowCount()):
            kind_w = table.cellWidget(r, 0)
            name_w = table.cellWidget(r, 1)
            amt_w = table.cellWidget(r, 2)
            if not kind_w or not name_w or not amt_w:
                continue
            amount = parse_decimal(amt_w.text(), Decimal("0"))
            if amount is None:
                continue
            name = name_w.text().strip() or "Extra"
            extras.append(
                ExtraCostInput(
                    kind=ExtraCostKind(kind_w.currentData()),
                    name=name,
                    amount=amount,
                )
            )
        return extras

    def _build_cost_input(self) -> ProductCostInput | None:
        if self._exchange.value() <= 0:
            return None
        return ProductCostInput(
            exchange_rate=Decimal(str(self._exchange.value())),
            production_loss_pct=Decimal(
                str(self._pct_fields["production_loss_pct"].value())
            ),
            government_tax_pct=Decimal(
                str(self._pct_fields["government_tax_pct"].value())
            ),
            commission_pct=Decimal(str(self._pct_fields["commission_pct"].value())),
            factory_overhead_pct=Decimal(
                str(self._pct_fields["factory_overhead_pct"].value())
            ),
            profit_pct=Decimal(str(self._pct_fields["profit_pct"].value())),
            pricing_adjustment_pkr=Decimal(str(self._pricing_adj.value())),
            bom_lines=tuple(self._collect_bom_lines()),
            extra_costs=tuple(self._collect_extras()),
        )

    def _refresh_cost_preview(self) -> None:
        data = self._build_cost_input()
        if data is None:
            self._summary.set_breakdown(None)
            return
        try:
            self._summary.set_breakdown(calculate_product_cost(data))
        except ValueError:
            self._summary.set_breakdown(None)

    def _collect_material_rows(self) -> list[dict]:
        rows: list[dict] = []
        sort = 0
        for cat in MaterialCategory:
            table = self._bom_tables[cat]
            for r in range(table.rowCount()):
                combo = table.cellWidget(r, 0)
                avg_w = table.cellWidget(r, 1)
                waste_w = table.cellWidget(r, 2)
                override_w = table.cellWidget(r, 3)
                if not combo or not avg_w or not waste_w or not override_w:
                    continue
                material_id = combo.currentData()
                if material_id is None:
                    continue
                avg = parse_decimal(avg_w.text())
                waste = parse_decimal(waste_w.text(), Decimal("0"))
                if avg is None or waste is None:
                    continue
                override_text = override_w.text().strip()
                override = parse_decimal(override_text) if override_text else None
                rows.append(
                    {
                        "raw_material_id": material_id,
                        "average_qty": avg,
                        "waste_pct": waste,
                        "category": cat.value,
                        "rate_override": override,
                        "sort_order": sort,
                    }
                )
                sort += 1
        return rows

    def _collect_extra_rows(self) -> list[dict]:
        rows: list[dict] = []
        for r in range(self._extras_table.rowCount()):
            kind_w = self._extras_table.cellWidget(r, 0)
            name_w = self._extras_table.cellWidget(r, 1)
            amt_w = self._extras_table.cellWidget(r, 2)
            if not kind_w or not name_w or not amt_w:
                continue
            amount = parse_decimal(amt_w.text())
            if amount is None:
                continue
            rows.append(
                {
                    "kind": kind_w.currentData(),
                    "name": name_w.text().strip() or "Extra",
                    "amount": amount,
                    "sort_order": r,
                }
            )
        return rows

    def _persist_images(self, session, product_id: int) -> None:
        state = self._image_panel.build_state(
            original_extras=self._original_extra_entries
        )
        if state.clear_front:
            image_service.clear_slot(session, product_id, ProductImageKind.FRONT)
        if state.clear_back:
            image_service.clear_slot(session, product_id, ProductImageKind.BACK)
        for image_id in state.removed_extra_ids:
            img = session.get(ProductImage, image_id)
            if img is not None and img.product_id == product_id:
                image_service.remove_image(session, img)
        if state.front_path is not None:
            image_service.set_slot_image(
                session, product_id, ProductImageKind.FRONT, state.front_path
            )
        if state.back_path is not None:
            image_service.set_slot_image(
                session, product_id, ProductImageKind.BACK, state.back_path
            )
        for path in state.new_extra_paths:
            image_service.add_extra_image(session, product_id, path)

    def _save(self) -> None:
        name = self._name.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation", "Product name is required.")
            return
        if self._exchange.value() <= 0:
            QMessageBox.warning(self, "Validation", "Exchange rate must be positive.")
            return

        article = self._article.text().strip() or None
        customer_id = self._customer.currentData()
        header_kwargs = dict(
            name=name,
            article_no=article,
            customer_id=customer_id,
            special_note=self._note.toPlainText().strip() or None,
            exchange_rate=Decimal(str(self._exchange.value())),
            production_loss_pct=Decimal(
                str(self._pct_fields["production_loss_pct"].value())
            ),
            government_tax_pct=Decimal(
                str(self._pct_fields["government_tax_pct"].value())
            ),
            commission_pct=Decimal(str(self._pct_fields["commission_pct"].value())),
            factory_overhead_pct=Decimal(
                str(self._pct_fields["factory_overhead_pct"].value())
            ),
            profit_pct=Decimal(str(self._pct_fields["profit_pct"].value())),
            pricing_adjustment_pkr=Decimal(str(self._pricing_adj.value())),
            costing_mode=self._mode.currentData(),
        )
        material_rows = self._collect_material_rows()
        extra_rows = self._collect_extra_rows()

        try:
            with session_scope(self._engine) as session:
                if self._product:
                    product = product_service.get_product(session, self._product.id)
                    assert product is not None
                    product_service.update_product_header(session, product, **header_kwargs)
                else:
                    product = product_service.create_product(session, **header_kwargs)
                product_service.replace_product_materials(session, product, material_rows)
                product_service.replace_product_extra_costs(session, product, extra_rows)
                self._persist_images(session, product.id)
                session.flush()
                product_id = product.id
            self.saved.emit(product_id)
            self.accept()
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Save failed", str(exc))
