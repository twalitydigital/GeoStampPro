"""Generate Microsoft Store/MSIX logo assets from Logo.png."""

from __future__ import annotations

from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "Logo.png"
OUT_DIR = ROOT / "assets" / "store"

ASSETS = {
    "Square44x44Logo": (44, 44),
    "Square150x150Logo": (150, 150),
    "Square310x310Logo": (310, 310),
    "StoreLogo": (50, 50),
    "Wide310x150Logo": (310, 150),
    "SplashScreen": (620, 300),
}

SCALES = {
    "scale-100": 1.00,
    "scale-125": 1.25,
    "scale-150": 1.50,
    "scale-200": 2.00,
    "scale-400": 4.00,
}


def resize_contained(source: Image.Image, size: tuple[int, int]) -> Image.Image:
    """Resize source proportionally on a transparent canvas."""
    canvas = Image.new("RGBA", size, (0, 0, 0, 0))
    working = source.copy()
    working.thumbnail(size, Image.Resampling.LANCZOS)
    x = (size[0] - working.width) // 2
    y = (size[1] - working.height) // 2
    canvas.alpha_composite(working, (x, y))
    return canvas


def main() -> int:
    if not SOURCE.exists():
        raise FileNotFoundError(f"Store asset source image not found: {SOURCE}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    source = Image.open(SOURCE).convert("RGBA")

    for asset_name, base_size in ASSETS.items():
        for scale_name, scale in SCALES.items():
            scaled_size = (int(base_size[0] * scale + 0.5), int(base_size[1] * scale + 0.5))
            output = OUT_DIR / f"{asset_name}.{scale_name}.png"
            resize_contained(source, scaled_size).save(output)

    # Unscaled aliases are convenient in AppxManifest.xml templates and tools.
    for asset_name, base_size in ASSETS.items():
        output = OUT_DIR / f"{asset_name}.png"
        resize_contained(source, base_size).save(output)

    print(f"Generated MSIX store assets in {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
