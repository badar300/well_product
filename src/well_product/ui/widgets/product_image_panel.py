from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from well_product.services.product_images import InvalidImageError, validate_image_source


@dataclass
class ExtraImageEntry:
    image_id: int | None
    path: Path


@dataclass
class ImageEditorState:
    front_path: Path | None = None
    back_path: Path | None = None
    clear_front: bool = False
    clear_back: bool = False
    new_extra_paths: list[Path] = field(default_factory=list)
    removed_extra_ids: list[int] = field(default_factory=list)
    existing_extras: list[ExtraImageEntry] = field(default_factory=list)


_IMAGE_FILTER = "Images (*.png *.jpg *.jpeg *.webp)"
_PREVIEW_SIZE = QSize(320, 200)


def _scale_pixmap(pix: QPixmap, size: QSize) -> QPixmap:
    return pix.scaled(
        size,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )


def _pick_image(parent: QWidget, title: str) -> Path | None:
    path, _ = QFileDialog.getOpenFileName(parent, title, "", _IMAGE_FILTER)
    if not path:
        return None
    try:
        return validate_image_source(Path(path))
    except InvalidImageError as exc:
        QMessageBox.warning(parent, "Invalid image", str(exc))
        return None


class _PreviewFrame(QFrame):
    clicked = Signal()

    def mousePressEvent(self, event) -> None:  # noqa: ANN001, N802
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class _ImageSlot(QFrame):
    changed = Signal()

    def __init__(self, title: str, subtitle: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setProperty("class", "upload-slot")
        self.setProperty("hasImage", False)
        self._dialog_title = title
        self._path: Path | None = None
        self._cleared = False
        self._pix: QPixmap | None = None

        title_lbl = QLabel(title)
        title_lbl.setProperty("class", "slot-title")
        sub_lbl = QLabel(subtitle)
        sub_lbl.setProperty("class", "slot-subtitle")
        sub_lbl.setWordWrap(True)

        self._preview_frame = _PreviewFrame()
        self._preview_frame.setProperty("class", "upload-preview")
        self._preview_frame.setCursor(Qt.CursorShape.PointingHandCursor)
        self._preview_frame.setFixedHeight(_PREVIEW_SIZE.height())
        self._preview_frame.clicked.connect(self._choose)

        self._empty_wrap = QWidget()
        empty_stack = QVBoxLayout(self._empty_wrap)
        empty_stack.setAlignment(Qt.AlignmentFlag.AlignCenter)
        plus = QLabel("+")
        plus.setProperty("class", "upload-plus")
        plus.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint = QLabel("Click to upload")
        hint.setProperty("class", "upload-hint")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_stack.addWidget(plus)
        empty_stack.addWidget(hint)

        self._image_lbl = QLabel()
        self._image_lbl.setProperty("class", "upload-image")
        self._image_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._preview_stack = QStackedWidget()
        self._preview_stack.setFixedHeight(_PREVIEW_SIZE.height())
        self._preview_stack.addWidget(self._empty_wrap)
        self._preview_stack.addWidget(self._image_lbl)

        preview_outer = QVBoxLayout(self._preview_frame)
        preview_outer.setContentsMargins(0, 0, 0, 0)
        preview_outer.addWidget(self._preview_stack)

        self._filename = QLabel("")
        self._filename.setProperty("class", "upload-filename")
        self._filename.setWordWrap(True)

        upload_btn = QPushButton("Upload")
        upload_btn.clicked.connect(self._choose)
        replace_btn = QPushButton("Replace")
        replace_btn.setProperty("class", "secondary")
        replace_btn.clicked.connect(self._choose)
        clear_btn = QPushButton("Remove")
        clear_btn.setProperty("class", "ghost")
        clear_btn.clicked.connect(self._clear)

        self._actions_empty = QHBoxLayout()
        self._actions_empty.addWidget(upload_btn)
        self._actions_empty.addStretch()

        self._actions_filled = QHBoxLayout()
        self._actions_filled.addWidget(replace_btn)
        self._actions_filled.addWidget(clear_btn)
        self._actions_filled.addStretch()

        self._actions_wrap = QWidget()
        actions_layout = QVBoxLayout(self._actions_wrap)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.addLayout(self._actions_empty)
        actions_layout.addLayout(self._actions_filled)

        inner = QVBoxLayout(self)
        inner.setContentsMargins(12, 12, 12, 12)
        inner.setSpacing(8)
        inner.addWidget(title_lbl)
        inner.addWidget(sub_lbl)
        inner.addWidget(self._preview_frame)
        inner.addWidget(self._filename)
        inner.addWidget(self._actions_wrap)
        self._sync_action_visibility()

    def _sync_action_visibility(self) -> None:
        has = bool(self.property("hasImage"))
        for layout in (self._actions_empty, self._actions_filled):
            for i in range(layout.count()):
                w = layout.itemAt(i).widget()
                if w:
                    w.setVisible(layout is self._actions_empty and not has or layout is self._actions_filled and has)
        self._preview_stack.setCurrentIndex(1 if has else 0)

    def _set_has_image(self, has: bool) -> None:
        self.setProperty("hasImage", has)
        self.style().unpolish(self)
        self.style().polish(self)
        self._preview_frame.setProperty("hasImage", has)
        self._preview_frame.style().unpolish(self._preview_frame)
        self._preview_frame.style().polish(self._preview_frame)
        self._sync_action_visibility()

    def _choose(self) -> None:
        validated = _pick_image(self, f"Select {self._dialog_title}")
        if validated is None:
            return
        pix = QPixmap(str(validated))
        if pix.isNull():
            QMessageBox.warning(self, "Invalid image", "Could not load this file.")
            return
        self._path = validated
        self._cleared = False
        self._pix = pix
        self._filename.setText(validated.name)
        self._apply_scale()
        self._set_has_image(True)
        self.changed.emit()

    def _clear(self) -> None:
        self._path = None
        self._cleared = True
        self._pix = None
        self._image_lbl.setPixmap(QPixmap())
        self._filename.setText("")
        self._set_has_image(False)
        self.changed.emit()

    def _apply_scale(self) -> None:
        if self._pix is None or self._pix.isNull():
            return
        self._image_lbl.setPixmap(
            _scale_pixmap(
                self._pix,
                QSize(_PREVIEW_SIZE.width() - 16, _PREVIEW_SIZE.height() - 16),
            )
        )

    def load_existing(self, path: Path | None) -> None:
        self._path = None
        self._cleared = False
        self._pix = None
        if path is None or not path.is_file():
            self._image_lbl.setPixmap(QPixmap())
            self._filename.setText("")
            self._set_has_image(False)
            return
        pix = QPixmap(str(path))
        if pix.isNull():
            self._filename.setText("Could not load image")
            self._set_has_image(False)
            return
        self._pix = pix
        self._filename.setText(path.name)
        self._apply_scale()
        self._set_has_image(True)

    def state(self) -> tuple[Path | None, bool]:
        return self._path, self._cleared


class _ExtraTile(QFrame):
    remove_clicked = Signal(object)

    def __init__(
        self, *, label: str, path: Path, payload: tuple, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self.setProperty("class", "extra-tile")
        self._payload = payload
        self.setFixedSize(108, 150)

        thumb = QLabel()
        thumb.setProperty("class", "extra-thumb")
        thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        thumb.setFixedSize(88, 88)
        pix = QPixmap(str(path))
        if not pix.isNull():
            thumb.setPixmap(_scale_pixmap(pix, QSize(88, 88)))

        name = QLabel(label)
        name.setProperty("class", "extra-name")
        name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name.setToolTip(str(path))

        remove = QPushButton("Remove")
        remove.setProperty("class", "ghost")
        remove.clicked.connect(lambda: self.remove_clicked.emit(self._payload))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)
        layout.addWidget(thumb, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(name)
        layout.addWidget(remove)


class _AddExtraTile(QFrame):
    clicked = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setProperty("class", "add-extra-tile")
        self.setFixedSize(108, 150)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        plus = QLabel("+")
        plus.setProperty("class", "upload-plus")
        plus.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint = QLabel("Add extra")
        hint.setProperty("class", "upload-hint")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(plus)
        layout.addWidget(hint)

    def mousePressEvent(self, event) -> None:  # noqa: ANN001, N802
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class ProductImagePanel(QWidget):
    """Front/back uploads and extra photo strip (embed inside Overview Photos group)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("ProductImagePanel")
        self._front = _ImageSlot("Front", "Used in the product list.")
        self._back = _ImageSlot("Back", "Optional second view.")
        self._existing_extras: list[ExtraImageEntry] = []
        self._new_extra_paths: list[Path] = []

        primary_row = QHBoxLayout()
        primary_row.setSpacing(16)
        primary_row.addWidget(self._front, stretch=1)
        primary_row.addWidget(self._back, stretch=1)

        extras_frame = QFrame()
        extras_frame.setProperty("class", "extras-panel")
        extras_title = QLabel("Extra photos")
        extras_title.setProperty("class", "slot-title")
        extras_sub = QLabel("Labels, trims, packaging — optional.")
        extras_sub.setProperty("class", "slot-subtitle")

        self._extra_strip = QWidget()
        self._extra_strip_layout = QHBoxLayout(self._extra_strip)
        self._extra_strip_layout.setContentsMargins(0, 0, 0, 0)
        self._extra_strip_layout.setSpacing(10)
        self._extra_strip_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFixedHeight(168)
        scroll.setWidget(self._extra_strip)

        extras_layout = QVBoxLayout(extras_frame)
        extras_layout.setContentsMargins(14, 12, 14, 12)
        extras_layout.setSpacing(8)
        extras_layout.addWidget(extras_title)
        extras_layout.addWidget(extras_sub)
        extras_layout.addWidget(scroll)

        hint = QLabel("Photos are saved when you click Save on this dialog.")
        hint.setProperty("class", "hint")
        hint.setWordWrap(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        layout.addWidget(hint)
        layout.addLayout(primary_row)
        layout.addWidget(extras_frame)
        self._rebuild_extra_strip()

    def load_images(
        self,
        *,
        front: Path | None,
        back: Path | None,
        extras: list[ExtraImageEntry],
    ) -> None:
        self._existing_extras = list(extras)
        self._new_extra_paths = []
        self._front.load_existing(front)
        self._back.load_existing(back)
        self._rebuild_extra_strip()

    def _rebuild_extra_strip(self) -> None:
        while self._extra_strip_layout.count():
            item = self._extra_strip_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        add_tile = _AddExtraTile()
        add_tile.clicked.connect(self._add_extra)
        self._extra_strip_layout.addWidget(add_tile)

        for entry in self._existing_extras:
            tile = _ExtraTile(
                label=entry.path.name,
                path=entry.path,
                payload=("existing", entry.image_id),
            )
            tile.remove_clicked.connect(self._remove_extra_payload)
            self._extra_strip_layout.addWidget(tile)

        for idx, path in enumerate(self._new_extra_paths):
            tile = _ExtraTile(
                label=f"{path.name}*",
                path=path,
                payload=("new", idx),
            )
            tile.remove_clicked.connect(self._remove_extra_payload)
            self._extra_strip_layout.addWidget(tile)

        if not self._existing_extras and not self._new_extra_paths:
            empty = QLabel("No extra photos")
            empty.setProperty("class", "upload-hint")
            self._extra_strip_layout.addWidget(empty)

        self._extra_strip_layout.addStretch()

    def _add_extra(self) -> None:
        validated = _pick_image(self, "Select extra photo")
        if validated is None:
            return
        self._new_extra_paths.append(validated)
        self._rebuild_extra_strip()

    def _remove_extra_payload(self, payload: tuple) -> None:
        kind, ref = payload
        if kind == "existing":
            self._existing_extras = [
                e for e in self._existing_extras if e.image_id != ref
            ]
        else:
            index = int(ref)
            if 0 <= index < len(self._new_extra_paths):
                self._new_extra_paths.pop(index)
        self._rebuild_extra_strip()

    def build_state(self, *, original_extras: list[ExtraImageEntry]) -> ImageEditorState:
        front_path, clear_front = self._front.state()
        back_path, clear_back = self._back.state()
        original_ids = {e.image_id for e in original_extras if e.image_id is not None}
        kept_ids = {e.image_id for e in self._existing_extras if e.image_id is not None}
        removed = [i for i in original_ids if i not in kept_ids]
        return ImageEditorState(
            front_path=front_path,
            back_path=back_path,
            clear_front=clear_front,
            clear_back=clear_back,
            new_extra_paths=list(self._new_extra_paths),
            removed_extra_ids=removed,
            existing_extras=list(self._existing_extras),
        )
