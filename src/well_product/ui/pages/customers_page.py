from __future__ import annotations

from PySide6.QtWidgets import (
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
from well_product.services import customers as customer_service
from well_product.ui.styles import APP_STYLE
from well_product.ui.util import (
    apply_table_search_filter,
    build_page_header,
    build_toolbar,
    configure_data_table,
)


class CustomerDialog(QDialog):
    def __init__(
        self,
        *,
        name: str = "",
        email: str = "",
        phone: str = "",
        company: str = "",
        address: str = "",
        notes: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setStyleSheet(APP_STYLE)
        self.setWindowTitle("Edit customer" if name else "Add customer")
        self._name = QLineEdit(name)
        self._email = QLineEdit(email)
        self._phone = QLineEdit(phone)
        self._company = QLineEdit(company)
        self._address = QPlainTextEdit(address)
        self._address.setMaximumHeight(60)
        self._notes = QPlainTextEdit(notes)
        self._notes.setMaximumHeight(60)

        form = QFormLayout()
        form.addRow("Name *", self._name)
        form.addRow("Email", self._email)
        form.addRow("Phone", self._phone)
        form.addRow("Company", self._company)
        form.addRow("Address", self._address)
        form.addRow("Notes", self._notes)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def values(self) -> dict | None:
        name = self._name.text().strip()
        if not name:
            return None
        return {
            "name": name,
            "email": self._email.text().strip() or None,
            "phone": self._phone.text().strip() or None,
            "company": self._company.text().strip() or None,
            "address": self._address.toPlainText().strip() or None,
            "notes": self._notes.toPlainText().strip() or None,
        }


class CustomersPage(QWidget):
    def __init__(self, engine: Engine, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._engine = engine
        self._search_query = ""
        self._table = QTableWidget(0, 5)
        self._table.setHorizontalHeaderLabels(
            ["Name", "Company", "Email", "Phone", "Notes"]
        )
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        configure_data_table(self._table)

        add_btn = QPushButton("Add customer")
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
                "Customers",
                "Buyers and contacts linked to your costing worksheets.",
            )
        )
        layout.addWidget(toolbar)
        layout.addWidget(self._table, stretch=1)
        self.refresh()

    def refresh(self) -> None:
        with session_scope(self._engine) as session:
            rows = [
                (c.id, c.name, c.company or "", c.email or "", c.phone or "", c.notes or "")
                for c in customer_service.list_customers(session)
            ]
        self._table.setRowCount(0)
        for cid, name, company, email, phone, notes in rows:
            row = self._table.rowCount()
            self._table.insertRow(row)
            self._table.setItem(row, 0, QTableWidgetItem(name))
            self._table.setItem(row, 1, QTableWidgetItem(company))
            self._table.setItem(row, 2, QTableWidgetItem(email))
            self._table.setItem(row, 3, QTableWidgetItem(phone))
            self._table.setItem(row, 4, QTableWidgetItem(notes))
            self._table.item(row, 0).setData(256, cid)
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
        dialog = CustomerDialog(parent=self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        values = dialog.values()
        if values is None:
            QMessageBox.warning(self, "Validation", "Customer name is required.")
            return
        try:
            with session_scope(self._engine) as session:
                customer_service.create_customer(session, **values)
            self.refresh()
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Error", str(exc))

    def _edit(self) -> None:
        customer_id = self._selected_id()
        if customer_id is None:
            QMessageBox.information(self, "Edit", "Select a customer first.")
            return
        with session_scope(self._engine) as session:
            customer = customer_service.get_customer(session, customer_id)
            if customer is None:
                self.refresh()
                return
            initial = {
                "name": customer.name,
                "email": customer.email or "",
                "phone": customer.phone or "",
                "company": customer.company or "",
                "address": customer.address or "",
                "notes": customer.notes or "",
            }
        dialog = CustomerDialog(**initial, parent=self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        values = dialog.values()
        if values is None:
            QMessageBox.warning(self, "Validation", "Customer name is required.")
            return
        try:
            with session_scope(self._engine) as session:
                cust = customer_service.get_customer(session, customer_id)
                assert cust is not None
                customer_service.update_customer(session, cust, **values)
            self.refresh()
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Error", str(exc))

    def _delete(self) -> None:
        customer_id = self._selected_id()
        if customer_id is None:
            QMessageBox.information(self, "Delete", "Select a customer first.")
            return
        if (
            QMessageBox.question(self, "Confirm", "Delete this customer?")
            != QMessageBox.StandardButton.Yes
        ):
            return
        try:
            with session_scope(self._engine) as session:
                customer = customer_service.get_customer(session, customer_id)
                if customer:
                    customer_service.delete_customer(session, customer)
            self.refresh()
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Error", str(exc))
