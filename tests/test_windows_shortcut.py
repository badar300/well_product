from __future__ import annotations

import sys

import pytest

from well_product.platform import windows_shortcut as ws


def test_ensure_shortcut_noop_off_windows(monkeypatch) -> None:
    monkeypatch.setattr(ws, "is_frozen", lambda: True)
    monkeypatch.setattr(sys, "platform", "darwin")
    ws.ensure_windows_desktop_shortcut()


def test_ensure_shortcut_noop_when_not_frozen(monkeypatch) -> None:
    monkeypatch.setattr(ws, "is_frozen", lambda: False)
    monkeypatch.setattr(sys, "platform", "win32")
    ws.ensure_windows_desktop_shortcut()
