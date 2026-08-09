"""Theme loading and validation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from config import THEMES_DIR


@dataclass(frozen=True)
class Theme:
    """Visual style for overlay rendering."""

    name: str
    panel_color: tuple[int, int, int, int]
    text_color: tuple[int, int, int, int]
    accent_color: tuple[int, int, int, int]
    muted_color: tuple[int, int, int, int]
    shadow_color: tuple[int, int, int, int]
    font_family: str = "Segoe UI"


class ThemeManager:
    """Load bundled and custom JSON themes."""

    def __init__(self, themes_dir: Path = THEMES_DIR) -> None:
        self.themes_dir = themes_dir
        self.themes: dict[str, Theme] = {}
        self.load()

    def load(self) -> None:
        """Load every valid JSON theme file."""
        self.themes_dir.mkdir(parents=True, exist_ok=True)
        self.themes = {}
        for path in sorted(self.themes_dir.glob("*.json")):
            theme = self._load_theme(path)
            self.themes[theme.name.lower().replace(" ", "_")] = theme
        if not self.themes:
            self.themes["professional"] = Theme(
                "Professional",
                (18, 24, 32, 218),
                (255, 255, 255, 255),
                (64, 180, 160, 255),
                (205, 214, 224, 255),
                (0, 0, 0, 130),
            )

    def _load_theme(self, path: Path) -> Theme:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return Theme(
            name=str(raw["name"]),
            panel_color=tuple(raw["panel_color"]),
            text_color=tuple(raw["text_color"]),
            accent_color=tuple(raw["accent_color"]),
            muted_color=tuple(raw["muted_color"]),
            shadow_color=tuple(raw["shadow_color"]),
            font_family=str(raw.get("font_family", "Segoe UI")),
        )

    def names(self) -> list[str]:
        """Return available theme display names."""
        return [theme.name for theme in self.themes.values()]

    def get(self, name: str) -> Theme:
        """Return a theme by key or display name."""
        key = name.lower().replace(" ", "_")
        return self.themes.get(key, self.themes.get("professional", next(iter(self.themes.values()))))
