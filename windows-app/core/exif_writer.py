"""Metadata preservation using ExifTool."""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
from pathlib import Path

LOGGER = logging.getLogger(__name__)
EXIFTOOL_TIMEOUT_SECONDS = 30


class ExifToolMissingError(RuntimeError):
    """Raised when exiftool is not installed or not on PATH."""


class ExifWriter:
    """Copy and verify all metadata from an original file to an output file."""

    def __init__(self, executable: str = "exiftool") -> None:
        self.executable = executable

    def available(self) -> bool:
        """Return True if ExifTool can be executed."""
        return shutil.which(self.executable) is not None

    def copy_all_metadata(self, original: Path, output: Path) -> None:
        """Run exiftool -TagsFromFile original -all:all output and remove backup."""
        if not self.available():
            raise ExifToolMissingError("ExifTool is required to preserve all metadata.")
        command = [
            self.executable,
            "-overwrite_original",
            "-TagsFromFile",
            str(original),
            "-all:all",
            str(output),
        ]
        LOGGER.info("Copying metadata with ExifTool: %s", output)
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=False, timeout=EXIFTOOL_TIMEOUT_SECONDS)
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError("ExifTool metadata copy timed out.") from exc
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "ExifTool metadata copy failed.")
        backup = output.with_name(output.name + "_original")
        if backup.exists():
            backup.unlink()

    def verify_metadata(self, original: Path, output: Path) -> bool:
        """Verify that key identity and GPS tags are present after metadata copy."""
        if not self.available():
            raise ExifToolMissingError("ExifTool is required to verify metadata.")
        tags = ["-GPSLatitude", "-GPSLongitude", "-DateTimeOriginal", "-Make", "-Model"]
        original_values = self._read_tags(original, tags)
        output_values = self._read_tags(output, tags)
        for key, value in original_values.items():
            if value and output_values.get(key) != value:
                LOGGER.error("Metadata verification mismatch for %s", key)
                return False
        return True

    def _read_tags(self, path: Path, tags: list[str]) -> dict[str, str]:
        command = [self.executable, "-j", "-s", *tags, str(path)]
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=False, timeout=EXIFTOOL_TIMEOUT_SECONDS)
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError("ExifTool metadata read timed out.") from exc
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "ExifTool metadata read failed.")
        try:
            records = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise RuntimeError("ExifTool metadata read returned invalid JSON.") from exc
        values = records[0] if records else {}
        return {tag.lstrip("-"): str(values.get(tag.lstrip("-"), "")).strip() for tag in tags}
