"""Main window for Twality GMark Pro."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QThread, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QHeaderView,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from config import APP_NAME, CACHE_DIR
from core.batch_processor import BatchProcessor, ProcessingResult
from core.exif_reader import ExifReader
from core.exif_writer import ExifWriter
from core.overlay_renderer import OverlayOptions, OverlayRenderer, TIMESTAMP_FORMATS
from core.reverse_geocoder import ReverseGeocoder
from core.settings import SettingsStore
from core.static_map import StaticMapRenderer
from core.theme_manager import ThemeManager
from core.utils import Stopwatch, discover_images, human_eta
from ui.help_dialog import AboutDialog, HelpDialog
from ui.preview_dialog import PreviewDialog
from ui.settings_dialog import SettingsDialog
from ui.watermark_dialog import WatermarkDialog
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
        watermark_action = QAction("Watermark Settings", self)
        watermark_action.triggered.connect(self.show_watermark_settings)
        file_menu.addAction(preview_action)
        file_menu.addAction(settings_action)
        file_menu.addAction(watermark_action)

        help_menu = menu.addMenu("&Help")
        help_action = QAction("Help Contents", self)
        help_action.triggered.connect(self.show_help)
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(help_action)
        help_menu.addAction(about_action)

        root = QWidget()
        layout = QVBoxLayout(root)
        self.input_edit = QLineEdit(str(self.settings.get("last_input_folder", "")))
        self.output_edit = QLineEdit(str(self.settings.get("last_output_folder", "")))
        self.input_edit.editingFinished.connect(self.update_output_folder_from_input)
        layout.addLayout(self._folder_row("Input Folder", self.input_edit, self.pick_input))
        layout.addLayout(self._folder_row("Output Folder", self.output_edit, self.pick_output))

        controls = QHBoxLayout()
        self.geo_group = QGroupBox("Geo Stamping")
        self.geo_group.setCheckable(True)
        self.geo_group.setChecked(bool(self.settings.get("print_geo_stamp", True)))
        geo_layout = QFormLayout(self.geo_group)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(self.themes.names())
        self.theme_combo.setCurrentText(str(self.settings.get("theme", "Professional")).replace("_", " ").title())
        self.position_combo = QComboBox()
        self.position_combo.addItems(["bottom", "top", "left", "right"])
        self.position_combo.setCurrentText(str(self.settings.get("overlay_position", "bottom")))
        self.timestamp_combo = QComboBox()
        for key, label, _ in TIMESTAMP_FORMATS:
            self.timestamp_combo.addItem(label, key)
        self._set_timestamp_combo(str(self.settings.get("timestamp_format", "yyyy-mm-dd_24h")))
        geo_layout.addRow("Theme", self.theme_combo)
        geo_layout.addRow("Placement", self.position_combo)
        geo_layout.addRow("Timestamp format", self.timestamp_combo)

        self.exif_group = QGroupBox("All Additional EXIF Data")
        self.exif_group.setCheckable(True)
        self.exif_group.setChecked(bool(self.settings.get("stamp_all_additional_exif", False)))

        self.watermark_group = QGroupBox("Print Watermark")
        self.watermark_group.setCheckable(True)
        self.watermark_group.setChecked(bool(self.settings.get("print_watermark", False)))
        watermark_layout = QVBoxLayout(self.watermark_group)
        watermark_button = QPushButton("Configure")
        watermark_button.clicked.connect(self.show_watermark_settings)
        watermark_layout.addWidget(watermark_button)
        watermark_layout.addStretch()

        controls.addWidget(self.geo_group, stretch=3)
        controls.addWidget(self.exif_group, stretch=1)
        controls.addWidget(self.watermark_group, stretch=1)
        layout.addLayout(controls)

        batch_controls = QHBoxLayout()
        self.recursive_check = QCheckBox("Recursive")
        self.recursive_check.setChecked(bool(self.settings.get("recursive", True)))
        self.workers_spin = QSpinBox()
        self.workers_spin.setRange(1, 32)
        self.workers_spin.setValue(int(self.settings.get("workers", 4)))
        for widget in (self.recursive_check, QLabel("Workers"), self.workers_spin):
            batch_controls.addWidget(widget)
        batch_controls.addStretch()
        layout.addLayout(batch_controls)

        actions = QHBoxLayout()
        self.start_button = QPushButton("Start")
        self.pause_button = QPushButton("Pause")
        self.resume_button = QPushButton("Resume")
        self.cancel_button = QPushButton("Cancel")
        self.start_button.clicked.connect(self.start_processing)
        self.pause_button.clicked.connect(self.processor.pause)
        self.resume_button.clicked.connect(self.processor.resume)
        self.cancel_button.clicked.connect(self.cancel_processing)
        for button in (self.start_button, self.pause_button, self.resume_button, self.cancel_button):
            actions.addWidget(button)
        layout.addLayout(actions)

        self.progress = QProgressBar()
        self.status_label = QLabel("Drop a folder or choose an input folder to begin.")
        layout.addWidget(self.progress)
        layout.addWidget(self.status_label)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Source", "Output", "Status", "Message"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Interactive)
        header.setSectionResizeMode(1, QHeaderView.Interactive)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.setColumnWidth(0, 360)
        self.table.setColumnWidth(1, 420)
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
            self.update_output_folder_from_input()

    def pick_output(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Choose output folder", self.output_edit.text())
        if folder:
            self.output_edit.setText(folder)
            self.settings.set("last_output_folder", folder)

    def update_output_folder_from_input(self) -> None:
        input_text = self.input_edit.text().strip()
        if not input_text:
            return
        output_folder = Path(input_text) / "gmark_output"
        self.output_edit.setText(str(output_folder))
        self.settings.set("last_input_folder", input_text)
        self.settings.set("last_output_folder", str(output_folder))

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:
        urls = event.mimeData().urls()
        if urls:
            path = Path(urls[0].toLocalFile())
            if path.is_dir():
                self.input_edit.setText(str(path))
                self.update_output_folder_from_input()

    def start_processing(self) -> None:
        if self.thread and self.thread.isRunning():
            QMessageBox.information(self, APP_NAME, "A batch is already running.")
            return
        input_folder = Path(self.input_edit.text())
        output_folder = Path(self.output_edit.text())
        try:
            paths = discover_images(input_folder, self.recursive_check.isChecked())
            self.total = len(paths)
        except FileNotFoundError as exc:
            QMessageBox.warning(self, APP_NAME, str(exc))
            return
        if self.total == 0:
            QMessageBox.information(self, APP_NAME, "No supported images found.")
            return
        if not self._has_selected_stamping_option():
            QMessageBox.warning(self, APP_NAME, "Select at least one stamping option.")
            return
        self._save_processing_controls()
        self.table.setRowCount(0)
        self.done = 0
        self.stopwatch = Stopwatch()
        self.progress.setRange(0, self.total)
        self.progress.setValue(0)
        options = self._current_overlay_options()
        exif_only_paths = self._confirm_exif_only_paths(paths, options) if options.stamp_all_additional_exif else set()
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
            exif_only_paths,
            paths,
        )
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.add_result)
        self.worker.finished.connect(self.finish_processing)
        self.worker.finished.connect(self.thread.quit)
        self.thread.finished.connect(self._clear_worker)
        self.thread.start()

    def cancel_processing(self) -> None:
        self.processor.cancel()
        self.status_label.setText("Cancelling current batch...")

    def add_result(self, result: ProcessingResult) -> None:
        self.done += 1
        self.progress.setValue(self.done)
        self.status_label.setText(f"{self.done}/{self.total} complete · ETA {human_eta(self.done, self.total, self.stopwatch.elapsed)}")
        row = self.table.rowCount()
        self.table.insertRow(row)
        values = [str(result.source), str(result.output or ""), result.status, result.message]
        for column, value in enumerate(values):
            item = QTableWidgetItem(value)
            item.setToolTip(value)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, column, item)

    def finish_processing(self, results: list[ProcessingResult]) -> None:
        errors = sum(1 for result in results if result.status == "error")
        skipped = sum(1 for result in results if result.status == "skipped")
        self.status_label.setText(f"Finished {len(results)} images with {errors} errors and {skipped} skipped.")

    def _clear_worker(self) -> None:
        self.worker = None
        self.thread = None

    def preview_first(self) -> None:
        try:
            paths = discover_images(Path(self.input_edit.text()), self.recursive_check.isChecked())
        except FileNotFoundError as exc:
            QMessageBox.warning(self, APP_NAME, str(exc))
            return
        if not paths:
            QMessageBox.information(self, APP_NAME, "No image available for preview.")
            return
        if not self._has_selected_stamping_option():
            QMessageBox.warning(self, APP_NAME, "Select at least one stamping option.")
            return
        try:
            preview_path = self._render_preview(paths[0])
        except Exception as exc:
            QMessageBox.warning(self, APP_NAME, str(exc))
            return
        PreviewDialog(preview_path, self).exec()

    def show_settings(self) -> None:
        if SettingsDialog(self.settings, self).exec():
            self._set_timestamp_combo(str(self.settings.get("timestamp_format", "yyyy-mm-dd_24h")))
            self.exif_group.setChecked(bool(self.settings.get("stamp_all_additional_exif", False)))

    def show_watermark_settings(self) -> None:
        WatermarkDialog(self.settings, self).exec()

    def show_help(self) -> None:
        HelpDialog(self).exec()

    def show_about(self) -> None:
        AboutDialog(self).exec()

    def _confirm_exif_only_paths(self, paths: list[Path], options: OverlayOptions) -> set[Path]:
        allowed: set[Path] = set()
        apply_to_all: bool | None = None
        for path in paths:
            try:
                metadata = self.processor.exif_reader.read(path)
            except Exception:
                continue
            if metadata.gps is not None or not self.processor.renderer.has_stampable_exif(metadata, options):
                continue
            if apply_to_all is not None:
                if apply_to_all:
                    allowed.add(path)
                continue
            should_stamp, do_for_all = self._ask_stamp_remaining_exif(path)
            if should_stamp:
                allowed.add(path)
            if do_for_all:
                apply_to_all = should_stamp
        return allowed

    def _ask_stamp_remaining_exif(self, path: Path) -> tuple[bool, bool]:
        checkbox = QCheckBox("Do this for all items in this batch")
        message = QMessageBox(self)
        message.setIcon(QMessageBox.Warning)
        message.setWindowTitle(APP_NAME)
        message.setText("No GPS Data available. Do you want to stamp remaining EXIF data?")
        message.setInformativeText(str(path))
        message.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        message.setDefaultButton(QMessageBox.Yes)
        message.setCheckBox(checkbox)
        return message.exec() == QMessageBox.Yes, checkbox.isChecked()

    def _set_timestamp_combo(self, timestamp_format: str) -> None:
        index = self.timestamp_combo.findData(timestamp_format)
        self.timestamp_combo.setCurrentIndex(max(0, index))

    def _current_overlay_options(self) -> OverlayOptions:
        return OverlayOptions(
            position=self.position_combo.currentText(),
            quality=int(self.settings.get("output_quality", 95)),
            map_width=int(self.settings.get("map_width", 320)),
            map_height=int(self.settings.get("map_height", 220)),
            font_size=int(self.settings.get("font_size", 24)),
            print_geo_stamp=self.geo_group.isChecked(),
            timestamp_format=str(self.timestamp_combo.currentData() or "yyyy-mm-dd_24h"),
            stamp_all_additional_exif=self.exif_group.isChecked(),
            print_watermark=self.watermark_group.isChecked(),
            watermark_type=str(self.settings.get("watermark_type", "text")),
            watermark_text=str(self.settings.get("watermark_text", "Twality GMark Pro")),
            watermark_image_path=str(self.settings.get("watermark_image_path", "")),
            watermark_position=str(self.settings.get("watermark_position", "bottom_right")),
            watermark_opacity=int(self.settings.get("watermark_opacity", 45)),
            watermark_size=int(self.settings.get("watermark_size", 18)),
            watermark_margin=int(self.settings.get("watermark_margin", 4)),
        )

    def _render_preview(self, path: Path) -> Path:
        self._save_processing_controls()
        options = self._current_overlay_options()
        metadata = self.processor.exif_reader.read(path)
        effective_options, address, message = self.processor._effective_options(path, metadata, options, str(self.settings.get("language", "en")), {path})
        if effective_options is None:
            raise RuntimeError(message)
        preview_dir = CACHE_DIR / "previews"
        preview_dir.mkdir(parents=True, exist_ok=True)
        preview_path = preview_dir / f"{path.stem}_preview.jpg"
        self.processor.renderer.render(path, preview_path, metadata, address, self.themes.get(self.theme_combo.currentText()), effective_options)
        return preview_path

    def _save_processing_controls(self) -> None:
        self.settings.set("theme", self.theme_combo.currentText().lower().replace(" ", "_"))
        self.settings.set("overlay_position", self.position_combo.currentText())
        self.settings.set("print_geo_stamp", self.geo_group.isChecked())
        self.settings.set("timestamp_format", self.timestamp_combo.currentData())
        self.settings.set("stamp_all_additional_exif", self.exif_group.isChecked())
        self.settings.set("print_watermark", self.watermark_group.isChecked())
        self.settings.set("recursive", self.recursive_check.isChecked())
        self.settings.set("workers", self.workers_spin.value())

    def _has_selected_stamping_option(self) -> bool:
        return self.geo_group.isChecked() or self.exif_group.isChecked() or self.watermark_group.isChecked()

    def closeEvent(self, event) -> None:
        self.settings.set("window_width", self.width())
        self.settings.set("window_height", self.height())
        if self.thread and self.thread.isRunning():
            self.processor.cancel()
            self.thread.quit()
            if not self.thread.wait(3000):
                self.thread.terminate()
                self.thread.wait(1000)
        super().closeEvent(event)
