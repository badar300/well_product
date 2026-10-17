"""Seed Hoody (full) sheet raw materials and product snapshot

Revision ID: 007_seed_hoody_sheet
Revises: 006_product_pct_whole_percent
Create Date: 2026-10-18

"""

from typing import Sequence, Union

from alembic import op
from sqlalchemy.orm import Session

from well_product.data.hoody_seed import apply_hoody_seed, remove_hoody_seed

revision: str = "007_seed_hoody_sheet"
down_revision: Union[str, None] = "006_product_pct_whole_percent"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    try:
        apply_hoody_seed(session)
        session.flush()
    finally:
        session.close()


def downgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    try:
        remove_hoody_seed(session)
        session.flush()
    finally:
        session.close()
