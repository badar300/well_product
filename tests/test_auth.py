from __future__ import annotations

from well_product.auth import validate_credentials


def test_valid_admin_credentials() -> None:
    assert validate_credentials("admin", "admin!@#")


def test_wrong_password() -> None:
    assert not validate_credentials("admin", "wrong")


def test_wrong_username() -> None:
    assert not validate_credentials("user", "admin!@#")


def test_empty_credentials() -> None:
    assert not validate_credentials("", "admin!@#")
    assert not validate_credentials("admin", "")
