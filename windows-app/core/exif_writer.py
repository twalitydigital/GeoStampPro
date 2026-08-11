"""Metadata preservation using ExifTool."""

from __future__ import annotations

import json
import logging
import platform
import shutil
import subprocess
import sys
from pathlib import Path

from config import APP_METADATA_TOOL, EXIFTOOL_EXE, VENDOR_DIR

LOGGER = logging.getLogger(__name__)
EXIFTOOL_TIMEOUT_SECONDS = 30
WINDOWS_NO_WINDOW_FLAGS = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0


class ExifToolMissingError(RuntimeError):
    """Raised when ExifTool is not bundled and not available on PATH."""


class ExifWriter:
    """Copy and verify all metadata from an original file to an output file."""

    def __init__(self, executable: str | None = None) -> None:
        self.executable = executable or self._resolve_executable()

    @staticmethod
    def _resolve_executable() -> str:
        """Prefer the private bundled ExifTool, then fall back to PATH."""
        if EXIFTOOL_EXE.exists():
            return str(EXIFTOOL_EXE)
        machine = platform.machine().lower()
        preferred_arch = "x86" if machine in {"x86", "i386", "i686"} else "x64"
        fallback_arch = "x64" if preferred_arch == "x86" else "x86"
        for arch in (preferred_arch, fallback_arch):
            candidate = VENDOR_DIR / "exiftool" / arch / "exiftool.exe"
            if candidate.exists():
                return str(candidate)
        return "exiftool"

    def available(self) -> bool:
        """Return True if ExifTool can be executed."""
        executable_path = Path(self.executable)
        if executable_path.is_absolute():
            return executable_path.exists()
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
            f"-XMP-dc:Subject+={APP_METADATA_TOOL}",
            str(output),
        ]
        LOGGER.info("Copying metadata with ExifTool: %s", output)
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
                timeout=EXIFTOOL_TIMEOUT_SECONDS,
                creationflags=WINDOWS_NO_WINDOW_FLAGS,
            )
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
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
                timeout=EXIFTOOL_TIMEOUT_SECONDS,
                creationflags=WINDOWS_NO_WINDOW_FLAGS,
            )
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
