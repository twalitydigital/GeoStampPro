"""Application constants for Twality GeoStamp."""

from __future__ import annotations

from pathlib import Path

APP_NAME = "Twality GeoStamp"
APP_VERSION = "1.0.0"
ORG_NAME = "Twality"

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
THEMES_DIR = ASSETS_DIR / "themes"
FONTS_DIR = ASSETS_DIR / "fonts"
ICONS_DIR = ASSETS_DIR / "icons"
RESOURCES_DIR = BASE_DIR / "resources"
LOG_DIR = BASE_DIR / "logs"
OUTPUT_DIR = BASE_DIR / "output"
CACHE_DIR = RESOURCES_DIR / "cache"
GEOCODE_CACHE = CACHE_DIR / "geocode_cache.json"
MAP_CACHE_DIR = CACHE_DIR / "map_tiles"
SETTINGS_FILE = RESOURCES_DIR / "settings.json"

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".heic", ".heif"}
JPEG_EXTENSIONS = {".jpg", ".jpeg"}
DEFAULT_OUTPUT_SUFFIX = "_GeoStamped"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"
USER_AGENT = f"TwalityGeoStamp/{APP_VERSION} (metadata-preserving desktop app)"

DEFAULT_SETTINGS = {
    "theme": "professional",
    "output_quality": 95,
    "map_provider": "openstreetmap",
    "map_width": 320,
    "map_height": 220,
    "font_size": 24,
    "overlay_position": "bottom",
    "language": "en",
    "logo_path": "",
    "last_input_folder": "",
    "last_output_folder": "",
    "window_width": 1280,
    "window_height": 820,
    "recursive": True,
    "workers": 4,
}
