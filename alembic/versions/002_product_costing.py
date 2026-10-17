"""product costing fields

Revision ID: 002_product_costing
Revises: 001_initial
Create Date: 2026-09-29

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002_product_costing"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "products",
        sa.Column(
            "exchange_rate",
            sa.Numeric(precision=18, scale=4),
            nullable=False,
            server_default="277",
        ),
    )
    op.add_column(
        "products",
        sa.Column(
            "production_loss_pct",
            sa.Numeric(precision=8, scale=6),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "products",
        sa.Column(
            "government_tax_pct",
            sa.Numeric(precision=8, scale=6),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "products",
        sa.Column(
            "commission_pct",
            sa.Numeric(precision=8, scale=6),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "products",
        sa.Column(
            "factory_overhead_pct",
            sa.Numeric(precision=8, scale=6),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "products",
        sa.Column(
            "profit_pct",
            sa.Numeric(precision=8, scale=6),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "products",
        sa.Column(
            "pricing_adjustment_pkr",
            sa.Numeric(precision=18, scale=4),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "products",
        sa.Column(
            "costing_mode",
            sa.String(length=16),
            nullable=False,
            server_default="full",
        ),
    )
    op.add_column(
        "product_materials",
        sa.Column(
            "category",
            sa.String(length=32),
            nullable=False,
            server_default="accessory",
        ),
    )
    op.add_column(
        "product_materials",
        sa.Column("rate_override", sa.Numeric(precision=18, scale=4), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("product_materials", "rate_override")
    op.drop_column("product_materials", "category")
    op.drop_column("products", "costing_mode")
    op.drop_column("products", "pricing_adjustment_pkr")
    op.drop_column("products", "profit_pct")
    op.drop_column("products", "factory_overhead_pct")
    op.drop_column("products", "commission_pct")
    op.drop_column("products", "government_tax_pct")
    op.drop_column("products", "production_loss_pct")
    op.drop_column("products", "exchange_rate")
