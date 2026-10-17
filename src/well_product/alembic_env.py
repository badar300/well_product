"""Alembic env logic (imported from alembic/env.py). No logging.config — PyInstaller-safe."""

from __future__ import annotations

from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

from well_product.database import sqlite_url
from well_product.models import Base
from well_product.paths import ensure_user_data_dir

target_metadata = Base.metadata


def _project_db_url() -> str:
    project_root = Path(__file__).resolve().parents[2]
    return f"sqlite:///{project_root / 'well_product.sqlite'}"


def _resolve_migration_url(config) -> None:
    """Ensure Alembic uses the database URL for this process (fresh each run)."""
    configured_url = config.get_main_option("sqlalchemy.url")
    if configured_url and "%(here)s" in configured_url:
        project_root = Path(__file__).resolve().parents[2]
        configured_url = configured_url.replace("%(here)s", str(project_root))

    project_db_url = _project_db_url()
    if configured_url in (None, project_db_url):
        ensure_user_data_dir()
        config.set_main_option("sqlalchemy.url", sqlite_url())


def run_migrations_offline() -> None:
    config = context.config
    _resolve_migration_url(config)
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    config = context.config
    _resolve_migration_url(config)
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


def run() -> None:
    if context.is_offline_mode():
        run_migrations_offline()
    else:
        run_migrations_online()
