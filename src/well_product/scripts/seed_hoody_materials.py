"""Load Hoody (full) sheet raw materials into raw_materials table."""

from __future__ import annotations

import argparse
from pathlib import Path

from sqlalchemy import select

from well_product.data.hoody_materials import HoodyMaterialRow, parse_hoody_full_sheet
from well_product.database import init_db, session_scope
from well_product.models import RawMaterial
from well_product.services import materials as material_service


def _note_for(row: HoodyMaterialRow) -> str:
    return f"Hoody cost sheet · {row.section}"


def upsert_hoody_materials(
    session,
    rows: list[HoodyMaterialRow],
) -> tuple[int, int]:
    created = 0
    updated = 0
    for row in rows:
        notes = _note_for(row)
        existing = session.scalar(
            select(RawMaterial).where(RawMaterial.name == row.name)
        )
        if existing is None:
            material_service.create_material(
                session,
                name=row.name,
                unit=row.unit,
                rate=row.rate,
                notes=notes,
            )
            created += 1
        else:
            material_service.update_material(
                session,
                existing,
                name=row.name,
                unit=row.unit,
                rate=row.rate,
                notes=notes,
            )
            updated += 1
    return created, updated


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Import raw materials from the Hoody (full) Excel costing sheet."
    )
    parser.add_argument(
        "xlsx",
        type=Path,
        help="Path to Well Product Hoody .xlsx",
    )
    args = parser.parse_args()

    rows = parse_hoody_full_sheet(args.xlsx)
    source = str(args.xlsx)

    engine = init_db()
    with session_scope(engine) as session:
        created, updated = upsert_hoody_materials(session, rows)
    print(
        f"Imported {len(rows)} materials from {source}: "
        f"{created} created, {updated} updated."
    )


if __name__ == "__main__":
    main()
