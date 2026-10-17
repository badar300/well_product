"""Parse the Hoody (full) tab from the Well Product Excel cost sheet."""

from __future__ import annotations

import re
import tempfile
import zipfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from well_product.units import MaterialCategory, ProductImageKind

_NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
_XDR = "http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing"
_A = "http://schemas.openxmlformats.org/drawingml/2006/main"
_R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"

_SECTION_HEADERS = {
    "Main Fabrication",
    "Stitching Accessories",
    "Packaging Accessories",
    "Special Operation Cost",
    "Direct Labour Cost",
    "Other Expences",
}

_SECTION_TO_CATEGORY: dict[str, MaterialCategory] = {
    "Main Fabrication": MaterialCategory.FABRIC,
    "Stitching Accessories": MaterialCategory.ACCESSORY,
    "Packaging Accessories": MaterialCategory.PACKAGING,
    "Special Operation Cost": MaterialCategory.SPECIAL_OPERATION,
    "Direct Labour Cost": MaterialCategory.LABOUR,
}


@dataclass(frozen=True)
class HoodyProductMeta:
    name: str
    article_no: str
    exchange_rate: Decimal
    special_note: str | None
    production_loss_pct: Decimal
    government_tax_pct: Decimal
    commission_pct: Decimal
    factory_overhead_pct: Decimal
    profit_pct: Decimal
    pricing_adjustment_pkr: Decimal


@dataclass(frozen=True)
class HoodyBomLine:
    material_name: str
    category: MaterialCategory
    average_qty: Decimal
    waste_pct: Decimal
    sort_order: int


@dataclass(frozen=True)
class HoodySheetImage:
    kind: ProductImageKind
    media_path: str  # path inside xlsx zip, e.g. xl/media/image1.png


def load_hoody_cells(xlsx_path: Path) -> dict[str, str]:
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
            raise ValueError("Expected Hoody full sheet as first worksheet")
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
        return cells


def _dec(cell: dict[str, str], ref: str, default: str = "0") -> Decimal:
    raw = cell.get(ref, default)
    return Decimal(str(raw).strip() or default)


def parse_hoody_product_meta(cells: dict[str, str]) -> HoodyProductMeta:
    name = cells.get("B2", "").strip()
    if not name:
        raise ValueError("Missing product name in cell B2")
    article_raw = cells.get("L2", "").strip()
    article_no = str(int(float(article_raw))) if article_raw else ""
    if not article_no:
        raise ValueError("Missing article number in cell L2")
    return HoodyProductMeta(
        name=name,
        article_no=article_no,
        exchange_rate=_dec(cells, "L3", "277"),
        special_note=(cells.get("O57") or "").strip() or None,
        production_loss_pct=_dec(cells, "I48") * Decimal("100"),
        government_tax_pct=_dec(cells, "I49") * Decimal("100"),
        commission_pct=_dec(cells, "I50") * Decimal("100"),
        factory_overhead_pct=_dec(cells, "I51") * Decimal("100"),
        profit_pct=_dec(cells, "I57") * Decimal("100"),
        pricing_adjustment_pkr=_dec(cells, "J57"),
    )


def parse_hoody_bom(cells: dict[str, str]) -> list[HoodyBomLine]:
    max_row = max(int(re.search(r"\d+", ref).group()) for ref in cells)
    section = ""
    lines: list[HoodyBomLine] = []
    order = 0
    for r in range(1, max_row + 1):
        label = cells.get(f"A{r}", "").strip()
        if not label:
            continue
        if label in _SECTION_HEADERS:
            section = label
            continue
        if label.startswith("Total ") or section not in _SECTION_TO_CATEGORY:
            continue
        if not cells.get(f"F{r}") or not cells.get(f"H{r}"):
            continue
        avg = _dec(cells, f"H{r}")
        # Excel stores waste as a decimal fraction (0.05); app stores whole percent (5).
        waste = _dec(cells, f"I{r}", "0") * Decimal("100")
        lines.append(
            HoodyBomLine(
                material_name=label,
                category=_SECTION_TO_CATEGORY[section],
                average_qty=avg,
                waste_pct=waste,
                sort_order=order,
            )
        )
        order += 1
    return lines


def _col_letter(index: int) -> str:
    """0-based column index to Excel letters."""
    n = index + 1
    s = ""
    while n:
        n, rem = divmod(n - 1, 26)
        s = chr(65 + rem) + s
    return s


def extract_hoody_images(xlsx_path: Path) -> list[HoodySheetImage]:
    """Embedded PNGs on sheet1: leftmost anchor → front, next → back."""
    path = xlsx_path.expanduser().resolve()
    drawing_rels: dict[str, str] = {}
    anchors: list[tuple[int, str]] = []

    with zipfile.ZipFile(path) as z:
        rel_path = "xl/drawings/_rels/drawing1.xml.rels"
        if rel_path not in z.namelist():
            return []
        rel_root = ET.fromstring(z.read(rel_path))
        for rel in rel_root:
            if rel.get("Type", "").endswith("/image"):
                drawing_rels[rel.get("Id")] = rel.get("Target", "").replace("../", "xl/")

        draw_root = ET.fromstring(z.read("xl/drawings/drawing1.xml"))
        for anchor in draw_root.findall(f"{{{_XDR}}}oneCellAnchor"):
            fr = anchor.find(f"{{{_XDR}}}from")
            blip = anchor.find(f".//{{{_A}}}blip")
            if fr is None or blip is None:
                continue
            col_el = fr.find(f"{{{_XDR}}}col")
            if col_el is None or col_el.text is None:
                continue
            col = int(col_el.text)
            rid = blip.get(f"{{{_R}}}embed")
            if rid and rid in drawing_rels:
                anchors.append((col, drawing_rels[rid]))

    if not anchors:
        return []

    anchors.sort(key=lambda t: t[0])
    slot_kinds = (ProductImageKind.FRONT, ProductImageKind.BACK)
    return [
        HoodySheetImage(kind=slot_kinds[i], media_path=media)
        for i, (_, media) in enumerate(anchors)
        if i < len(slot_kinds)
    ]


def extract_image_to_temp(xlsx_path: Path, media_path: str) -> Path:
    """Write one embedded image from the xlsx to a temp file for import."""
    path = xlsx_path.expanduser().resolve()
    suffix = Path(media_path).suffix or ".png"
    with zipfile.ZipFile(path) as z:
        data = z.read(media_path)
    tmp = Path(tempfile.mkstemp(suffix=suffix)[1])
    tmp.write_bytes(data)
    return tmp
