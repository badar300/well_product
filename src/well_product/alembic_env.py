"""Alembic env logic (imported from alembic/env.py). No logging.config — PyInstaller-safe."""

from __future__ import annotations

from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

from well_product.database import sqlite_url
from well_product.models import Base
from well_product.paths import ensure_user_data_dir

config = context.config

project_root = Path(__file__).resolve().parents[2]
project_db_url = f"sqlite:///{project_root / 'well_product.sqlite'}"
configured_url = config.get_main_option("sqlalchemy.url")
if configured_url and "%(here)s" in configured_url:
    configured_url = configured_url.replace("%(here)s", str(project_root))

if configured_url in (None, project_db_url):
    ensure_user_data_dir()
    config.set_main_option("sqlalchemy.url", sqlite_url())

target_metadata = Base.metadata


def run_migrations_offline() -> None:
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
