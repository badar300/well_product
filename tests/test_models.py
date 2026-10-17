from __future__ import annotations

from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from well_product.models import (
    Customer,
    CustomerOrder,
    OrderExtraCost,
    Product,
    ProductExtraCost,
    ProductMaterial,
    RawMaterial,
)
from well_product.services.materials import MaterialInUseError, delete_material
from well_product.units import ExtraCostKind, MaterialCategory, Unit


def test_create_customer_material_product_bom_and_extras(session: Session) -> None:
    customer = Customer(name="Ahmad SB", email="buyer@example.com", phone="+92-300-0000000")
    material = RawMaterial(
        name="92% Polyester 8% Spandex",
        unit=Unit.MTR.value,
        rate=Decimal("886.4000"),
    )
    session.add_all([customer, material])
    session.flush()

    product = Product(
        name="Hoody Black Dryrider (Ribstop)",
        article_no="45996",
        customer_id=customer.id,
        special_note="Zipper are normal waterproof (Not Aqua seal)",
    )
    session.add(product)
    session.flush()

    session.add(
        ProductMaterial(
            product_id=product.id,
            raw_material_id=material.id,
            average_qty=Decimal("2.5"),
            waste_pct=Decimal("5"),
            category=MaterialCategory.FABRIC.value,
            sort_order=1,
        )
    )
    session.add(
        ProductExtraCost(
            product_id=product.id,
            kind=ExtraCostKind.LOGISTIC.value,
            name="Freight Sialkot to Karachi",
            amount=Decimal("1500"),
            sort_order=1,
        )
    )
    session.commit()

    session.refresh(material)
    assert material.rate == Decimal("886.4000")

    loaded = session.get(Product, product.id)
    assert loaded is not None
    assert len(loaded.materials) == 1
    assert len(loaded.extra_costs) == 1


def test_create_order_with_extra_cost(session: Session) -> None:
    customer = Customer(name="Buyer")
    product = Product(name="Hoody", article_no="45996")
    session.add_all([customer, product])
    session.flush()

    order = CustomerOrder(
        customer_id=customer.id,
        product_id=product.id,
        quantity=Decimal("10"),
        notes="Sample order",
    )
    session.add(order)
    session.flush()

    session.add(
        OrderExtraCost(
            order_id=order.id,
            kind=ExtraCostKind.OTHER.value,
            name="Factory Overhead",
            amount=Decimal("522.72"),
            sort_order=1,
        )
    )
    session.commit()

    loaded = session.get(CustomerOrder, order.id)
    assert loaded is not None
    assert loaded.quantity == Decimal("10")
    assert len(loaded.extra_costs) == 1


def test_delete_material_in_use_rejected(session: Session) -> None:
    material = RawMaterial(name="Thread", unit=Unit.CON.value, rate=Decimal("260"))
    product = Product(name="Hoody", article_no="45996")
    session.add_all([material, product])
    session.flush()
    session.add(
        ProductMaterial(
            product_id=product.id,
            raw_material_id=material.id,
            average_qty=Decimal("1"),
            waste_pct=Decimal("0"),
            category=MaterialCategory.ACCESSORY.value,
        )
    )
    session.commit()
    with pytest.raises(MaterialInUseError) as exc_info:
        delete_material(session, material)
        session.commit()
    assert "Hoody" in exc_info.value.product_names


def test_duplicate_raw_material_name_rejected(session: Session) -> None:
    session.add(RawMaterial(name="Thread", unit=Unit.CON.value, rate=Decimal("260")))
    session.commit()
    session.add(RawMaterial(name="Thread", unit=Unit.CON.value, rate=Decimal("270")))
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_duplicate_product_material_pair_rejected(session: Session) -> None:
    material = RawMaterial(name="Zipper", unit=Unit.NO.value, rate=Decimal("610"))
    product = Product(name="Hoody", article_no="45996")
    session.add_all([material, product])
    session.flush()

    session.add(
        ProductMaterial(
            product_id=product.id,
            raw_material_id=material.id,
            average_qty=Decimal("1"),
            waste_pct=Decimal("1"),
        )
    )
    session.commit()

    session.add(
        ProductMaterial(
            product_id=product.id,
            raw_material_id=material.id,
            average_qty=Decimal("2"),
            waste_pct=Decimal("2"),
        )
    )
    with pytest.raises(IntegrityError):
        session.commit()
