from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QHeaderView,
    QInputDialog,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from sqlalchemy.engine import Engine

from well_product.database import session_scope
from well_product.services import product_images as image_service
from well_product.services import products as product_service
from well_product.ui.util import (
    apply_table_search_filter,
    build_page_header,
    build_toolbar,
    configure_data_table,
    format_decimal,
)
from well_product.ui.widgets.product_editor import ProductEditorDialog
from well_product.ui.widgets.product_photos_viewer import (
    PhotoViewEntry,
    ProductPhotosViewerDialog,
)
from well_product.units import ProductImageKind


def _photo_entries_for_product(product) -> list[PhotoViewEntry]:  # noqa: ANN001
    entries: list[PhotoViewEntry] = []
    kind_labels = {
        ProductImageKind.FRONT.value: "Front",
        ProductImageKind.BACK.value: "Back",
    }
    extras: list[tuple[int, PhotoViewEntry]] = []
    for img in product.images:
        path = image_service.resolve_absolute(img.relative_path)
        if not path.is_file():
            continue
        if img.kind == ProductImageKind.EXTRA.value:
            order = img.sort_order or 0
            extras.append(
                (
                    order,
                    PhotoViewEntry(label=f"Extra {order or len(extras) + 1}", path=path),
                )
            )
        else:
            label = kind_labels.get(img.kind, img.kind.title())
            entries.append(PhotoViewEntry(label=label, path=path))
    extras.sort(key=lambda t: t[0])
    entries.extend(e for _, e in extras)
    return entries


class ProductsPage(QWidget):
    def __init__(self, engine: Engine, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._engine = engine
        self._search_query = ""
        self._table = QTableWidget(0, 6)
        self._table.setHorizontalHeaderLabels(
            [
                "Photo",
                "Name",
                "Article",
                "Customer",
                "Grand total PKR",
                "Grand total USD",
            ]
        )
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        configure_data_table(self._table, row_height=56)
        self._table.setIconSize(QSize(52, 52))
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(0, 72)
        self._table.doubleClicked.connect(self._on_row_double_click)

        new_btn = QPushButton("New product")
        photos_btn = QPushButton("View photos")
        photos_btn.setProperty("class", "secondary")
        edit_btn = QPushButton("Edit")
        copy_btn = QPushButton("Copy from…")
        delete_btn = QPushButton("Delete")
        delete_btn.setProperty("class", "danger")
        refresh_btn = QPushButton("Refresh")
        new_btn.clicked.connect(self._new)
        photos_btn.clicked.connect(self._view_photos)
        edit_btn.clicked.connect(self._edit)
        copy_btn.clicked.connect(self._copy)
        delete_btn.clicked.connect(self._delete)
        refresh_btn.clicked.connect(self.refresh)

        toolbar = build_toolbar(
            new_btn,
            photos_btn,
            edit_btn,
            copy_btn,
            delete_btn,
            trailing=refresh_btn,
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 28)
        layout.setSpacing(8)
        layout.addWidget(
            build_page_header(
                "Products & costing",
                "Double-click a row to edit, or double-click the Photo cell to view all images.",
            )
        )
        layout.addWidget(toolbar)
        layout.addWidget(self._table, stretch=1)
        self.refresh()

    def refresh(self) -> None:
        with session_scope(self._engine) as session:
            products = product_service.list_products(session)
            rows_data = []
            for p in products:
                try:
                    cost = product_service.compute_product_cost(p)
                    grand_pkr = format_decimal(cost.grand_total_pkr, 2)
                    grand_usd = format_decimal(cost.grand_total_usd, 2)
                except ValueError:
                    grand_pkr = "—"
                    grand_usd = "—"
                front_path = None
                photo_count = 0
                for img in p.images:
                    candidate = image_service.resolve_absolute(img.relative_path)
                    if candidate.is_file():
                        photo_count += 1
                        if img.kind == ProductImageKind.FRONT.value:
                            front_path = candidate
                rows_data.append(
                    (
                        p.id,
                        front_path,
                        photo_count,
                        p.name,
                        p.article_no or "",
                        p.customer.name if p.customer else "",
                        grand_pkr,
                        grand_usd,
                    )
                )
        self._table.setRowCount(0)
        for pid, front, photo_count, name, article, customer, pkr, usd in rows_data:
            row = self._table.rowCount()
            self._table.insertRow(row)
            photo_item = QTableWidgetItem()
            photo_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if photo_count == 0:
                photo_item.setText("—")
                photo_item.setToolTip("No photos — edit product to add")
            else:
                if front is not None:
                    pix = QPixmap(str(front))
                    if not pix.isNull():
                        scaled = pix.scaled(
                            52,
                            52,
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation,
                        )
                        photo_item.setIcon(QIcon(scaled))
                extra = photo_count - 1
                if extra > 0:
                    photo_item.setText(f"+{extra}")
                photo_item.setToolTip(
                    f"{photo_count} photo(s) — double-click to view"
                )
            photo_item.setData(Qt.ItemDataRole.UserRole, pid)
            self._table.setItem(row, 0, photo_item)
            name_item = QTableWidgetItem(name)
            name_item.setData(Qt.ItemDataRole.UserRole, pid)
            self._table.setItem(row, 1, name_item)
            self._table.setItem(row, 2, QTableWidgetItem(article))
            self._table.setItem(row, 3, QTableWidgetItem(customer))
            self._table.setItem(row, 4, QTableWidgetItem(pkr))
            self._table.setItem(row, 5, QTableWidgetItem(usd))
        self.apply_search(self._search_query)

    def apply_search(self, query: str) -> None:
        self._search_query = query
        apply_table_search_filter(self._table, query)

    def _selected_id(self) -> int | None:
        rows = self._table.selectionModel().selectedRows()
        if not rows:
            return None
        item = self._table.item(rows[0].row(), 1)
        if item is None:
            return None
        return item.data(Qt.ItemDataRole.UserRole)

    def _open_editor(
        self,
        *,
        product_id: int | None = None,
        clone_from_id: int | None = None,
    ) -> None:
        product = None
        clone_from = None
        with session_scope(self._engine) as session:
            if product_id is not None:
                product = product_service.get_product(session, product_id)
            if clone_from_id is not None:
                clone_from = product_service.get_product(session, clone_from_id)
        dialog = ProductEditorDialog(
            self._engine,
            product=product,
            clone_from=clone_from if product is None else None,
            parent=self,
        )
        if dialog.exec() == dialog.DialogCode.Accepted:
            self.refresh()

    def _new(self) -> None:
        self._open_editor()

    def _on_row_double_click(self, index) -> None:  # noqa: ANN001
        if index.column() == 0:
            self._view_photos()
        else:
            self._edit()

    def _view_photos(self) -> None:
        product_id = self._selected_id()
        if product_id is None:
            QMessageBox.information(self, "Photos", "Select a product first.")
            return
        with session_scope(self._engine) as session:
            product = product_service.get_product(session, product_id)
            if product is None:
                self.refresh()
                return
            name = product.name
            entries = _photo_entries_for_product(product)
        dialog = ProductPhotosViewerDialog(
            product_name=name,
            entries=entries,
            parent=self,
        )
        dialog.exec()

    def _edit(self) -> None:
        product_id = self._selected_id()
        if product_id is None:
            QMessageBox.information(self, "Edit", "Select a product first.")
            return
        self._open_editor(product_id=product_id)

    def _copy(self) -> None:
        source_id = self._selected_id()
        if source_id is None:
            QMessageBox.information(self, "Copy", "Select a product to copy from.")
            return
        name, ok = QInputDialog.getText(self, "Copy product", "New product name:")
        if not ok or not name.strip():
            return
        article, ok2 = QInputDialog.getText(self, "Copy product", "New article no.:")
        if not ok2:
            return
        with session_scope(self._engine) as session:
            source = product_service.get_product(session, source_id)
            if source is None:
                self.refresh()
                return
            try:
                clone = product_service.duplicate_product(
                    session,
                    source,
                    name=name.strip(),
                    article_no=article.strip() or None,
                    customer_id=source.customer_id,
                )
                clone_id = clone.id
            except Exception as exc:  # noqa: BLE001
                QMessageBox.critical(self, "Copy failed", str(exc))
                return
        self._open_editor(product_id=clone_id)

    def _delete(self) -> None:
        product_id = self._selected_id()
        if product_id is None:
            QMessageBox.information(self, "Delete", "Select a product first.")
            return
        if (
            QMessageBox.question(self, "Confirm", "Delete this product?")
            != QMessageBox.StandardButton.Yes
        ):
            return
        try:
            with session_scope(self._engine) as session:
                product = product_service.get_product(session, product_id)
                if product:
                    product_service.delete_product(session, product)
            self.refresh()
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Error", str(exc))
