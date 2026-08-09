"""Batch orchestration for stamping photos."""

from __future__ import annotations

import logging
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from threading import Event
from typing import Callable

from config import DEFAULT_OUTPUT_SUFFIX, JPEG_EXTENSIONS
from core.exif_reader import ExifReader
from core.exif_writer import ExifWriter
from core.overlay_renderer import OverlayOptions, OverlayRenderer
from core.reverse_geocoder import ReverseGeocoder
from core.theme_manager import Theme
from core.utils import discover_images, unique_output_path

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class ProcessingResult:
    """Outcome for one image."""

    source: Path
    output: Path | None
    status: str
    message: str = ""


class BatchProcessor:
    """Process folders of images using a thread pool."""

    def __init__(
        self,
        exif_reader: ExifReader,
        exif_writer: ExifWriter,
        geocoder: ReverseGeocoder,
        renderer: OverlayRenderer,
    ) -> None:
        self.exif_reader = exif_reader
        self.exif_writer = exif_writer
        self.geocoder = geocoder
        self.renderer = renderer
        self.pause_event = Event()
        self.cancel_event = Event()
        self.pause_event.set()

    def pause(self) -> None:
        self.pause_event.clear()

    def resume(self) -> None:
        self.pause_event.set()

    def cancel(self) -> None:
        self.cancel_event.set()
        self.pause_event.set()

    def process_folder(
        self,
        input_folder: Path,
        output_folder: Path,
        recursive: bool,
        workers: int,
        theme: Theme,
        options: OverlayOptions,
        language: str,
        progress: Callable[[ProcessingResult], None],
    ) -> list[ProcessingResult]:
        """Process all supported images from a folder."""
        paths = discover_images(input_folder, recursive)
        results: list[ProcessingResult] = []
        with ThreadPoolExecutor(max_workers=max(1, workers)) as executor:
            futures: list[Future[ProcessingResult]] = [
                executor.submit(self._process_one, path, output_folder, theme, options, language) for path in paths
            ]
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
                progress(result)
                if self.cancel_event.is_set():
                    break
        return results

    def _process_one(self, path: Path, output_folder: Path, theme: Theme, options: OverlayOptions, language: str) -> ProcessingResult:
        self.pause_event.wait()
        if self.cancel_event.is_set():
            return ProcessingResult(path, None, "cancelled", "Cancelled by user.")
        try:
            metadata = self.exif_reader.read(path)
            if metadata.gps is None:
                return ProcessingResult(path, None, "skipped", "No GPS metadata.")
            output = unique_output_path(path, output_folder, DEFAULT_OUTPUT_SUFFIX)
            address = self.geocoder.lookup(metadata.gps, language=language)
            self.renderer.render(path, output, metadata, address, theme, options)
            if path.suffix.lower() in JPEG_EXTENSIONS:
                self.exif_writer.copy_all_metadata(path, output)
                if not self.exif_writer.verify_metadata(path, output):
                    return ProcessingResult(path, output, "error", "Metadata verification failed.")
            else:
                LOGGER.warning("EXIF preservation warning for non-JPEG output: %s", path)
                return ProcessingResult(path, output, "warning", "Stamped; full EXIF preservation is only guaranteed for JPEG.")
            return ProcessingResult(path, output, "processed", "OK")
        except Exception as exc:
            LOGGER.exception("Failed to process %s", path)
            return ProcessingResult(path, None, "error", str(exc))
