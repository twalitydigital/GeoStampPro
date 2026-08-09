"""Reverse geocoding with local caching and Nominatim rate limiting."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from time import monotonic, sleep

import requests

from config import GEOCODE_CACHE, NOMINATIM_URL, USER_AGENT
from core.gps_parser import GPSCoordinate

LOGGER = logging.getLogger(__name__)


class ReverseGeocoder:
    """Resolve coordinates into an address, falling back gracefully offline."""

    def __init__(self, cache_path: Path = GEOCODE_CACHE) -> None:
        self.cache_path = cache_path
        self.cache: dict[str, str] = {}
        self._last_request = 0.0
        self.load()

    def load(self) -> None:
        """Load cached geocoding responses."""
        if self.cache_path.exists():
            try:
                self.cache = json.loads(self.cache_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                self.cache = {}

    def save(self) -> None:
        """Save cache to disk."""
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache_path.write_text(json.dumps(self.cache, indent=2), encoding="utf-8")

    def lookup(self, coordinate: GPSCoordinate, language: str = "en") -> str:
        """Return a display address or a coordinate string when offline."""
        key = f"{coordinate.latitude:.6f},{coordinate.longitude:.6f},{language}"
        if key in self.cache:
            return self.cache[key]
        elapsed = monotonic() - self._last_request
        if elapsed < 1.1:
            sleep(1.1 - elapsed)
        try:
            response = requests.get(
                NOMINATIM_URL,
                params={
                    "format": "jsonv2",
                    "lat": coordinate.latitude,
                    "lon": coordinate.longitude,
                    "accept-language": language,
                },
                headers={"User-Agent": USER_AGENT},
                timeout=8,
            )
            self._last_request = monotonic()
            response.raise_for_status()
            data = response.json()
            address = data.get("display_name") or self._fallback(coordinate)
        except requests.RequestException as exc:
            LOGGER.warning("Reverse geocoding unavailable: %s", exc)
            address = self._fallback(coordinate)
        self.cache[key] = address
        self.save()
        return address

    def _fallback(self, coordinate: GPSCoordinate) -> str:
        return f"{coordinate.latitude:.6f}, {coordinate.longitude:.6f}"
