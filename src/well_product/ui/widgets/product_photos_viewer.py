from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from well_product.ui.styles import APP_STYLE


@dataclass(frozen=True)
class PhotoViewEntry:
    label: str
    path: Path


class _PreviewPane(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("PhotoPreviewPane")
        self._source: QPixmap | None = None
        self._caption = QLabel("")
        self._caption.setProperty("class", "slot-title")
        self._caption.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._image = QLabel()
        self._image.setProperty("class", "image-preview")
        self._image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._image.setMinimumSize(520, 420)
        self._image.setText("Select a photo from the list")
        self._image.setWordWrap(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._caption)
        layout.addWidget(self._image, stretch=1)

    def resizeEvent(self, event) -> None:  # noqa: ANN001, N802
        super().resizeEvent(event)
        self._apply_scale()

    def set_photo(self, entry: PhotoViewEntry | None) -> None:
        if entry is None:
            self._source = None
            self._caption.setText("")
            self._image.setPixmap(QPixmap())
            self._image.setText("Select a photo from the list")
            return
        pix = QPixmap(str(entry.path))
        if pix.isNull():
            self._source = None
            self._caption.setText(entry.label)
            self._image.setPixmap(QPixmap())
            self._image.setText("Could not load this image.")
            return
        self._source = pix
        self._caption.setText(f"{entry.label} · {entry.path.name}")
        self._image.setText("")
        self._apply_scale()

    def _apply_scale(self) -> None:
        if self._source is None or self._source.isNull():
            return
        margin = 24
        target = QSize(
            max(200, self._image.width() - margin),
            max(200, self._image.height() - margin),
        )
        scaled = self._source.scaled(
            target,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._image.setPixmap(scaled)


class ProductPhotosViewerDialog(QDialog):
    """Large preview of front, back, and extra photos for one product."""

    def __init__(
        self,
        *,
        product_name: str,
        entries: list[PhotoViewEntry],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setStyleSheet(APP_STYLE)
        self.setWindowTitle(f"Photos — {product_name}")
        self.setMinimumSize(920, 640)
        self.resize(1024, 720)

        self._entries = entries
        self._preview = _PreviewPane()

        self._list = QListWidget()
        self._list.setIconSize(QSize(72, 72))
        self._list.setMinimumWidth(220)
        self._list.setMaximumWidth(280)
        self._list.currentRowChanged.connect(self._on_selection)

        for entry in entries:
            item = QListWidgetItem(entry.label)
            item.setToolTip(str(entry.path))
            pix = QPixmap(str(entry.path))
            if not pix.isNull():
                thumb = pix.scaled(
                    72,
                    72,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                item.setIcon(QIcon(thumb))
            self._list.addItem(item)

        prev_btn = QPushButton("Previous")
        prev_btn.setProperty("class", "secondary")
        next_btn = QPushButton("Next")
        next_btn.setProperty("class", "secondary")
        close_btn = QPushButton("Close")
        prev_btn.clicked.connect(self._prev)
        next_btn.clicked.connect(self._next)
        close_btn.clicked.connect(self.accept)

        nav = QHBoxLayout()
        nav.addWidget(prev_btn)
        nav.addWidget(next_btn)
        nav.addStretch()
        nav.addWidget(close_btn)

        if not entries:
            empty = QLabel("This product has no photos yet.\nEdit the product to add front, back, or extra images.")
            empty.setProperty("class", "hint")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setWordWrap(True)
            body = QVBoxLayout()
            body.addWidget(empty, stretch=1)
            body.addLayout(nav)
            root = QVBoxLayout(self)
            root.addLayout(body)
            return

        body = QHBoxLayout()
        body.setSpacing(16)
        body.addWidget(self._list)
        body.addWidget(self._preview, stretch=1)

        root = QVBoxLayout(self)
        root.addLayout(body, stretch=1)
        root.addLayout(nav)
        self._list.setCurrentRow(0)

    def _on_selection(self, row: int) -> None:
        if row < 0 or row >= len(self._entries):
            self._preview.set_photo(None)
            return
        self._preview.set_photo(self._entries[row])

    def _prev(self) -> None:
        if self._list.count() == 0:
            return
        row = self._list.currentRow()
        self._list.setCurrentRow((row - 1) % self._list.count())

    def _next(self) -> None:
        if self._list.count() == 0:
            return
        row = self._list.currentRow()
        self._list.setCurrentRow((row + 1) % self._list.count())
