from __future__ import annotations

import sys
from pathlib import Path

import pytest

from well_product import paths


def test_user_data_dir_respects_override(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("WELL_PRODUCT_DATA_DIR", raising=False)
    monkeypatch.setattr(paths, "is_frozen", lambda: False)
    monkeypatch.setenv("WELL_PRODUCT_DATA_DIR", str(tmp_path / "custom"))
    assert paths.user_data_dir() == (tmp_path / "custom").resolve()


def test_dev_uses_desktop_wellproduct(tmp_path, monkeypatch) -> None:
    desktop = tmp_path / "Desktop"
    desktop.mkdir()
    monkeypatch.delenv("WELL_PRODUCT_DATA_DIR", raising=False)
    monkeypatch.setattr(
        paths,
        "_desktop_wellproduct_dir",
        lambda: desktop / paths.APP_DIR_NAME,
    )
    assert paths.user_data_dir() == desktop / paths.APP_DIR_NAME


def test_frozen_windows_uses_desktop_wellproduct(tmp_path, monkeypatch) -> None:
    desktop = tmp_path / "Desktop"
    desktop.mkdir()
    monkeypatch.delenv("WELL_PRODUCT_DATA_DIR", raising=False)
    monkeypatch.setattr(paths, "is_frozen", lambda: True)
    monkeypatch.setattr(paths, "_windows_desktop_dir", lambda: desktop)
    monkeypatch.setattr(sys, "platform", "win32")
    assert paths.user_data_dir() == desktop / paths.APP_DIR_NAME


def test_bundle_root_dev_is_project_root(monkeypatch) -> None:
    monkeypatch.setattr(paths, "is_frozen", lambda: False)
    assert paths.bundle_root() == paths.project_root()


def test_bundle_root_frozen_uses_meipass(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(paths, "is_frozen", lambda: True)
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path / "bundle"), raising=False)
    assert paths.bundle_root() == tmp_path / "bundle"
