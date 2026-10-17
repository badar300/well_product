"""Database engine, sessions, and startup migration."""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from well_product.models import Base
from well_product.paths import bundle_root, database_path, ensure_user_data_dir


def sqlite_url(db_path: Path | None = None) -> str:
    path = db_path if db_path is not None else database_path()
    return f"sqlite:///{path}"


def create_db_engine(db_path: Path | None = None) -> Engine:
    engine = create_engine(
        sqlite_url(db_path),
        future=True,
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine, "connect")
    def _set_sqlite_foreign_keys(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine


def get_alembic_config(db_path: Path | None = None) -> Config:
    root = bundle_root()
    config = Config(str(root / "alembic.ini"))
    config.set_main_option("script_location", str(root / "alembic"))
    config.set_main_option("sqlalchemy.url", sqlite_url(db_path))
    return config


def run_migrations(db_path: Path | None = None) -> None:
    command.upgrade(get_alembic_config(db_path), "head")


def init_db(db_path: Path | None = None) -> Engine:
    if db_path is None:
        ensure_user_data_dir()
    else:
        db_path.parent.mkdir(parents=True, exist_ok=True)
    run_migrations(db_path)
    return create_db_engine(db_path)


def build_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
        future=True,
    )


@contextmanager
def session_scope(engine: Engine) -> Generator[Session, None, None]:
    factory = build_session_factory(engine)
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def create_all_for_tests(engine: Engine) -> None:
    """Create schema without Alembic (used in unit tests)."""
    Base.metadata.create_all(engine)
