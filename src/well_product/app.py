"""PySide6 application entry point."""

from __future__ import annotations

import sys

from PySide6.QtCore import QEventLoop
from PySide6.QtWidgets import QApplication, QDialog

from well_product.database import init_db
from well_product.platform.windows_shortcut import ensure_windows_desktop_shortcut
from well_product.ui.login_dialog import LoginDialog
from well_product.ui.main_window import MainWindow

_engine = None


def get_engine():
    global _engine
    if _engine is None:
        _engine = init_db()
    return _engine


def main() -> int:
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    ensure_windows_desktop_shortcut()
    engine = get_engine()

    while True:
        login = LoginDialog()
        if login.exec() != QDialog.DialogCode.Accepted:
            return 0

        window = MainWindow(engine)
        session = QEventLoop()
        logout_after_close = False

        def on_session_finished(logout: bool) -> None:
            nonlocal logout_after_close
            logout_after_close = logout
            session.quit()

        window.session_finished.connect(on_session_finished)
        window.show()
        session.exec()

        window.deleteLater()
        app.processEvents()

        if not logout_after_close:
            return 0


if __name__ == "__main__":
    raise SystemExit(main())
