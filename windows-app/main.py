"""Entry point for Twality GeoStamp Pro."""

from __future__ import annotations

import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from config import APP_ICON, APP_NAME
from core.settings import SettingsStore
from core.theme_manager import ThemeManager
from core.utils import configure_logging, ensure_directories
from ui.main_window import MainWindow


def main() -> int:
    """Start the desktop application."""
    ensure_directories()
    configure_logging()

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    if APP_ICON.exists():
        app.setWindowIcon(QIcon(str(APP_ICON)))

    settings = SettingsStore()
    themes = ThemeManager()
    window = MainWindow(settings=settings, themes=themes)
    if APP_ICON.exists():
        window.setWindowIcon(QIcon(str(APP_ICON)))
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
