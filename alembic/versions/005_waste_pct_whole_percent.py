"""BOM waste stored as whole percent (5 = 5%, not 0.05)

Revision ID: 005_waste_pct_whole_percent
Revises: 004_product_images
Create Date: 2026-10-17

"""

from typing import Sequence, Union

from alembic import op

revision: str = "005_waste_pct_whole_percent"
down_revision: Union[str, None] = "004_product_images"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("UPDATE product_materials SET waste_pct = waste_pct * 100")


def downgrade() -> None:
    op.execute("UPDATE product_materials SET waste_pct = waste_pct / 100")
