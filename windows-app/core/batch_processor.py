"""Batch orchestration for stamping photos."""

from __future__ import annotations

import logging
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from dataclasses import replace
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
        exif_only_paths: set[Path] | None = None,
        paths: list[Path] | None = None,
    ) -> list[ProcessingResult]:
        """Process all supported images from a folder."""
        self.cancel_event.clear()
        self.pause_event.set()
        paths = paths or discover_images(input_folder, recursive)
        exif_only_paths = exif_only_paths or set()
        results: list[ProcessingResult] = []
        executor = ThreadPoolExecutor(max_workers=max(1, workers))
        futures: list[Future[ProcessingResult]] = [
            executor.submit(self._process_one, path, output_folder, theme, options, language, exif_only_paths) for path in paths
        ]
        try:
            for future in as_completed(futures):
                if self.cancel_event.is_set():
                    for pending in futures:
                        pending.cancel()
                    break
                result = future.result()
                results.append(result)
                progress(result)
        finally:
            executor.shutdown(wait=not self.cancel_event.is_set(), cancel_futures=True)
        return results

    def _process_one(
        self,
        path: Path,
        output_folder: Path,
        theme: Theme,
        options: OverlayOptions,
        language: str,
        exif_only_paths: set[Path],
    ) -> ProcessingResult:
        self.pause_event.wait()
        if self.cancel_event.is_set():
            return ProcessingResult(path, None, "cancelled", "Cancelled by user.")
        try:
            metadata = self.exif_reader.read(path)
            effective_options, address, message = self._effective_options(path, metadata, options, language, exif_only_paths)
            if effective_options is None:
                return ProcessingResult(path, None, "skipped", message)
            output = unique_output_path(path, output_folder, DEFAULT_OUTPUT_SUFFIX)
            self.renderer.render(path, output, metadata, address, theme, effective_options)
            if path.suffix.lower() in JPEG_EXTENSIONS:
                self.exif_writer.copy_all_metadata(path, output)
                if not self.exif_writer.verify_metadata(path, output):
                    return ProcessingResult(path, output, "error", "Metadata verification failed.")
            else:
                LOGGER.warning("EXIF preservation warning for non-JPEG output: %s", path)
                return ProcessingResult(path, output, "warning", f"{message}; full EXIF preservation is only guaranteed for JPEG.")
            return ProcessingResult(path, output, "processed", message)
        except Exception as exc:
            LOGGER.exception("Failed to process %s", path)
            return ProcessingResult(path, None, "error", str(exc))

    def _effective_options(
        self,
        path: Path,
        metadata,
        options: OverlayOptions,
        language: str,
        exif_only_paths: set[Path],
    ) -> tuple[OverlayOptions | None, str, str]:
        has_gps = metadata.gps is not None
        stamp_geo = options.print_geo_stamp and has_gps
        stamp_exif = options.stamp_all_additional_exif and self.renderer.has_stampable_exif(metadata, options)
        if options.stamp_all_additional_exif and not has_gps and path not in exif_only_paths:
            stamp_exif = False
        stamp_watermark = options.print_watermark

        if not (stamp_geo or stamp_exif or stamp_watermark):
            if options.print_geo_stamp and not has_gps:
                if options.stamp_all_additional_exif:
                    return None, "", "No GPS Data available and remaining EXIF stamping was not selected."
                return None, "", "No GPS metadata."
            if options.stamp_all_additional_exif:
                return None, "", "No EXIF data available."
            return None, "", "No selected stamping options could be applied."

        address = self.geocoder.lookup(metadata.gps, language=language) if stamp_geo else "EXIF data"
        effective_options = replace(options, print_geo_stamp=stamp_geo, stamp_all_additional_exif=stamp_exif)
        stamped = []
        if stamp_geo:
            stamped.append("Geo stamp")
        if stamp_exif:
            stamped.append("EXIF data")
        if stamp_watermark:
            stamped.append("watermark")
        return effective_options, address, "Stamped " + ", ".join(stamped) + "."
