# Twality GeoStamp

Twality GeoStamp is a Windows desktop application for stamping GPS information onto photos while preserving original JPEG metadata through ExifTool.

## Features

- Recursive folder processing for JPEG, JPG, PNG, HEIC, and HEIF images.
- GPS EXIF parsing with correct north/south and east/west handling.
- Reverse geocoding through OpenStreetMap Nominatim with a local JSON cache.
- Static OpenStreetMap panel with a location marker and north indicator.
- Professional overlay themes with custom JSON theme support.
- Multi-threaded batch processing with progress, pause, resume, cancel, ETA, and per-file results.
- Metadata preservation for JPEG files using `exiftool -TagsFromFile original -all:all output`.
- Local settings, rotating logs, PyInstaller spec, and Inno Setup installer script.

## Installation Guide

Install Python 3.12 or newer, ExifTool, and the Python dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

ExifTool must be available on `PATH` as `exiftool.exe`. The application can stamp PNG and HEIC files, but full metadata preservation is guaranteed only for JPEG outputs.

## User Guide

Run the app:

```powershell
python main.py
```

Choose an input folder and output folder, select a theme and overlay position, then press Start. The original files are never modified. Output files are named like `IMG0001_GeoStamped.JPG`; if a file already exists, a numbered suffix is added.

Reverse geocoding and map tile downloads use the internet. If either service is unavailable, the app continues with coordinates and a fallback map panel.

## Developer Guide

The project uses a small MVC-style split:

- `ui/` contains PySide6 windows, dialogs, and Qt worker wiring.
- `core/` contains metadata, GPS, geocoding, maps, rendering, settings, and batch orchestration.
- `assets/themes/` contains bundled and custom overlay themes.
- `installer/` contains packaging files.

Core services are injectable, so future plugins can add data providers such as weather, GPX tracks, elevation charts, QR codes, or branding without changing the UI contract.

## Architecture Diagram

```text
MainWindow
  -> BatchWorker / QThread
    -> BatchProcessor
      -> ExifReader
      -> ReverseGeocoder
      -> StaticMapRenderer
      -> OverlayRenderer
      -> ExifWriter
```

## Class Diagram

```text
SettingsStore
ThemeManager -> Theme
ExifReader -> PhotoMetadata -> GPSCoordinate
BatchProcessor -> ProcessingResult
OverlayRenderer -> OverlayOptions
BatchWorker -> BatchProcessor
MainWindow -> BatchWorker
```

## Packaging Instructions

Build with PyInstaller from the project folder:

```powershell
pyinstaller installer\TwalityGeoStamp.spec
```

Then build the Windows installer with Inno Setup:

```powershell
iscc installer\TwalityGeoStamp.iss
```

The spec references `assets/icons/app.ico`. Convert `assets/icons/app.svg` to ICO before final commercial packaging, or replace the icon path with an existing `.ico` file.

## Troubleshooting

- `ExifTool is required`: install ExifTool and confirm `exiftool -ver` works.
- No GPS metadata: the source photo does not contain GPS EXIF tags.
- Network timeout: the app will continue with coordinates and cached or fallback map data.
- Permission denied: choose an output folder where your Windows user can write.
- HEIC unsupported: install `pillow-heif` and confirm the file is readable by Pillow.
