"""Static OpenStreetMap rendering."""

from __future__ import annotations

import logging
from pathlib import Path

from PIL import Image, ImageDraw
from staticmap import CircleMarker, StaticMap

from config import MAP_CACHE_DIR
from core.gps_parser import GPSCoordinate

LOGGER = logging.getLogger(__name__)


class StaticMapRenderer:
    """Render a small map with a red pin and north indicator."""

    def __init__(self, cache_dir: Path = MAP_CACHE_DIR) -> None:
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def render(self, coordinate: GPSCoordinate, width: int, height: int) -> Image.Image:
        """Create or load a cached map image."""
        key = f"{coordinate.latitude:.5f}_{coordinate.longitude:.5f}_{width}x{height}.png"
        cache_path = self.cache_dir / key
        if cache_path.exists():
            return Image.open(cache_path).convert("RGBA")
        try:
            static_map = StaticMap(width, height, url_template="https://tile.openstreetmap.org/{z}/{x}/{y}.png")
            static_map.add_marker(CircleMarker((coordinate.longitude, coordinate.latitude), "red", 14))
            image = static_map.render(zoom=15).convert("RGBA")
        except Exception as exc:
            LOGGER.warning("Map rendering failed, using fallback map: %s", exc)
            image = Image.new("RGBA", (width, height), (36, 43, 50, 255))
            draw = ImageDraw.Draw(image)
            draw.text((16, height // 2 - 10), f"{coordinate.latitude:.5f}, {coordinate.longitude:.5f}", fill=(255, 255, 255, 255))
        image = self._decorate(image)
        image.save(cache_path)
        return image

    def _decorate(self, image: Image.Image) -> Image.Image:
        draw = ImageDraw.Draw(image)
        draw.rounded_rectangle((0, 0, image.width - 1, image.height - 1), radius=18, outline=(255, 255, 255, 210), width=3)
        draw.polygon([(image.width - 34, 18), (image.width - 22, 48), (image.width - 46, 48)], fill=(255, 255, 255, 230))
        draw.text((image.width - 39, 50), "N", fill=(255, 255, 255, 245))
        return image
