"""Main window for Twality GeoStamp."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QThread, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QFileDialog,
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from config import APP_NAME
from core.batch_processor import BatchProcessor, ProcessingResult
from core.exif_reader import ExifReader
from core.exif_writer import ExifWriter
from core.overlay_renderer import OverlayOptions, OverlayRenderer
from core.reverse_geocoder import ReverseGeocoder
from core.settings import SettingsStore
from core.static_map import StaticMapRenderer
from core.theme_manager import ThemeManager
from core.utils import Stopwatch, discover_images, human_eta
from ui.preview_dialog import PreviewDialog
from ui.settings_dialog import SettingsDialog
from ui.workers import BatchWorker


class MainWindow(QMainWindow):
    """Primary application shell."""

    def __init__(self, settings: SettingsStore, themes: ThemeManager) -> None:
        super().__init__()
        self.settings = settings
        self.themes = themes
        self.processor = BatchProcessor(ExifReader(), ExifWriter(), ReverseGeocoder(), OverlayRenderer(StaticMapRenderer()))
        self.thread: QThread | None = None
        self.worker: BatchWorker | None = None
        self.total = 0
        self.done = 0
        self.stopwatch = Stopwatch()
        self.setAcceptDrops(True)
        self.setWindowTitle(APP_NAME)
        self.resize(int(settings.get("window_width", 1280)), int(settings.get("window_height", 820)))
        self._build_ui()

    def _build_ui(self) -> None:
        menu = self.menuBar()
        file_menu = menu.addMenu("&File")
        preview_action = QAction("Preview First Image", self)
        preview_action.triggered.connect(self.preview_first)
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.show_settings)
        file_menu.addAction(preview_action)
        file_menu.addAction(settings_action)

        root = QWidget()
        layout = QVBoxLayout(root)
        self.input_edit = QLineEdit(str(self.settings.get("last_input_folder", "")))
        self.output_edit = QLineEdit(str(self.settings.get("last_output_folder", "")))
        layout.addLayout(self._folder_row("Input Folder", self.input_edit, self.pick_input))
        layout.addLayout(self._folder_row("Output Folder", self.output_edit, self.pick_output))

        controls = QHBoxLayout()
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(self.themes.names())
        self.theme_combo.setCurrentText(str(self.settings.get("theme", "Professional")).replace("_", " ").title())
        self.position_combo = QComboBox()
        self.position_combo.addItems(["bottom", "top", "left", "right"])
        self.position_combo.setCurrentText(str(self.settings.get("overlay_position", "bottom")))
        self.recursive_check = QCheckBox("Recursive")
        self.recursive_check.setChecked(bool(self.settings.get("recursive", True)))
        self.workers_spin = QSpinBox()
        self.workers_spin.setRange(1, 32)
        self.workers_spin.setValue(int(self.settings.get("workers", 4)))
        for widget in (QLabel("Theme"), self.theme_combo, QLabel("Placement"), self.position_combo, self.recursive_check, QLabel("Workers"), self.workers_spin):
            controls.addWidget(widget)
        controls.addStretch()
        layout.addLayout(controls)

        actions = QHBoxLayout()
        self.start_button = QPushButton("Start")
        self.pause_button = QPushButton("Pause")
        self.resume_button = QPushButton("Resume")
        self.cancel_button = QPushButton("Cancel")
        self.start_button.clicked.connect(self.start_processing)
        self.pause_button.clicked.connect(self.processor.pause)
        self.resume_button.clicked.connect(self.processor.resume)
        self.cancel_button.clicked.connect(self.processor.cancel)
        for button in (self.start_button, self.pause_button, self.resume_button, self.cancel_button):
            actions.addWidget(button)
        layout.addLayout(actions)

        self.progress = QProgressBar()
        self.status_label = QLabel("Drop a folder or choose an input folder to begin.")
        layout.addWidget(self.progress)
        layout.addWidget(self.status_label)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Source", "Output", "Status", "Message"])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table, stretch=1)
        self.setCentralWidget(root)

    def _folder_row(self, label: str, edit: QLineEdit, picker: object) -> QHBoxLayout:
        row = QHBoxLayout()
        button = QPushButton("Browse")
        button.clicked.connect(picker)
        row.addWidget(QLabel(label))
        row.addWidget(edit, stretch=1)
        row.addWidget(button)
        return row

    def pick_input(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Choose input folder", self.input_edit.text())
        if folder:
            self.input_edit.setText(folder)
            self.settings.set("last_input_folder", folder)

    def pick_output(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Choose output folder", self.output_edit.text())
        if folder:
            self.output_edit.setText(folder)
            self.settings.set("last_output_folder", folder)

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:
        urls = event.mimeData().urls()
        if urls:
            path = Path(urls[0].toLocalFile())
            if path.is_dir():
                self.input_edit.setText(str(path))

    def start_processing(self) -> None:
        input_folder = Path(self.input_edit.text())
        output_folder = Path(self.output_edit.text())
        try:
            self.total = len(discover_images(input_folder, self.recursive_check.isChecked()))
        except FileNotFoundError as exc:
            QMessageBox.warning(self, APP_NAME, str(exc))
            return
        if self.total == 0:
            QMessageBox.information(self, APP_NAME, "No supported images found.")
            return
        self.table.setRowCount(0)
        self.done = 0
        self.stopwatch = Stopwatch()
        self.progress.setRange(0, self.total)
        self.progress.setValue(0)
        options = OverlayOptions(
            position=self.position_combo.currentText(),
            quality=int(self.settings.get("output_quality", 95)),
            map_width=int(self.settings.get("map_width", 320)),
            map_height=int(self.settings.get("map_height", 220)),
            font_size=int(self.settings.get("font_size", 24)),
            logo_path=str(self.settings.get("logo_path", "")),
        )
        self.thread = QThread(self)
        self.worker = BatchWorker(
            self.processor,
            input_folder,
            output_folder,
            self.recursive_check.isChecked(),
            self.workers_spin.value(),
            self.themes.get(self.theme_combo.currentText()),
            options,
            str(self.settings.get("language", "en")),
        )
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.add_result)
        self.worker.finished.connect(self.finish_processing)
        self.worker.finished.connect(self.thread.quit)
        self.thread.start()

    def add_result(self, result: ProcessingResult) -> None:
        self.done += 1
        self.progress.setValue(self.done)
        self.status_label.setText(f"{self.done}/{self.total} complete · ETA {human_eta(self.done, self.total, self.stopwatch.elapsed)}")
        row = self.table.rowCount()
        self.table.insertRow(row)
        values = [str(result.source), str(result.output or ""), result.status, result.message]
        for column, value in enumerate(values):
            item = QTableWidgetItem(value)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, column, item)

    def finish_processing(self, results: list[ProcessingResult]) -> None:
        errors = sum(1 for result in results if result.status == "error")
        skipped = sum(1 for result in results if result.status == "skipped")
        self.status_label.setText(f"Finished {len(results)} images with {errors} errors and {skipped} skipped.")

    def preview_first(self) -> None:
        try:
            paths = discover_images(Path(self.input_edit.text()), self.recursive_check.isChecked())
        except FileNotFoundError as exc:
            QMessageBox.warning(self, APP_NAME, str(exc))
            return
        if not paths:
            QMessageBox.information(self, APP_NAME, "No image available for preview.")
            return
        PreviewDialog(paths[0], self).exec()

    def show_settings(self) -> None:
        SettingsDialog(self.settings, self).exec()

    def closeEvent(self, event) -> None:
        self.settings.set("window_width", self.width())
        self.settings.set("window_height", self.height())
        super().closeEvent(event)
