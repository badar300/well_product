from __future__ import annotations

from decimal import Decimal

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from sqlalchemy.engine import Engine

from well_product.database import session_scope
from well_product.services import materials as material_service
from well_product.services.materials import MaterialInUseError
from well_product.ui.styles import APP_STYLE
from well_product.ui.util import (
    apply_table_search_filter,
    build_page_header,
    build_toolbar,
    configure_data_table,
    parse_decimal,
)
from well_product.units import Unit


class MaterialDialog(QDialog):
    def __init__(
        self,
        *,
        name: str = "",
        unit: str = Unit.PCS.value,
        rate: str = "",
        notes: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setStyleSheet(APP_STYLE)
        self.setWindowTitle("Edit material" if name else "Add material")
        self._name = QLineEdit(name)
        self._unit = QComboBox()
        for u in Unit:
            self._unit.addItem(u.value, u.value)
        idx = self._unit.findData(unit)
        self._unit.setCurrentIndex(max(0, idx))
        self._rate = QLineEdit(rate)
        self._notes = QPlainTextEdit(notes)
        self._notes.setMaximumHeight(80)

        form = QFormLayout()
        form.addRow("Name *", self._name)
        form.addRow("Unit", self._unit)
        form.addRow("Rate (PKR) *", self._rate)
        form.addRow("Notes", self._notes)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def values(self) -> tuple[str, str, Decimal, str | None] | None:
        name = self._name.text().strip()
        rate = parse_decimal(self._rate.text())
        if not name or rate is None:
            return None
        notes = self._notes.toPlainText().strip() or None
        return name, self._unit.currentData(), rate, notes


class MaterialsPage(QWidget):
    def __init__(self, engine: Engine, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._engine = engine
        self._search_query = ""
        self._table = QTableWidget(0, 4)
        self._table.setHorizontalHeaderLabels(["Name", "Unit", "Rate", "Notes"])
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        configure_data_table(self._table)

        add_btn = QPushButton("Add material")
        edit_btn = QPushButton("Edit")
        delete_btn = QPushButton("Delete")
        delete_btn.setProperty("class", "danger")
        refresh_btn = QPushButton("Refresh")
        add_btn.clicked.connect(self._add)
        edit_btn.clicked.connect(self._edit)
        delete_btn.clicked.connect(self._delete)
        refresh_btn.clicked.connect(self.refresh)

        toolbar = build_toolbar(add_btn, edit_btn, delete_btn, trailing=refresh_btn)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 28)
        layout.setSpacing(8)
        layout.addWidget(
            build_page_header(
                "Raw materials",
                "Catalog of fabrics, trims, and rates used in product BOM lines.",
            )
        )
        layout.addWidget(toolbar)
        layout.addWidget(self._table, stretch=1)
        self.refresh()

    def refresh(self) -> None:
        with session_scope(self._engine) as session:
            rows = [
                (m.id, m.name, m.unit, str(m.rate), m.notes or "")
                for m in material_service.list_materials(session)
            ]
        self._table.setRowCount(0)
        for mid, name, unit, rate, notes in rows:
            row = self._table.rowCount()
            self._table.insertRow(row)
            self._table.setItem(row, 0, QTableWidgetItem(name))
            self._table.setItem(row, 1, QTableWidgetItem(unit))
            self._table.setItem(row, 2, QTableWidgetItem(rate))
            self._table.setItem(row, 3, QTableWidgetItem(notes))
            self._table.item(row, 0).setData(256, mid)  # Qt.UserRole
        self.apply_search(self._search_query)

    def apply_search(self, query: str) -> None:
        self._search_query = query
        apply_table_search_filter(self._table, query)

    def _selected_id(self) -> int | None:
        rows = self._table.selectionModel().selectedRows()
        if not rows:
            return None
        item = self._table.item(rows[0].row(), 0)
        return item.data(256) if item else None

    def _add(self) -> None:
        dialog = MaterialDialog(parent=self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        values = dialog.values()
        if values is None:
            QMessageBox.warning(self, "Validation", "Name and valid rate are required.")
            return
        name, unit, rate, notes = values
        try:
            with session_scope(self._engine) as session:
                material_service.create_material(
                    session, name=name, unit=unit, rate=rate, notes=notes
                )
            self.refresh()
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Error", str(exc))

    def _edit(self) -> None:
        material_id = self._selected_id()
        if material_id is None:
            QMessageBox.information(self, "Edit", "Select a material row first.")
            return
        with session_scope(self._engine) as session:
            material = material_service.get_material(session, material_id)
            if material is None:
                self.refresh()
                return
            initial = (
                material.name,
                material.unit,
                str(material.rate),
                material.notes or "",
            )
        dialog = MaterialDialog(
            name=initial[0],
            unit=initial[1],
            rate=initial[2],
            notes=initial[3],
            parent=self,
        )
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        values = dialog.values()
        if values is None:
            QMessageBox.warning(self, "Validation", "Name and valid rate are required.")
            return
        name, unit, rate, notes = values
        try:
            with session_scope(self._engine) as session:
                mat = material_service.get_material(session, material_id)
                assert mat is not None
                material_service.update_material(
                    session, mat, name=name, unit=unit, rate=rate, notes=notes
                )
            self.refresh()
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Error", str(exc))

    def _delete(self) -> None:
        material_id = self._selected_id()
        if material_id is None:
            QMessageBox.information(self, "Delete", "Select a material row first.")
            return
        if (
            QMessageBox.question(self, "Confirm", "Delete this material?")
            != QMessageBox.StandardButton.Yes
        ):
            return
        try:
            with session_scope(self._engine) as session:
                material = material_service.get_material(session, material_id)
                if material:
                    material_service.delete_material(session, material)
            self.refresh()
        except MaterialInUseError as exc:
            QMessageBox.warning(self, "Cannot delete", str(exc))
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Error", str(exc))
