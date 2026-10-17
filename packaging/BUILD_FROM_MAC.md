# Build the Windows ZIP from a Mac

PyInstaller cannot build a Windows `.exe` on macOS. Use **one** of these:

## Option A — GitHub Actions (no Windows PC)

1. Push this repo to GitHub.
2. Open **Actions** → **Build Windows client ZIP** → **Run workflow**.
3. When it finishes, download artifact **WellProduct-Windows.zip**.
4. Save it locally as `release/WellProduct-Windows.zip` if you like, then send to your client.

## Option B — Any Windows PC (friend, office, VM)

1. Copy the project folder to the PC (or `git clone`).
2. Open **PowerShell** in the project folder.
3. Run **one** of these (from the project folder):

```powershell
powershell -ExecutionPolicy Bypass -File .\packaging\build_windows.ps1
```

Or double-click **`packaging\build_windows.cmd`** in File Explorer.

You do **not** need `Activate.ps1` or `venv\Scripts\activate` — the script uses `.venv\Scripts\python.exe` directly.

If build fails, delete the `.venv` folder and run again.

4. Share this file only:

```text
release\WellProduct-Windows.zip
```

## Your Mac (daily dev + backup)

1. Run the app as usual: `python -m well_product`
2. Data is here (back up this folder):

```text
/Users/YOUR_NAME/Desktop/WellProduct/
```

3. Copy `well_product.sqlite` and `media/` to USB or cloud anytime.
