from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy.orm import Session

from well_product.models import Product
from well_product.paths import product_media_dir
from well_product.services import product_images as image_service
from well_product.services import products as product_service
from well_product.units import ProductImageKind


def _make_png(path: Path) -> None:
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc``\x00\x00\x00\x02\x00\x01\xe2!\xbc3\x00\x00\x00\x00IEND\xaeB`\x82"
    )


def _product(session: Session) -> Product:
    return product_service.create_product(
        session,
        name="Test Hoody",
        article_no="T1",
        customer_id=None,
        special_note=None,
        exchange_rate=Decimal("277"),
        production_loss_pct=Decimal("0"),
        government_tax_pct=Decimal("0"),
        commission_pct=Decimal("0"),
        factory_overhead_pct=Decimal("0"),
        profit_pct=Decimal("0"),
        pricing_adjustment_pkr=Decimal("0"),
        costing_mode="full",
    )


def test_set_front_and_back_images(
    session: Session, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("WELL_PRODUCT_DATA_DIR", str(tmp_path))
    product = _product(session)
    front = tmp_path / "front_src.png"
    back = tmp_path / "back_src.png"
    _make_png(front)
    _make_png(back)
    image_service.set_slot_image(session, product.id, ProductImageKind.FRONT, front)
    image_service.set_slot_image(session, product.id, ProductImageKind.BACK, back)
    session.commit()

    images = image_service.list_images(session, product.id)
    kinds = {img.kind for img in images}
    assert kinds == {ProductImageKind.FRONT.value, ProductImageKind.BACK.value}
    for img in images:
        assert image_service.resolve_absolute(img.relative_path).is_file()


def test_replace_front_removes_old_file(
    session: Session, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("WELL_PRODUCT_DATA_DIR", str(tmp_path))
    product = _product(session)
    first = tmp_path / "first.png"
    second = tmp_path / "second.png"
    _make_png(first)
    _make_png(second)
    image_service.set_slot_image(session, product.id, ProductImageKind.FRONT, first)
    image_service.set_slot_image(session, product.id, ProductImageKind.FRONT, second)
    session.commit()
    images = image_service.list_images(session, product.id)
    front_rows = [i for i in images if i.kind == ProductImageKind.FRONT.value]
    assert len(front_rows) == 1
    assert image_service.resolve_absolute(front_rows[0].relative_path).is_file()


def test_delete_product_removes_media_dir(
    session: Session, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("WELL_PRODUCT_DATA_DIR", str(tmp_path))
    product = _product(session)
    png = tmp_path / "pic.png"
    _make_png(png)
    image_service.set_slot_image(session, product.id, ProductImageKind.FRONT, png)
    session.commit()
    media_dir = product_media_dir(product.id)
    assert media_dir.is_dir()
    product_service.delete_product(session, product)
    session.commit()
    assert not media_dir.exists()


def test_duplicate_product_copies_images(
    session: Session, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("WELL_PRODUCT_DATA_DIR", str(tmp_path))
    source = _product(session)
    png = tmp_path / "pic.png"
    _make_png(png)
    image_service.set_slot_image(session, source.id, ProductImageKind.FRONT, png)
    session.commit()
    loaded = product_service.get_product(session, source.id)
    assert loaded is not None
    clone = product_service.duplicate_product(
        session,
        loaded,
        name="Clone",
        article_no="T2",
        customer_id=None,
    )
    session.commit()
    clone_images = image_service.list_images(session, clone.id)
    assert len(clone_images) == 1
    assert clone_images[0].kind == ProductImageKind.FRONT.value
