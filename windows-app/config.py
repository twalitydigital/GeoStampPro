"""Application constants for Twality GMark Pro."""

from __future__ import annotations

import os
import sys
from pathlib import Path

APP_NAME = "Twality GMark Pro"
APP_VERSION = "1.0.0"
ORG_NAME = "Twality"

BASE_DIR = Path(__file__).resolve().parent
BUNDLE_DIR = Path(getattr(sys, "_MEIPASS", BASE_DIR))
RUNTIME_DIR = Path(os.getenv("LOCALAPPDATA", BASE_DIR)) / "Twality GMark Pro" if getattr(sys, "frozen", False) else BASE_DIR / "resources"
ASSETS_DIR = BUNDLE_DIR / "assets"
VENDOR_DIR = BUNDLE_DIR / "vendor"
EXIFTOOL_EXE = VENDOR_DIR / "exiftool" / "exiftool.exe"
THEMES_DIR = ASSETS_DIR / "themes"
FONTS_DIR = ASSETS_DIR / "fonts"
ICONS_DIR = ASSETS_DIR / "icons"
RESOURCES_DIR = RUNTIME_DIR
LOG_DIR = RUNTIME_DIR / "logs"
OUTPUT_DIR = RUNTIME_DIR / "output"
CACHE_DIR = RESOURCES_DIR / "cache"
GEOCODE_CACHE = CACHE_DIR / "geocode_cache.json"
MAP_CACHE_DIR = CACHE_DIR / "map_tiles"
SETTINGS_FILE = RESOURCES_DIR / "settings.json"
APP_ICON = BUNDLE_DIR / "Logo.ico"

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".heic", ".heif"}
JPEG_EXTENSIONS = {".jpg", ".jpeg"}
DEFAULT_OUTPUT_SUFFIX = "_GMarked"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"
USER_AGENT = f"TwalityGMarkPro/{APP_VERSION} (metadata-preserving desktop app)"

DEFAULT_SETTINGS = {
    "theme": "professional",
    "output_quality": 95,
    "map_provider": "openstreetmap",
    "map_width": 320,
    "map_height": 220,
    "font_size": 24,
    "overlay_position": "bottom",
    "print_geo_stamp": True,
    "timestamp_format": "yyyy-mm-dd_24h",
    "stamp_all_additional_exif": False,
    "language": "en",
    "print_watermark": False,
    "watermark_type": "text",
    "watermark_text": "Twality GMark Pro",
    "watermark_image_path": "",
    "watermark_position": "bottom_right",
    "watermark_opacity": 45,
    "watermark_size": 18,
    "watermark_margin": 4,
    "last_input_folder": "",
    "last_output_folder": "",
    "window_width": 1280,
    "window_height": 820,
    "recursive": True,
    "workers": 4,
}
