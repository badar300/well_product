"""Product pricing percents as whole numbers (7 = 7%, not 0.07)

Revision ID: 006_product_pct_whole_percent
Revises: 005_waste_pct_whole_percent
Create Date: 2026-10-17

"""

from typing import Sequence, Union

from alembic import op

revision: str = "006_product_pct_whole_percent"
down_revision: Union[str, None] = "005_waste_pct_whole_percent"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_PCT_COLUMNS = (
    "production_loss_pct",
    "government_tax_pct",
    "commission_pct",
    "factory_overhead_pct",
    "profit_pct",
)


def upgrade() -> None:
    for col in _PCT_COLUMNS:
        op.execute(f"UPDATE products SET {col} = {col} * 100")


def downgrade() -> None:
    for col in _PCT_COLUMNS:
        op.execute(f"UPDATE products SET {col} = {col} / 100")
