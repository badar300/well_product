"""raw material delete protection (app-level; SQLite FK names unchanged)

Revision ID: 003_raw_material_fk_restrict
Revises: 002_product_costing
Create Date: 2026-09-29

"""

from typing import Sequence, Union

revision: str = "003_raw_material_fk_restrict"
down_revision: Union[str, None] = "002_product_costing"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Initial schema uses unnamed inline SQLite FKs; batch_alter_table cannot
    # drop "product_materials_raw_material_id_fkey". BOM delete protection is
    # enforced via MaterialInUseError, passive_deletes, and PRAGMA foreign_keys=ON.
    pass


def downgrade() -> None:
    pass
