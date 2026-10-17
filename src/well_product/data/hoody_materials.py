"""Raw materials extracted from the Hoody (full) costing sheet."""

from __future__ import annotations

import re
import zipfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from well_product.units import Unit

_NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}

_SECTION_SKIP = {
    "Main Fabrication",
    "Stitching Accessories",
    "Packaging Accessories",
    "Special Operation Cost",
    "Direct Labour Cost",
    "Other Expences",
    "Total of Manufacturing Cost",
    "Production Loss",
    "Government Tax",
    "Commission",
    "Factory Overhead",
    "Logistic Charges",
    "Total Logistic Cost",
    "Frofit %age Policy",
    "Order Quantity",
    "Current Exchange Rate",
    "Article No.",
    "BACK",
    "Costing Sheet",
}


@dataclass(frozen=True)
class HoodyMaterialRow:
    name: str
    unit: str
    rate: Decimal
    section: str


def normalize_unit(raw: str) -> str:
    """Map Excel unit text to app Unit enum values."""
    key = raw.strip().upper()
    if key in ("MTR", "METER", "METRE"):
        return Unit.MTR.value
    if key == Unit.KGS.value:
        return Unit.KGS.value
    if key == Unit.PCS.value:
        return Unit.PCS.value
    if key == Unit.CON.value:
        return Unit.CON.value
    if key in (Unit.NO.value, "NOS", "NO."):
        return Unit.NO.value
    raise ValueError(f"Unknown unit '{raw}' from Hoody sheet")


def parse_hoody_full_sheet(xlsx_path: Path) -> list[HoodyMaterialRow]:
    """Read sheet 'Hoody ' (first sheet) — material name, rate (F), unit (G)."""
    path = xlsx_path.expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(path)

    with zipfile.ZipFile(path) as z:
        shared: list[str] = []
        if "xl/sharedStrings.xml" in z.namelist():
            root = ET.fromstring(z.read("xl/sharedStrings.xml"))
            for si in root.findall("m:si", _NS):
                texts = [t.text or "" for t in si.findall(".//m:t", _NS)]
                shared.append("".join(texts))

        sheet_path = "xl/worksheets/sheet1.xml"
        if sheet_path not in z.namelist():
            raise ValueError("Expected first worksheet (Hoody full sheet) in workbook")
        root = ET.fromstring(z.read(sheet_path))
        cells: dict[str, str] = {}
        for c in root.findall(".//m:c", _NS):
            ref = c.get("r")
            if not ref:
                continue
            v = c.find("m:v", _NS)
            if v is None or v.text is None:
                continue
            cells[ref] = shared[int(v.text)] if c.get("t") == "s" else v.text

    max_row = max(int(re.search(r"\d+", ref).group()) for ref in cells)
    rows: list[HoodyMaterialRow] = []
    section = ""

    for r in range(1, max_row + 1):
        name = cells.get(f"A{r}", "").strip()
        if not name:
            continue
        if name in _SECTION_SKIP or name.startswith("Total "):
            section = name
            continue
        rate_raw = cells.get(f"F{r}", "")
        unit_raw = cells.get(f"G{r}", "").strip()
        if not rate_raw or not unit_raw:
            continue
        try:
            rate = Decimal(str(rate_raw))
        except Exception as exc:  # noqa: BLE001
            continue
        unit = normalize_unit(unit_raw)
        rows.append(
            HoodyMaterialRow(
                name=name,
                unit=unit,
                rate=rate,
                section=section or "Hoody sheet",
            )
        )
    return rows
