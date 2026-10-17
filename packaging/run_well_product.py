"""PyInstaller entry point for Well Product."""

# Bundled builds: load logging.config before Alembic/SQLAlchemy (PyInstaller stdlib gap).
import sys

if getattr(sys, "frozen", False) or hasattr(sys, "_MEIPASS"):
    import logging.config  # noqa: F401
    # Alembic revision 007 imports this at runtime; ensure PyInstaller bundles it.
    import well_product.data.hoody_seed  # noqa: F401
    import well_product.data.hoody_seed_snapshot  # noqa: F401

from well_product.app import main

if __name__ == "__main__":
    raise SystemExit(main())
