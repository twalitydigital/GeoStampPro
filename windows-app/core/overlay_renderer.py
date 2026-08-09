"""Image stamping and overlay composition."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

from core.exif_reader import PhotoMetadata
from core.static_map import StaticMapRenderer
from core.theme_manager import Theme


@dataclass(frozen=True)
class OverlayOptions:
    """User-controlled overlay rendering options."""

    position: str
    quality: int
    map_width: int
    map_height: int
    font_size: int
    logo_path: str = ""


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
        panel = self._build_panel(image.size, metadata, address, theme, options)
        x, y = self._panel_position(image.size, panel.size, options.position)
        overlay.alpha_composite(panel, (x, y))
        result = Image.alpha_composite(image, overlay).convert("RGB")
        save_kwargs = {"quality": options.quality, "subsampling": 0}
        if icc_profile:
            save_kwargs["icc_profile"] = icc_profile
        destination.parent.mkdir(parents=True, exist_ok=True)
        result.save(destination, **save_kwargs)

    def _build_panel(self, image_size: tuple[int, int], metadata: PhotoMetadata, address: str, theme: Theme, options: OverlayOptions) -> Image.Image:
        width, height = image_size
        horizontal = options.position in {"top", "bottom"}
        panel_width = int(width * 0.94) if horizontal else min(int(width * 0.42), 720)
        panel_height = max(options.map_height + 48, int(height * 0.23)) if horizontal else int(height * 0.86)
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

        padding = 30
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
        gps = metadata.gps
        rows = []
        if gps:
            rows.extend(
                [
                    ("Latitude", f"{gps.latitude:.6f}"),
                    ("Longitude", f"{gps.longitude:.6f}"),
                    ("Altitude", f"{gps.altitude_m:.1f} m" if gps.altitude_m is not None else "Unknown"),
                ]
            )
        date_value, time_value = self._split_datetime(metadata.datetime_original)
        rows.extend(
            [
                ("Date", date_value),
                ("Time", time_value),
                ("Camera", " ".join(part for part in [metadata.camera_make, metadata.camera_model] if part).strip() or "Unknown"),
            ]
        )
        for label, value in rows:
            draw.text((text_x, y), label.upper(), font=font_small, fill=theme.accent_color)
            draw.text((text_x + int(options.font_size * 6), y), value, font=font_regular, fill=theme.text_color)
            y += int(options.font_size * 1.35)
        return panel

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

    def _split_datetime(self, value: str) -> tuple[str, str]:
        if not value:
            return "Unknown", "Unknown"
        parts = value.replace(":", "-", 2).split()
        return (parts[0], parts[1] if len(parts) > 1 else "Unknown")
