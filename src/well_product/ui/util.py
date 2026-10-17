from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QTableWidget, QVBoxLayout, QWidget


@dataclass(frozen=True)
class MaterialOption:
    id: int
    name: str
    unit: str
    rate: Decimal


def parse_decimal(text: str, default: Decimal | None = None) -> Decimal | None:
    cleaned = text.strip().replace(",", "")
    if not cleaned:
        return default
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


def format_decimal(value: Decimal, places: int = 4) -> str:
    q = Decimal("1").scaleb(-places)
    return f"{value.quantize(q):f}"


def configure_data_table(
    table: QTableWidget,
    *,
    row_height: int = 44,
    compact: bool = False,
) -> None:
    """Shared table chrome: readable rows, no grid noise, hidden row numbers."""
    table.setAlternatingRowColors(True)
    table.setShowGrid(False)
    table.setWordWrap(False)
    table.verticalHeader().setVisible(False)
    table.verticalHeader().setDefaultSectionSize(row_height)
    table.horizontalHeader().setHighlightSections(False)
    table.horizontalHeader().setStretchLastSection(True)
    table.setSelectionBehavior(table.SelectionBehavior.SelectRows)
    table.setSelectionMode(table.SelectionMode.SingleSelection)
    table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    table.setProperty("class", "data-table")
    if compact:
        table.setProperty("class", "data-table compact")


def build_page_header(title: str, subtitle: str | None = None) -> QWidget:
    """Title + optional muted subtitle for list pages."""
    wrap = QWidget()
    layout = QVBoxLayout(wrap)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(4)
    title_lbl = QLabel(title)
    title_lbl.setProperty("class", "title")
    layout.addWidget(title_lbl)
    if subtitle:
        sub = QLabel(subtitle)
        sub.setProperty("class", "subtitle")
        sub.setWordWrap(True)
        layout.addWidget(sub)
    return wrap


def table_row_search_text(table: QTableWidget, row: int) -> str:
    parts: list[str] = []
    for col in range(table.columnCount()):
        item = table.item(row, col)
        if item is not None:
            parts.append(item.text())
    return " ".join(parts).lower()


def apply_table_search_filter(table: QTableWidget, query: str) -> None:
    needle = query.strip().lower()
    for row in range(table.rowCount()):
        if not needle:
            table.setRowHidden(row, False)
            continue
        haystack = table_row_search_text(table, row)
        table.setRowHidden(row, needle not in haystack)


def build_toolbar(*buttons: QWidget, trailing: QWidget | None = None) -> QWidget:
    """Horizontal action bar with primary actions left, optional control right."""
    bar = QWidget()
    bar.setProperty("class", "toolbar")
    layout = QHBoxLayout(bar)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(10)
    for btn in buttons:
        layout.addWidget(btn)
    layout.addStretch()
    if trailing is not None:
        layout.addWidget(trailing)
    return bar
