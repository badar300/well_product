"""Frozen Hoody (full) sheet snapshot for DB seed migrations."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

HOODY_ARTICLE_NO = '45996'
HOODY_SEED_NOTE_PREFIX = 'Hoody cost sheet'

MEDIA_DIR = Path(__file__).resolve().parent / "hoody_seed_media"

PRODUCT_META = {
    'name': 'Hoody Black Dryrider (Ribstop)',
    'article_no': '45996',
    'exchange_rate': Decimal(Decimal('277.0')),
    'special_note': 'Zipper are normal waterproof (Not Aqua seal)',
    'production_loss_pct': Decimal(Decimal('0.0')),
    'government_tax_pct': Decimal(Decimal('0.0')),
    'commission_pct': Decimal(Decimal('0.0')),
    'factory_overhead_pct': Decimal(Decimal('7.00')),
    'profit_pct': Decimal(Decimal('0.0')),
    'pricing_adjustment_pkr': Decimal(Decimal('0')),
}

MATERIAL_ROWS: list[dict[str, str]] = [
    {"name": '92% Polyester 8% Spandex', "unit": 'MTR', "rate": '886.4', "section": 'Main Fabrication'},
    {"name": 'Lining 100% Polyester', "unit": 'KGS', "rate": '900.0', "section": 'Main Fabrication'},
    {"name": 'Mesh Protector pocket', "unit": 'NO', "rate": '500.0', "section": 'Main Fabrication'},
    {"name": 'Pocket Fabric', "unit": 'NO', "rate": '60.0', "section": 'Main Fabrication'},
    {"name": 'Sewing thread', "unit": 'CON', "rate": '260.0', "section": 'Stitching Accessories'},
    {"name": 'Woven care label', "unit": 'PCS', "rate": '10.0', "section": 'Stitching Accessories'},
    {"name": 'Woven size label', "unit": 'PCS', "rate": '10.0', "section": 'Stitching Accessories'},
    {"name": 'Dori Stoper', "unit": 'NO', "rate": '20.0', "section": 'Stitching Accessories'},
    {"name": 'Zipper (Front)', "unit": 'NO', "rate": '610.0', "section": 'Stitching Accessories'},
    {"name": 'Zipper (Pocket) + Vents', "unit": 'NO', "rate": '100.0', "section": 'Stitching Accessories'},
    {"name": 'Snaps', "unit": 'PCS', "rate": '43.0', "section": 'Stitching Accessories'},
    {"name": 'Ceiling Tape', "unit": 'PCS', "rate": '150.0', "section": 'Stitching Accessories'},
    {"name": 'Ceiling Labour', "unit": 'PCS', "rate": '180.0', "section": 'Stitching Accessories'},
    {"name": 'Ceiling Patches', "unit": 'PCS', "rate": '110.0', "section": 'Stitching Accessories'},
    {"name": 'Hotmelt', "unit": 'PCS', "rate": '80.0', "section": 'Stitching Accessories'},
    {"name": 'Water Barrier + Hotmelt', "unit": 'PCS', "rate": '200.0', "section": 'Stitching Accessories'},
    {"name": 'Foam', "unit": 'PCS', "rate": '50.0', "section": 'Stitching Accessories'},
    {"name": 'Magnet', "unit": 'PCS', "rate": '85.0', "section": 'Stitching Accessories'},
    {"name": 'Lining connection zippers (long + Short)', "unit": 'PCS', "rate": '0.0', "section": 'Stitching Accessories'},
    {"name": 'Metal Badge', "unit": 'PCS', "rate": '200.0', "section": 'Stitching Accessories'},
    {"name": 'Velcro', "unit": 'MTR', "rate": '100.0', "section": 'Stitching Accessories'},
    {"name": 'Carton', "unit": 'PCS', "rate": '400.0', "section": 'Packaging Accessories'},
    {"name": 'Printed poly bag', "unit": 'PCS', "rate": '600.0', "section": 'Packaging Accessories'},
    {"name": 'Tape', "unit": 'PCS', "rate": '100.0', "section": 'Packaging Accessories'},
    {"name": 'Plastic strap', "unit": 'KGS', "rate": '200.0', "section": 'Packaging Accessories'},
    {"name": 'Barcode sticker', "unit": 'PCS', "rate": '5.0', "section": 'Packaging Accessories'},
    {"name": 'Hang tag', "unit": 'PCS', "rate": '30.0', "section": 'Packaging Accessories'},
    {"name": 'Screen Printing/Heat Transfer (pairs Lines)', "unit": 'PCS', "rate": '300.0', "section": 'Special Operation Cost'},
    {"name": 'Cutting', "unit": 'PCS', "rate": '120.0', "section": 'Direct Labour Cost'},
    {"name": 'Stitching Shell', "unit": 'PCS', "rate": '900.0', "section": 'Direct Labour Cost'},
    {"name": 'Stitching Aster', "unit": 'PCS', "rate": '350.0', "section": 'Direct Labour Cost'},
    {"name": 'Finishing (Threading, Pressing)', "unit": 'PCS', "rate": '20.0', "section": 'Direct Labour Cost'},
    {"name": 'Packing', "unit": 'PCS', "rate": '200.0', "section": 'Direct Labour Cost'},
]

BOM_LINES: list[dict[str, object]] = [
    {"material_name": '92% Polyester 8% Spandex', "category": 'fabric', "average_qty": Decimal(Decimal('2.5')), "waste_pct": Decimal(Decimal('5.00')), "sort_order": 0},
    {"material_name": 'Lining 100% Polyester', "category": 'fabric', "average_qty": Decimal(Decimal('0.5')), "waste_pct": Decimal(Decimal('5.00')), "sort_order": 1},
    {"material_name": 'Mesh Protector pocket', "category": 'fabric', "average_qty": Decimal(Decimal('0.1666666667')), "waste_pct": Decimal(Decimal('5.00')), "sort_order": 2},
    {"material_name": 'Pocket Fabric', "category": 'fabric', "average_qty": Decimal(Decimal('1.0')), "waste_pct": Decimal(Decimal('1.00')), "sort_order": 3},
    {"material_name": 'Sewing thread', "category": 'accessory', "average_qty": Decimal(Decimal('0.06')), "waste_pct": Decimal(Decimal('10.0')), "sort_order": 4},
    {"material_name": 'Woven care label', "category": 'accessory', "average_qty": Decimal(Decimal('1.0')), "waste_pct": Decimal(Decimal('5.00')), "sort_order": 5},
    {"material_name": 'Woven size label', "category": 'accessory', "average_qty": Decimal(Decimal('1.0')), "waste_pct": Decimal(Decimal('5.00')), "sort_order": 6},
    {"material_name": 'Dori Stoper', "category": 'accessory', "average_qty": Decimal(Decimal('3.0')), "waste_pct": Decimal(Decimal('5.00')), "sort_order": 7},
    {"material_name": 'Zipper (Front)', "category": 'accessory', "average_qty": Decimal(Decimal('1.0')), "waste_pct": Decimal(Decimal('1.00')), "sort_order": 8},
    {"material_name": 'Zipper (Pocket) + Vents', "category": 'accessory', "average_qty": Decimal(Decimal('4.0')), "waste_pct": Decimal(Decimal('1.00')), "sort_order": 9},
    {"material_name": 'Snaps', "category": 'accessory', "average_qty": Decimal(Decimal('4.0')), "waste_pct": Decimal(Decimal('5.00')), "sort_order": 10},
    {"material_name": 'Ceiling Tape', "category": 'accessory', "average_qty": Decimal(Decimal('1.0')), "waste_pct": Decimal(Decimal('5.00')), "sort_order": 11},
    {"material_name": 'Ceiling Labour', "category": 'accessory', "average_qty": Decimal(Decimal('1.0')), "waste_pct": Decimal(Decimal('1.00')), "sort_order": 12},
    {"material_name": 'Ceiling Patches', "category": 'accessory', "average_qty": Decimal(Decimal('1.0')), "waste_pct": Decimal(Decimal('1.00')), "sort_order": 13},
    {"material_name": 'Hotmelt', "category": 'accessory', "average_qty": Decimal(Decimal('1.0')), "waste_pct": Decimal(Decimal('1.00')), "sort_order": 14},
    {"material_name": 'Water Barrier + Hotmelt', "category": 'accessory', "average_qty": Decimal(Decimal('1.0')), "waste_pct": Decimal(Decimal('1.00')), "sort_order": 15},
    {"material_name": 'Foam', "category": 'accessory', "average_qty": Decimal(Decimal('1.0')), "waste_pct": Decimal(Decimal('1.00')), "sort_order": 16},
    {"material_name": 'Magnet', "category": 'accessory', "average_qty": Decimal(Decimal('2.0')), "waste_pct": Decimal(Decimal('1.00')), "sort_order": 17},
    {"material_name": 'Lining connection zippers (long + Short)', "category": 'accessory', "average_qty": Decimal(Decimal('1.0')), "waste_pct": Decimal(Decimal('1.00')), "sort_order": 18},
    {"material_name": 'Metal Badge', "category": 'accessory', "average_qty": Decimal(Decimal('1.0')), "waste_pct": Decimal(Decimal('2.00')), "sort_order": 19},
    {"material_name": 'Velcro', "category": 'accessory', "average_qty": Decimal(Decimal('1.0')), "waste_pct": Decimal(Decimal('2.00')), "sort_order": 20},
    {"material_name": 'Carton', "category": 'packaging', "average_qty": Decimal(Decimal('0.05')), "waste_pct": Decimal(Decimal('0.0')), "sort_order": 21},
    {"material_name": 'Printed poly bag', "category": 'packaging', "average_qty": Decimal(Decimal('0.01')), "waste_pct": Decimal(Decimal('5.00')), "sort_order": 22},
    {"material_name": 'Tape', "category": 'packaging', "average_qty": Decimal(Decimal('0.005')), "waste_pct": Decimal(Decimal('5.00')), "sort_order": 23},
    {"material_name": 'Plastic strap', "category": 'packaging', "average_qty": Decimal(Decimal('0.004')), "waste_pct": Decimal(Decimal('5.00')), "sort_order": 24},
    {"material_name": 'Barcode sticker', "category": 'packaging', "average_qty": Decimal(Decimal('1.0')), "waste_pct": Decimal(Decimal('10.0')), "sort_order": 25},
    {"material_name": 'Hang tag', "category": 'packaging', "average_qty": Decimal(Decimal('1.0')), "waste_pct": Decimal(Decimal('2.00')), "sort_order": 26},
    {"material_name": 'Screen Printing/Heat Transfer (pairs Lines)', "category": 'special_operation', "average_qty": Decimal(Decimal('1.0')), "waste_pct": Decimal(Decimal('1.00')), "sort_order": 27},
    {"material_name": 'Cutting', "category": 'labour', "average_qty": Decimal(Decimal('1.0')), "waste_pct": Decimal(Decimal('0.0')), "sort_order": 28},
    {"material_name": 'Stitching Shell', "category": 'labour', "average_qty": Decimal(Decimal('1.0')), "waste_pct": Decimal(Decimal('0.0')), "sort_order": 29},
    {"material_name": 'Stitching Aster', "category": 'labour', "average_qty": Decimal(Decimal('1.0')), "waste_pct": Decimal(Decimal('0.0')), "sort_order": 30},
    {"material_name": 'Finishing (Threading, Pressing)', "category": 'labour', "average_qty": Decimal(Decimal('1.0')), "waste_pct": Decimal(Decimal('0.0')), "sort_order": 31},
    {"material_name": 'Packing', "category": 'labour', "average_qty": Decimal(Decimal('1.0')), "waste_pct": Decimal(Decimal('0.0')), "sort_order": 32},
]

SLOT_IMAGES: list[tuple[str, str]] = [
    ('front', 'front.png'),
    ('back', 'back.png'),
]
