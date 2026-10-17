"""Resolve user-writable application data paths."""

from __future__ import annotations

import os
import sys
from pathlib import Path


APP_DIR_NAME = "WellProduct"
DB_FILENAME = "well_product.sqlite"
MEDIA_DIR_NAME = "media"
PRODUCTS_MEDIA_DIR = "products"

ALLOWED_IMAGE_SUFFIXES = frozenset({".jpg", ".jpeg", ".png", ".webp"})


def is_frozen() -> bool:
    """True when running as a PyInstaller (or similar) bundled executable."""
    return getattr(sys, "frozen", False)


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def bundle_root() -> Path:
    """Root directory for bundled read-only assets (alembic, alembic.ini)."""
    if is_frozen():
        return Path(getattr(sys, "_MEIPASS"))
    return project_root()


def _windows_desktop_dir() -> Path:
    home = Path.home()
    profile = Path(os.environ.get("USERPROFILE", str(home)))
    for candidate in (
        profile / "Desktop",
        profile / "OneDrive" / "Desktop",
        home / "Desktop",
    ):
        if candidate.is_dir():
            return candidate
    return profile / "Desktop"


def _desktop_wellproduct_dir() -> Path:
    """User-visible folder for DB + media (easy manual backup)."""
    if sys.platform == "win32":
        return _windows_desktop_dir() / APP_DIR_NAME
    desktop = Path.home() / "Desktop" / APP_DIR_NAME
    if (Path.home() / "Desktop").is_dir():
        return desktop
    if sys.platform == "darwin":
        return Path.home() / "Documents" / APP_DIR_NAME
    return Path.home() / APP_DIR_NAME


def user_data_dir() -> Path:
    """Return the directory where the app stores its SQLite database."""
    override = os.environ.get("WELL_PRODUCT_DATA_DIR")
    if override:
        return Path(override).expanduser().resolve()
    return _desktop_wellproduct_dir()


def database_path() -> Path:
    return user_data_dir() / DB_FILENAME


def ensure_user_data_dir() -> Path:
    directory = user_data_dir()
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def media_root() -> Path:
    return user_data_dir() / MEDIA_DIR_NAME


def product_media_dir(product_id: int) -> Path:
    return media_root() / PRODUCTS_MEDIA_DIR / str(product_id)


def ensure_media_dirs(product_id: int | None = None) -> Path:
    root = media_root()
    root.mkdir(parents=True, exist_ok=True)
    products_dir = root / PRODUCTS_MEDIA_DIR
    products_dir.mkdir(parents=True, exist_ok=True)
    if product_id is not None:
        product_dir = products_dir / str(product_id)
        product_dir.mkdir(parents=True, exist_ok=True)
        return product_dir
    return products_dir


def resolve_media_path(relative_path: str) -> Path:
    return user_data_dir() / relative_path


def relative_media_path(absolute: Path) -> str:
    return str(absolute.relative_to(user_data_dir()))
