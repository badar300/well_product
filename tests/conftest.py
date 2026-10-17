from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from well_product.database import create_all_for_tests, sqlite_url
from well_product.models import (
    Customer,
    CustomerOrder,
    OrderExtraCost,
    Product,
    ProductExtraCost,
    ProductMaterial,
    RawMaterial,
)
from well_product.units import ExtraCostKind, Unit


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "test.sqlite"


@pytest.fixture
def session(db_path: Path) -> Session:
    engine = create_engine(
        sqlite_url(db_path),
        connect_args={"check_same_thread": False},
    )
    create_all_for_tests(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    sess = factory()
    try:
        yield sess
    finally:
        sess.close()
        engine.dispose()
