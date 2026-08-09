"""JSON-backed application settings."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from config import DEFAULT_SETTINGS, SETTINGS_FILE


class SettingsStore:
    """Persist user preferences in a local JSON file."""

    def __init__(self, path: Path = SETTINGS_FILE) -> None:
        self.path = path
        self.data: dict[str, Any] = dict(DEFAULT_SETTINGS)
        self.load()

    def load(self) -> None:
        """Load settings, falling back to defaults for missing keys."""
        if not self.path.exists():
            self.save()
            return
        try:
            loaded = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                self.data.update(loaded)
        except (OSError, json.JSONDecodeError):
            self.data = dict(DEFAULT_SETTINGS)

    def save(self) -> None:
        """Write current settings to disk."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, indent=2), encoding="utf-8")

    def get(self, key: str, default: Any = None) -> Any:
        """Return a setting value."""
        return self.data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set and save a setting value."""
        self.data[key] = value
        self.save()
