"""Shared utilities for filesystem, logging, image discovery, and timing."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from time import monotonic
from typing import Iterable

from config import CACHE_DIR, LOG_DIR, MAP_CACHE_DIR, OUTPUT_DIR, RESOURCES_DIR, SUPPORTED_EXTENSIONS


def ensure_directories() -> None:
    """Create runtime directories used by the application."""
    for folder in (LOG_DIR, OUTPUT_DIR, RESOURCES_DIR, CACHE_DIR, MAP_CACHE_DIR):
        folder.mkdir(parents=True, exist_ok=True)


def configure_logging() -> None:
    """Configure rotating file and console logging."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOG_DIR / "twality-gmark.log"
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers.clear()

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        "%Y-%m-%d %H:%M:%S",
    )
    file_handler = RotatingFileHandler(log_file, maxBytes=2_000_000, backupCount=5, encoding="utf-8")
    file_handler.setFormatter(formatter)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root.addHandler(file_handler)
    root.addHandler(console_handler)


def discover_images(folder: Path, recursive: bool = True) -> list[Path]:
    """Return supported image paths from a folder."""
    if not folder.exists() or not folder.is_dir():
        raise FileNotFoundError(f"Input folder does not exist: {folder}")
    iterator: Iterable[Path] = folder.rglob("*") if recursive else folder.iterdir()
    return sorted(path for path in iterator if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS)


def unique_output_path(input_path: Path, output_folder: Path, suffix: str) -> Path:
    """Build a non-overwriting output filename for a stamped image."""
    output_folder.mkdir(parents=True, exist_ok=True)
    candidate = output_folder / f"{input_path.stem}{suffix}{input_path.suffix}"
    index = 1
    while candidate.exists():
        candidate = output_folder / f"{input_path.stem}{suffix}_{index}{input_path.suffix}"
        index += 1
    return candidate


class Stopwatch:
    """Small elapsed-time helper."""

    def __init__(self) -> None:
        self._start = monotonic()

    @property
    def elapsed(self) -> float:
        """Return elapsed seconds."""
        return monotonic() - self._start


def human_eta(done: int, total: int, elapsed: float) -> str:
    """Estimate remaining time from completed work."""
    if done <= 0 or total <= done:
        return "00:00"
    rate = elapsed / done
    remaining = int(rate * (total - done))
    minutes, seconds = divmod(remaining, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"
