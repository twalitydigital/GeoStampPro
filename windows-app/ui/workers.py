"""Qt worker objects for non-blocking batch processing."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot

from core.batch_processor import BatchProcessor, ProcessingResult
from core.overlay_renderer import OverlayOptions
from core.theme_manager import Theme


class BatchWorker(QObject):
    """Run batch processing in a QThread."""

    progress = Signal(object)
    finished = Signal(list)

    def __init__(
        self,
        processor: BatchProcessor,
        input_folder: Path,
        output_folder: Path,
        recursive: bool,
        workers: int,
        theme: Theme,
        options: OverlayOptions,
        language: str,
    ) -> None:
        super().__init__()
        self.processor = processor
        self.input_folder = input_folder
        self.output_folder = output_folder
        self.recursive = recursive
        self.workers = workers
        self.theme = theme
        self.options = options
        self.language = language

    @Slot()
    def run(self) -> None:
        """Execute the batch job."""
        results = self.processor.process_folder(
            self.input_folder,
            self.output_folder,
            self.recursive,
            self.workers,
            self.theme,
            self.options,
            self.language,
            self._emit_progress,
        )
        self.finished.emit(results)

    def _emit_progress(self, result: ProcessingResult) -> None:
        self.progress.emit(result)
