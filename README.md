# Well Product

Desktop costing application for garment products. Manage raw material rates, customers, and product BOMs with live cost calculation aligned to the Excel cost sheet formulas.

## Requirements

- Python 3.12 or newer
- macOS (development) or Windows (target deployment)

## Setup

```bash
cd /path/to/well_product
python3.12 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

## Database location

The SQLite file and product photos live in a folder you can back up manually:

```text
Desktop/WellProduct/well_product.sqlite
Desktop/WellProduct/media/...
```

On Mac: `~/Desktop/WellProduct/`  
On Windows (dev or packaged app): `Desktop\WellProduct\`

Override for tests or custom locations:

```bash
export WELL_PRODUCT_DATA_DIR=/tmp/well-product-data
```

The file is gitignored. Migrations run automatically on app startup (`alembic upgrade head`).

## Seed Hoody raw materials (optional)

Import **33** raw material rates from the Hoody (full) Excel costing sheet into your local database:

```bash
well-product-seed-hoody "/path/to/Well Product - Cost Sheet for hoody ....xlsx"
```

Existing materials are matched **by name** and updated with the sheet rate and unit.

Import the full Hoody product (BOM, pricing, front/back photos from the sheet):

```bash
well-product-seed-hoody-product "/path/to/Well Product - Cost Sheet for hoody ....xlsx"
```

Re-running replaces the product with the same article number (`45996` from the sheet).

## Sign in (local desktop)

Default gate for single-workstation use:

- **Username:** `admin`
- **Password:** `admin!@#`

This is a local deterrent only, not network-grade authentication.

## Run the application

```bash
python -m well_product
```

Or:

```bash
well-product
```

### UI overview

- **Raw materials** — catalog of items with unit and PKR rate (editable anytime; product costing uses current rates unless a line has a rate override).
- **Customers** — buyer contact records linked to products.
- **Products** — full costing worksheet per garment:
  - **Overview** tab: details + **Front / Back / extra** photos
  - **Materials** tab: BOM by section (accordion)
  - **Pricing** tab: exchange rate, overheads, fixed extras
  - Live cost summary (manufacturing → overheads → grand total → selling price)
  - **Copy from…** duplicates BOM, costing settings, and images

### Product images

Files are stored under the app data directory (next to the SQLite file in dev):

```text
media/products/{product_id}/front.png
media/products/{product_id}/back.jpg
media/products/{product_id}/extra_1.webp
```

Supported formats: `.jpg`, `.jpeg`, `.png`, `.webp`. The database stores relative paths only; the `media/` folder is gitignored.

## Costing logic

Line PKR = `avg × rate × (1 + waste/100)` (BOM waste % as a whole number, e.g. `5` = 5%).  
Manufacturing = sum of BOM sections.  
Percent overheads apply to manufacturing PKR (whole percent on Pricing tab, e.g. `7` = 7%).  
Grand total = manufacturing + percent overheads + fixed extras.  
Selling price = `grand × (1 + profit%) + pricing adjustment PKR`.

Implemented in `src/well_product/costing/engine.py` (not stored in the database).

## Windows executable (delivery)

Build **on a Windows machine** (PySide6 cannot be cross-compiled reliably from macOS).

```powershell
cd C:\path\to\well_product
.\packaging\build_windows.ps1
```

Output: `dist\WellProduct\WellProduct.exe` plus `_internal\`. Zip the entire `dist\WellProduct\` folder for the other person.

**End user:** unzip, run `WellProduct.exe`, sign in. No Python, pip, or manual migrations — schema upgrades run automatically when the app starts.

**Data location (packaged app on Windows):**

```text
Desktop\WellProduct\well_product.sqlite
Desktop\WellProduct\media\...
```

(Typical path: `C:\Users\<You>\Desktop\WellProduct\`. OneDrive Desktop is detected when `%USERPROFILE%\Desktop` is redirected.)

**Upgrades:** ship a new ZIP and replace the app folder only; user data stays on the Desktop.

Post-build checklist: [packaging/WINDOWS_SMOKE_TEST.md](packaging/WINDOWS_SMOKE_TEST.md).

Development (Mac or Windows) stores the database on the **Desktop** for easy backup:

```text
~/Desktop/WellProduct/well_product.sqlite
~/Desktop/WellProduct/media/...
```

Override with `WELL_PRODUCT_DATA_DIR` or use in tests.

After `.\packaging\build_windows.ps1`, the file to send your client is:

```text
release/WellProduct-Windows.zip
```

## Tests

```bash
pytest
```

## Schema overview

- **customers** — buyer contact details
- **raw_materials** — catalog name, unit, rate
- **products** — product master, customer, exchange rate, overhead % fields, costing mode
- **product_materials** — BOM lines (category, material, avg, waste, optional rate override)
- **product_extra_costs** — fixed logistic/other PKR amounts on a product
- **product_images** — front/back/extra photo paths per product
- **orders** / **order_extra_costs** — reserved for future quotations (not used in v1 UI)

## Project layout

```
src/well_product/
  app.py              entry point
  costing/            calculation engine
  services/           CRUD
  ui/                 PySide6 screens
alembic/              migrations
packaging/            PyInstaller spec, Windows build script
tests/
```
