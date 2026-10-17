from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from sqlalchemy.engine import Engine

from well_product.ui.pages.customers_page import CustomersPage
from well_product.ui.pages.materials_page import MaterialsPage
from well_product.ui.pages.products_page import ProductsPage
from well_product.ui.styles import APP_STYLE

_SEARCH_PLACEHOLDERS = (
    "Search materials by name, unit, rate, or notes…",
    "Search customers by name, company, email, or phone…",
    "Search products by name, article, customer, or totals…",
)


class MainWindow(QMainWindow):
    session_finished = Signal(bool)

    def __init__(self, engine: Engine) -> None:
        super().__init__()
        self._engine = engine
        self._logout_requested = False
        self.setWindowTitle("Well Product — Costing")
        self.setMinimumSize(1200, 750)
        self.resize(1320, 840)

        nav_wrap = QWidget()
        nav_layout = QVBoxLayout(nav_wrap)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(0)

        brand = QLabel("Well Product")
        brand.setProperty("class", "nav-brand")
        tagline = QLabel("Garment costing")
        tagline.setProperty("class", "nav-tagline")

        self._nav = QListWidget()
        self._nav.setObjectName("NavSidebar")
        self._nav.addItems(["Raw materials", "Customers", "Products"])
        self._nav.currentRowChanged.connect(self._on_nav_changed)

        logout = QPushButton("Log out")
        logout.setObjectName("NavLogout")
        logout.setCursor(Qt.CursorShape.PointingHandCursor)
        logout.clicked.connect(self._on_logout)

        nav_layout.addWidget(brand)
        nav_layout.addWidget(tagline)
        nav_layout.addWidget(self._nav, stretch=1)
        nav_layout.addWidget(logout)
        nav_wrap.setFixedWidth(220)

        self._search = QLineEdit()
        self._search.setObjectName("GlobalSearchBar")
        self._search.setClearButtonEnabled(True)
        self._search.textChanged.connect(self._apply_search_to_current_page)

        search_wrap = QWidget()
        search_wrap.setObjectName("GlobalSearchWrap")
        search_layout = QHBoxLayout(search_wrap)
        search_layout.setContentsMargins(20, 12, 20, 8)
        search_layout.addWidget(self._search)

        self._stack = QStackedWidget()
        self._stack.setObjectName("ContentStack")
        self._materials = MaterialsPage(engine)
        self._customers = CustomersPage(engine)
        self._products = ProductsPage(engine)
        self._stack.addWidget(self._materials)
        self._stack.addWidget(self._customers)
        self._stack.addWidget(self._products)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        content_layout.addWidget(search_wrap)
        content_layout.addWidget(self._stack, stretch=1)

        central = QWidget()
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(nav_wrap)
        layout.addWidget(content, stretch=1)
        self.setCentralWidget(central)
        self.setStyleSheet(APP_STYLE)
        self._nav.setCurrentRow(2)

    def _apply_search_to_current_page(self) -> None:
        page = self._stack.currentWidget()
        if page is not None and hasattr(page, "apply_search"):
            page.apply_search(self._search.text())

    def _update_search_placeholder(self, index: int) -> None:
        if 0 <= index < len(_SEARCH_PLACEHOLDERS):
            self._search.setPlaceholderText(_SEARCH_PLACEHOLDERS[index])

    def _on_nav_changed(self, index: int) -> None:
        if index < 0:
            return
        self._stack.setCurrentIndex(index)
        self._update_search_placeholder(index)
        page = self._stack.widget(index)
        if hasattr(page, "refresh"):
            page.refresh()
        self._apply_search_to_current_page()

    def _on_logout(self) -> None:
        self._logout_requested = True
        self.close()

    def closeEvent(self, event) -> None:
        self.session_finished.emit(self._logout_requested)
        super().closeEvent(event)
