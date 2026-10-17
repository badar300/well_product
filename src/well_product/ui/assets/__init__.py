"""Bundled UI asset paths (package resources)."""

from __future__ import annotations

from importlib import resources
from pathlib import Path


def asset_path(name: str) -> Path:
    """Return filesystem path to a file under well_product/ui/assets/."""
    root = resources.files("well_product.ui.assets")
    return Path(str(root / name))
