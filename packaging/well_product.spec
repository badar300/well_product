# PyInstaller one-folder build for Well Product (Windows).
# Run from repo root: pyinstaller packaging/well_product.spec

import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_all, collect_submodules

block_cipher = None

project_root = Path(SPECPATH).resolve().parent
src_path = project_root / "src"

datas = [
    (str(project_root / "alembic"), "alembic"),
    (str(project_root / "alembic.ini"), "."),
]

binaries: list = []
_alembic_submodules = [
    name
    for name in collect_submodules("alembic")
    if not name.startswith("alembic.templates")
]

hiddenimports = _alembic_submodules + [
    "logging.config",
    "logging.handlers",
    "well_product.alembic_env",
    "sqlalchemy.dialects.sqlite",
    "well_product",
]

pyside6_datas, pyside6_binaries, pyside6_hidden = collect_all("PySide6")
datas += pyside6_datas
binaries += pyside6_binaries
hiddenimports += pyside6_hidden

a = Analysis(
    [str(project_root / "packaging" / "run_well_product.py")],
    pathex=[str(src_path)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[str(project_root / "packaging" / "pyi_rth_logging.py")],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="WellProduct",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="WellProduct",
)
