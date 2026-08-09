"""Entry point for Twality GeoStamp."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from config import APP_NAME
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

    settings = SettingsStore()
    themes = ThemeManager()
    window = MainWindow(settings=settings, themes=themes)
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
