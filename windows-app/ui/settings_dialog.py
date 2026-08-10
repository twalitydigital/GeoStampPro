"""Settings dialog."""

from __future__ import annotations

from PySide6.QtWidgets import QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFormLayout, QSpinBox

from core.overlay_renderer import TIMESTAMP_FORMATS
from core.settings import SettingsStore


class SettingsDialog(QDialog):
    """Edit persistent application settings."""

    def __init__(self, settings: SettingsStore, parent=None) -> None:
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Settings")
        layout = QFormLayout(self)
        self.quality = QSpinBox()
        self.quality.setRange(50, 100)
        self.quality.setValue(int(settings.get("output_quality", 95)))
        self.font_size = QSpinBox()
        self.font_size.setRange(14, 64)
        self.font_size.setValue(int(settings.get("font_size", 24)))
        self.map_width = QSpinBox()
        self.map_width.setRange(160, 900)
        self.map_width.setValue(int(settings.get("map_width", 320)))
        self.map_height = QSpinBox()
        self.map_height.setRange(120, 700)
        self.map_height.setValue(int(settings.get("map_height", 220)))
        self.timestamp_format = QComboBox()
        for key, label, _ in TIMESTAMP_FORMATS:
            self.timestamp_format.addItem(label, key)
        current_format = str(settings.get("timestamp_format", "yyyy-mm-dd_24h"))
        current_index = self.timestamp_format.findData(current_format)
        self.timestamp_format.setCurrentIndex(max(0, current_index))
        self.stamp_all_additional_exif = QCheckBox("Stamp all additional EXIF Data")
        self.stamp_all_additional_exif.setChecked(bool(settings.get("stamp_all_additional_exif", False)))
        layout.addRow("Output quality", self.quality)
        layout.addRow("Font size", self.font_size)
        layout.addRow("Map width", self.map_width)
        layout.addRow("Map height", self.map_height)
        layout.addRow("Timestamp format", self.timestamp_format)
        layout.addRow("", self.stamp_all_additional_exif)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def save(self) -> None:
        self.settings.set("output_quality", self.quality.value())
        self.settings.set("font_size", self.font_size.value())
        self.settings.set("map_width", self.map_width.value())
        self.settings.set("map_height", self.map_height.value())
        self.settings.set("timestamp_format", self.timestamp_format.currentData())
        self.settings.set("stamp_all_additional_exif", self.stamp_all_additional_exif.isChecked())
        self.accept()
