"""Image stamping and overlay composition."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
import re

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps
import piexif

from core.exif_reader import PhotoMetadata
from core.static_map import StaticMapRenderer
from core.theme_manager import Theme

TIMESTAMP_FORMATS = [
    ("yyyy-mm-dd_24h", "yyyy-mm-dd hh:mm:ss", "%Y-%m-%d %H:%M:%S"),
    ("dd-mm-yyyy_24h", "dd-mm-yyyy hh:mm:ss", "%d-%m-%Y %H:%M:%S"),
    ("mm-dd-yyyy_12h", "mm-dd-yyyy hh:mm:ss AM/PM", "%m-%d-%Y %I:%M:%S %p"),
    ("dd_mmm_yyyy_12h", "dd mmm yyyy hh:mm AM/PM", "%d %b %Y %I:%M %p"),
    ("exif_original", "EXIF original", ""),
]

DATETIME_TAG_NAMES = {
    "DateTime",
    "DateTimeOriginal",
    "DateTimeDigitized",
    "GPSDateStamp",
    "GPSTimeStamp",
}

PRIMARY_TAG_NAMES = {
    "DateTimeOriginal",
    "GPSLatitude",
    "GPSLongitude",
    "GPSAltitude",
    "Make",
    "Model",
}

SKIPPED_ADDITIONAL_EXIF_TAGS = {
    "MakerNote",
    "PrintImageMatching",
    "ComponentsConfiguration",
    "FileSource",
    "SceneType",
}

MAX_EXIF_ROWS = 48
MAX_EXIF_VALUE_LENGTH = 220


@dataclass(frozen=True)
class OverlayOptions:
    """User-controlled overlay rendering options."""

    position: str
    quality: int
    map_width: int
    map_height: int
    font_size: int
    print_geo_stamp: bool = True
    timestamp_format: str = "yyyy-mm-dd_24h"
    stamp_all_additional_exif: bool = False
    print_watermark: bool = False
    watermark_type: str = "text"
    watermark_text: str = "Twality GMark Pro"
    watermark_image_path: str = ""
    watermark_position: str = "bottom_right"
    watermark_opacity: int = 45
    watermark_size: int = 18
    watermark_margin: int = 4


class OverlayRenderer:
    """Render GPS information panels onto images."""

    def __init__(self, map_renderer: StaticMapRenderer) -> None:
        self.map_renderer = map_renderer

    def render(self, source: Path, destination: Path, metadata: PhotoMetadata, address: str, theme: Theme, options: OverlayOptions) -> None:
        """Create a stamped output image without modifying the source."""
        with Image.open(source) as opened:
            image = ImageOps.exif_transpose(opened).convert("RGBA")
            icc_profile = opened.info.get("icc_profile")
        overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
        if options.print_geo_stamp or options.stamp_all_additional_exif:
            panel = self._build_panel(image.size, metadata, address, theme, options)
            x, y = self._panel_position(image.size, panel.size, options.position)
            overlay.alpha_composite(panel, (x, y))
        if options.print_watermark:
            self._draw_watermark(overlay, image.size, theme, options)
        result = Image.alpha_composite(image, overlay).convert("RGB")
        save_kwargs = {"quality": options.quality, "subsampling": 0}
        if icc_profile:
            save_kwargs["icc_profile"] = icc_profile
        destination.parent.mkdir(parents=True, exist_ok=True)
        result.save(destination, **save_kwargs)

    def has_stampable_exif(self, metadata: PhotoMetadata, options: OverlayOptions) -> bool:
        """Return True when there is non-GPS EXIF content worth stamping."""
        direct_values = [
            metadata.datetime_original,
            metadata.camera_make,
            metadata.camera_model,
            metadata.lens,
            metadata.exposure,
            metadata.iso,
        ]
        if any(self._has_exif_value(value) for value in direct_values):
            return True
        if options.stamp_all_additional_exif:
            return bool(self._additional_exif_rows(metadata, options.timestamp_format, include_gps=False))
        return False

    def _build_panel(self, image_size: tuple[int, int], metadata: PhotoMetadata, address: str, theme: Theme, options: OverlayOptions) -> Image.Image:
        width, height = image_size
        horizontal = options.position in {"top", "bottom"}
        panel_width = int(width * 0.94) if horizontal else min(int(width * 0.42), 720)
        padding = 30
        rows = self._metadata_rows(metadata, options)
        row_height = int(options.font_size * 1.35)
        text_block_height = int(options.font_size * 2.6) + row_height * max(1, len(rows))
        desired_height = padding * 2 + max(options.map_height, text_block_height)
        max_height = max(180, height - max(24, int(min(image_size) * 0.025)) * 2)
        base_height = max(options.map_height + 48, int(height * 0.23)) if horizontal else int(height * 0.86)
        panel_height = min(max(base_height, desired_height), max_height)
        panel = Image.new("RGBA", (panel_width, panel_height), (0, 0, 0, 0))
        shadow = Image.new("RGBA", panel.size, (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow)
        shadow_draw.rounded_rectangle((8, 8, panel_width - 8, panel_height - 8), radius=26, fill=theme.shadow_color)
        shadow = shadow.filter(ImageFilter.GaussianBlur(10))
        panel.alpha_composite(shadow)
        draw = ImageDraw.Draw(panel)
        draw.rounded_rectangle((0, 0, panel_width - 16, panel_height - 16), radius=26, fill=theme.panel_color)

        font_regular = self._font(theme.font_family, options.font_size)
        font_small = self._font(theme.font_family, max(16, int(options.font_size * 0.72)))
        font_title = self._font(theme.font_family, max(20, int(options.font_size * 1.08)))
        map_image = self.map_renderer.render(metadata.gps, options.map_width, options.map_height) if metadata.gps else None

        text_x = padding
        map_x = panel_width - options.map_width - padding - 16
        if map_image and map_x > panel_width * 0.45:
            panel.alpha_composite(map_image, (map_x, padding))
            text_limit = map_x - padding
        else:
            text_limit = panel_width - padding * 2
        y = padding
        self._draw_wrapped(draw, address, (text_x, y), text_limit, font_title, theme.text_color, max_lines=2)
        y += int(options.font_size * 2.6)
        max_y = panel_height - padding - int(options.font_size * 1.35)
        overflow = 0
        for label, value in rows:
            if y > max_y:
                overflow += 1
                continue
            value_x = text_x + int(options.font_size * 6)
            value_width = max(80, text_limit - (value_x - text_x))
            draw.text((text_x, y), self._ellipsize(draw, label.upper(), font_small, value_x - text_x - 8), font=font_small, fill=theme.accent_color)
            draw.text((value_x, y), self._ellipsize(draw, value, font_regular, value_width), font=font_regular, fill=theme.text_color)
            y += int(options.font_size * 1.35)
        if overflow:
            draw.text((text_x, max_y), f"+ {overflow} more EXIF fields", font=font_small, fill=theme.accent_color)
        return panel

    def _metadata_rows(self, metadata: PhotoMetadata, options: OverlayOptions) -> list[tuple[str, str]]:
        gps = metadata.gps
        rows: list[tuple[str, str]] = []
        if options.print_geo_stamp and gps:
            rows.extend(
                [
                    ("Latitude", f"{gps.latitude:.6f}"),
                    ("Longitude", f"{gps.longitude:.6f}"),
                    ("Altitude", f"{gps.altitude_m:.1f} m" if gps.altitude_m is not None else "Unknown"),
                ]
            )
        if options.print_geo_stamp or options.stamp_all_additional_exif:
            rows.extend(
                [
                    ("Captured", self._format_datetime(metadata.datetime_original, options.timestamp_format)),
                    ("Camera", " ".join(part for part in [metadata.camera_make, metadata.camera_model] if part).strip() or "Unknown"),
                ]
            )
        if options.stamp_all_additional_exif:
            rows.extend(self._direct_exif_rows(metadata))
            rows.extend(self._additional_exif_rows(metadata, options.timestamp_format))
        return rows[:MAX_EXIF_ROWS]

    def _direct_exif_rows(self, metadata: PhotoMetadata) -> list[tuple[str, str]]:
        rows = [
            ("Lens", metadata.lens),
            ("Exposure", metadata.exposure),
            ("ISO", metadata.iso),
        ]
        return [(label, value) for label, value in rows if self._has_exif_value(value)]

    def _additional_exif_rows(self, metadata: PhotoMetadata, timestamp_format: str, include_gps: bool = True) -> list[tuple[str, str]]:
        rows: list[tuple[str, str]] = []
        for ifd_name, ifd_values in metadata.raw_exif.items():
            if ifd_name == "thumbnail" or not isinstance(ifd_values, dict):
                continue
            if ifd_name == "GPS" and not include_gps:
                continue
            for tag_id, value in ifd_values.items():
                tag_name = piexif.TAGS.get(ifd_name, {}).get(tag_id, {}).get("name", str(tag_id))
                if tag_name in PRIMARY_TAG_NAMES or tag_name in SKIPPED_ADDITIONAL_EXIF_TAGS:
                    continue
                formatted = self._format_exif_value(tag_name, value, timestamp_format)
                if formatted:
                    rows.append((tag_name, formatted))
        return rows

    def _format_exif_value(self, tag_name: str, value: Any, timestamp_format: str) -> str:
        if tag_name == "GPSTimeStamp" and isinstance(value, tuple):
            return self._format_gps_time(value, timestamp_format)
        if tag_name in DATETIME_TAG_NAMES:
            return self._format_datetime(self._stringify_exif_value(value), timestamp_format)
        return self._stringify_exif_value(value)

    def _stringify_exif_value(self, value: Any) -> str:
        if value is None or value == b"":
            return ""
        if isinstance(value, bytes):
            if len(value) > MAX_EXIF_VALUE_LENGTH * 4:
                return ""
            return self._truncate_value(self._single_line(value.decode("utf-8", errors="ignore").strip("\x00 ")))
        if isinstance(value, tuple):
            return self._truncate_value(self._single_line(", ".join(self._stringify_exif_value(item) for item in value)))
        return self._truncate_value(self._single_line(str(value).strip()))

    def _has_exif_value(self, value: Any) -> bool:
        formatted = self._stringify_exif_value(value)
        return bool(formatted and formatted not in {"()", "None"})

    def _single_line(self, value: str) -> str:
        return re.sub(r"\s+", " ", value).strip()

    def _truncate_value(self, value: str) -> str:
        if len(value) <= MAX_EXIF_VALUE_LENGTH:
            return value
        return value[: MAX_EXIF_VALUE_LENGTH - 3].rstrip() + "..."

    def _format_datetime(self, value: str, timestamp_format: str) -> str:
        if not value:
            return "Unknown"
        if timestamp_format == "exif_original":
            return value
        format_map = {key: pattern for key, _, pattern in TIMESTAMP_FORMATS}
        output_format = format_map.get(timestamp_format, "%Y-%m-%d %H:%M:%S")
        parsed = self._parse_exif_datetime(value)
        return parsed.strftime(output_format) if parsed else value

    def _format_gps_time(self, value: tuple[Any, ...], timestamp_format: str) -> str:
        parts = [self._rational_to_int(part) for part in value[:3]]
        if len(parts) < 3 or any(part is None for part in parts):
            return self._stringify_exif_value(value)
        hour, minute, second = (int(part) for part in parts)
        parsed = datetime(1900, 1, 1, hour, minute, second)
        use_12_hour = timestamp_format in {"mm-dd-yyyy_12h", "dd_mmm_yyyy_12h"}
        pattern = "%I:%M:%S %p" if use_12_hour else "%H:%M:%S"
        return parsed.strftime(pattern)

    def _rational_to_int(self, value: Any) -> int | None:
        try:
            if isinstance(value, tuple) and len(value) == 2:
                numerator, denominator = value
                return round(numerator / denominator) if denominator else None
            return round(float(value))
        except (TypeError, ValueError):
            return None

    def _panel_position(self, image_size: tuple[int, int], panel_size: tuple[int, int], position: str) -> tuple[int, int]:
        image_width, image_height = image_size
        panel_width, panel_height = panel_size
        margin = max(24, int(min(image_size) * 0.025))
        if position == "top":
            return ((image_width - panel_width) // 2, margin)
        if position == "left":
            return (margin, (image_height - panel_height) // 2)
        if position == "right":
            return (image_width - panel_width - margin, (image_height - panel_height) // 2)
        return ((image_width - panel_width) // 2, image_height - panel_height - margin)

    def _draw_watermark(self, overlay: Image.Image, image_size: tuple[int, int], theme: Theme, options: OverlayOptions) -> None:
        watermark = self._watermark_image(image_size, theme, options)
        if watermark is None:
            return
        opacity = max(0, min(100, options.watermark_opacity)) / 100
        alpha = watermark.getchannel("A").point(lambda value: int(value * opacity))
        watermark.putalpha(alpha)
        overlay.alpha_composite(watermark, self._watermark_position(image_size, watermark.size, options))

    def _watermark_image(self, image_size: tuple[int, int], theme: Theme, options: OverlayOptions) -> Image.Image | None:
        if options.watermark_type == "image" and options.watermark_image_path:
            path = Path(options.watermark_image_path)
            if path.exists():
                with Image.open(path) as opened:
                    watermark = opened.convert("RGBA")
                max_width = max(1, int(image_size[0] * max(1, options.watermark_size) / 100))
                ratio = max_width / watermark.width
                size = (max_width, max(1, int(watermark.height * ratio)))
                return watermark.resize(size, Image.Resampling.LANCZOS)
        text = options.watermark_text.strip()
        if not text:
            return None
        font_size = max(10, int(min(image_size) * max(1, options.watermark_size) / 1000))
        font = self._font(theme.font_family, font_size)
        measure = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
        draw = ImageDraw.Draw(measure)
        bbox = draw.textbbox((0, 0), text, font=font)
        padding = max(8, font_size // 3)
        width = max(1, bbox[2] - bbox[0] + padding * 2)
        height = max(1, bbox[3] - bbox[1] + padding * 2)
        watermark = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(watermark)
        draw.text((padding - bbox[0], padding - bbox[1]), text, font=font, fill=theme.text_color)
        return watermark

    def _watermark_position(self, image_size: tuple[int, int], watermark_size: tuple[int, int], options: OverlayOptions) -> tuple[int, int]:
        image_width, image_height = image_size
        watermark_width, watermark_height = watermark_size
        margin = max(0, int(min(image_size) * max(0, options.watermark_margin) / 100))
        left = margin
        center_x = (image_width - watermark_width) // 2
        right = image_width - watermark_width - margin
        top = margin
        center_y = (image_height - watermark_height) // 2
        bottom = image_height - watermark_height - margin
        positions = {
            "top_left": (left, top),
            "top_center": (center_x, top),
            "top_right": (right, top),
            "middle_left": (left, center_y),
            "middle_center": (center_x, center_y),
            "middle_right": (right, center_y),
            "bottom_left": (left, bottom),
            "bottom_center": (center_x, bottom),
            "bottom_right": (right, bottom),
        }
        return positions.get(options.watermark_position, positions["bottom_right"])

    def _font(self, family: str, size: int) -> ImageFont.ImageFont:
        try:
            return ImageFont.truetype(f"{family}.ttf", size)
        except OSError:
            try:
                return ImageFont.truetype("arial.ttf", size)
            except OSError:
                return ImageFont.load_default()

    def _draw_wrapped(self, draw: ImageDraw.ImageDraw, text: str, xy: tuple[int, int], width: int, font: ImageFont.ImageFont, fill: tuple[int, int, int, int], max_lines: int) -> None:
        words = text.split()
        lines: list[str] = []
        current = ""
        for word in words:
            trial = f"{current} {word}".strip()
            if draw.textlength(trial, font=font) <= width:
                current = trial
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        line_height = int(getattr(font, "size", 20) * 1.2)
        for index, line in enumerate(lines[:max_lines]):
            if index == max_lines - 1 and len(lines) > max_lines:
                line = line.rstrip(". ") + "..."
            draw.text((xy[0], xy[1] + index * line_height), line, font=font, fill=fill)

    def _ellipsize(self, draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, width: int) -> str:
        if draw.textlength(text, font=font) <= width:
            return text
        suffix = "..."
        low = 0
        high = len(text)
        while low < high:
            middle = (low + high + 1) // 2
            if draw.textlength(text[:middle] + suffix, font=font) <= width:
                low = middle
            else:
                high = middle - 1
        return text[:low].rstrip() + suffix if low else suffix

    def _parse_exif_datetime(self, value: str) -> datetime | None:
        normalized = value.strip().replace(":", "-", 2)
        for pattern in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%H:%M:%S"):
            try:
                return datetime.strptime(normalized, pattern)
            except ValueError:
                continue
        return None
