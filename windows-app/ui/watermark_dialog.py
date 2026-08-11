"""Watermark configuration dialog."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QWidget,
)

from core.settings import SettingsStore


WATERMARK_POSITIONS = [
    ("top_left", "Top left"),
    ("top_center", "Top center"),
    ("top_right", "Top right"),
    ("middle_left", "Middle left"),
    ("middle_center", "Center"),
    ("middle_right", "Middle right"),
    ("bottom_left", "Bottom left"),
    ("bottom_center", "Bottom center"),
    ("bottom_right", "Bottom right"),
]


class WatermarkDialog(QDialog):
    """Edit persistent watermark settings."""

    def __init__(self, settings: SettingsStore, parent=None) -> None:
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Watermark Settings")

        layout = QFormLayout(self)

        self.watermark_type = QComboBox()
        self.watermark_type.addItem("Text", "text")
        self.watermark_type.addItem("Image", "image")
        self._set_combo_value(self.watermark_type, str(settings.get("watermark_type", "text")))
        self.watermark_type.currentIndexChanged.connect(self.update_type_controls)

        self.watermark_text = QLineEdit(str(settings.get("watermark_text", "Twality GMark Pro")))
        self.watermark_image_path = QLineEdit(str(settings.get("watermark_image_path", "")))
        self.image_browse_button = QPushButton("Browse")
        self.image_browse_button.clicked.connect(self.pick_watermark_image)
        image_row = QHBoxLayout()
        image_row.addWidget(self.watermark_image_path, stretch=1)
        image_row.addWidget(self.image_browse_button)
        image_widget = QWidget()
        image_widget.setLayout(image_row)

        self.position_buttons = QButtonGroup(self)
        position_widget = QWidget()
        position_layout = QGridLayout(position_widget)
        position_layout.setSpacing(4)
        current_position = str(settings.get("watermark_position", "bottom_right"))
        for index, (key, label) in enumerate(WATERMARK_POSITIONS):
            button = QRadioButton(label)
            button.setProperty("position", key)
            self.position_buttons.addButton(button)
            position_layout.addWidget(button, index // 3, index % 3)
            if key == current_position:
                button.setChecked(True)
        if self.position_buttons.checkedButton() is None:
            self.position_buttons.buttons()[-1].setChecked(True)

        self.opacity = QSpinBox()
        self.opacity.setRange(0, 100)
        self.opacity.setSuffix("%")
        self.opacity.setValue(int(settings.get("watermark_opacity", 45)))

        self.size = QSpinBox()
        self.size.setRange(1, 100)
        self.size.setSuffix("%")
        self.size.setValue(int(settings.get("watermark_size", 18)))

        self.margin = QSpinBox()
        self.margin.setRange(0, 25)
        self.margin.setSuffix("%")
        self.margin.setValue(int(settings.get("watermark_margin", 4)))

        layout.addRow("Type", self.watermark_type)
        layout.addRow("Text", self.watermark_text)
        layout.addRow("Image", image_widget)
        layout.addRow("Position", position_widget)
        layout.addRow("Opacity", self.opacity)
        layout.addRow("Size", self.size)
        layout.addRow("Inset", self.margin)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.update_type_controls()

    def pick_watermark_image(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Choose watermark image",
            self.watermark_image_path.text(),
            "Images (*.png *.jpg *.jpeg *.bmp *.webp)",
        )
        if path:
            self.watermark_image_path.setText(path)

    def save(self) -> None:
        self.settings.set("watermark_type", self.watermark_type.currentData())
        self.settings.set("watermark_text", self.watermark_text.text())
        self.settings.set("watermark_image_path", self.watermark_image_path.text())
        self.settings.set("watermark_position", self.position_buttons.checkedButton().property("position"))
        self.settings.set("watermark_opacity", self.opacity.value())
        self.settings.set("watermark_size", self.size.value())
        self.settings.set("watermark_margin", self.margin.value())
        self.accept()

    def update_type_controls(self) -> None:
        is_text = self.watermark_type.currentData() == "text"
        self.watermark_text.setEnabled(is_text)
        self.watermark_image_path.setEnabled(not is_text)
        self.image_browse_button.setEnabled(not is_text)

    def _set_combo_value(self, combo: QComboBox, value: str) -> None:
        index = combo.findData(value)
        combo.setCurrentIndex(max(0, index))
