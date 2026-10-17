"""Create a Desktop shortcut to the packaged Windows executable (once)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from well_product.paths import ensure_user_data_dir, is_frozen, windows_desktop_dir


def _shortcut_path() -> Path:
    return windows_desktop_dir() / "Well Product.lnk"


def _marker_path() -> Path:
    return ensure_user_data_dir() / ".windows_desktop_shortcut"


def ensure_windows_desktop_shortcut() -> None:
    """On frozen Windows builds, place Well Product.lnk on the user's Desktop once."""
    if sys.platform != "win32" or not is_frozen():
        return

    marker = _marker_path()
    if marker.exists():
        return

    exe = Path(sys.executable).resolve()
    if not exe.is_file():
        return

    shortcut = _shortcut_path()
    work_dir = exe.parent
    ps = (
        "$shell = New-Object -ComObject WScript.Shell; "
        f"$sc = $shell.CreateShortcut('{shortcut.as_posix()}'); "
        f"$sc.TargetPath = '{exe.as_posix()}'; "
        f"$sc.WorkingDirectory = '{work_dir.as_posix()}'; "
        f"$sc.IconLocation = '{exe.as_posix()},0'; "
        "$sc.Description = 'Well Product — garment costing'; "
        "$sc.Save()"
    )
    try:
        subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                ps,
            ],
            check=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        marker.write_text(str(shortcut), encoding="utf-8")
    except (OSError, subprocess.CalledProcessError):
        # Non-fatal: user can still use Send to → Desktop from CLIENT_SETUP.txt.
        return
