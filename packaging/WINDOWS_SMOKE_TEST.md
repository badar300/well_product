# Windows smoke test (after PyInstaller build)

Run these on a Windows PC after `packaging/build_windows.ps1` succeeds.

## 1. First launch

1. Delete `%USERPROFILE%\Desktop\WellProduct` if it exists (clean test).
2. Open `dist\WellProduct\WellProduct.exe` (keep the whole folder; do not move the exe alone).
3. Sign in: `admin` / `admin!@#`.
4. Confirm folder created: `Desktop\WellProduct\well_product.sqlite`.

## 2. Data and media

1. Create a customer and a product with at least one BOM line.
2. Upload a front or back photo on the product Overview tab.
3. Confirm files under `Desktop\WellProduct\media\products\{id}\`.

## 3. Upgrade path

1. Keep `Desktop\WellProduct` as-is.
2. Replace `dist\WellProduct\` with a newer build (or re-run PyInstaller after a schema change).
3. Launch again — app should open with existing data; migrations apply automatically on startup.

## 4. Common issues

| Symptom | Likely cause |
|---------|----------------|
| App exits immediately | Missing Qt plugin — rebuild with `collect_all('PySide6')` in spec (already included). |
| Migration error on startup | `alembic/` or `alembic.ini` not bundled — check spec `datas`. |
| `No module named well_product.data.hoody_seed` | Old build before seed migration bundling — rebuild with latest `packaging/well_product.spec`. |
| SmartScreen warning | Unsigned exe — choose “More info” → “Run anyway” or sign the binary later. |
| DB not on Desktop | Running from Python dev install, not frozen exe — only packaged exe uses Desktop path. |
