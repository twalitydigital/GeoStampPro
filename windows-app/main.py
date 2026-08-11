"""Entry point for Twality GMark Pro."""

from __future__ import annotations

import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QIcon, QLinearGradient, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QApplication, QSplashScreen

from config import APP_ICON, APP_NAME, APP_VERSION


def create_splash_screen() -> QSplashScreen:
    """Create the startup splash screen shown while the main window is built."""
    width = 560
    height = 320
    pixmap = QPixmap(width, height)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    background = QLinearGradient(0, 0, width, height)
    background.setColorAt(0.0, QColor("#102033"))
    background.setColorAt(0.55, QColor("#163d4f"))
    background.setColorAt(1.0, QColor("#1d6b5d"))
    painter.setBrush(background)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRoundedRect(0, 0, width, height, 18, 18)

    painter.setBrush(QColor(255, 255, 255, 28))
    painter.drawRoundedRect(34, 34, width - 68, height - 68, 14, 14)

    if APP_ICON.exists():
        icon = QIcon(str(APP_ICON)).pixmap(64, 64)
        painter.drawPixmap(56, 58, icon)

    painter.setPen(QColor("#f7fbff"))
    title_font = QFont("Segoe UI", 24, QFont.Weight.DemiBold)
    painter.setFont(title_font)
    painter.drawText(136, 68, width - 180, 42, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, APP_NAME)

    painter.setPen(QColor("#cfe9ef"))
    subtitle_font = QFont("Segoe UI", 10)
    painter.setFont(subtitle_font)
    painter.drawText(138, 112, width - 190, 24, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, f"Version {APP_VERSION}")

    painter.setPen(QPen(QColor("#62d2b2"), 3))
    painter.drawLine(56, 174, width - 56, 174)

    painter.setPen(QColor("#edf7f9"))
    status_font = QFont("Segoe UI", 11)
    painter.setFont(status_font)
    painter.drawText(56, 198, width - 112, 30, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, "Loading workspace and photo tools...")

    painter.setPen(QColor("#b7cbd2"))
    copyright_font = QFont("Segoe UI", 9)
    painter.setFont(copyright_font)
    painter.drawText(
        56,
        height - 64,
        width - 112,
        24,
        Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
        "Copyright (c) 2026 Twality Digital Solutions LLP. All rights reserved.",
    )

    painter.end()
    return QSplashScreen(pixmap, Qt.WindowType.WindowStaysOnTopHint)


def main() -> int:
    """Start the desktop application."""
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    if APP_ICON.exists():
        app.setWindowIcon(QIcon(str(APP_ICON)))

    splash = create_splash_screen()
    splash.show()
    app.processEvents()

    from core.settings import SettingsStore
    from core.theme_manager import ThemeManager
    from core.utils import configure_logging, ensure_directories
    from ui.main_window import MainWindow

    ensure_directories()
    configure_logging()

    settings = SettingsStore()
    themes = ThemeManager()
    window = MainWindow(settings=settings, themes=themes)
    if APP_ICON.exists():
        window.setWindowIcon(QIcon(str(APP_ICON)))
    window.show()
    splash.finish(window)

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
