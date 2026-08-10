# Twality GeoStamp Pro

Twality GeoStamp Pro is a free Windows desktop application by Twality Digital Solutions LLP for creating stamped copies of photos with Geo, EXIF, and watermark information.

Original source images are not intentionally modified. Stamped copies are written to the selected output folder.

## Features

- Geo Stamping with GPS coordinates, altitude, capture timestamp, address, and map.
- Optional stamping of all additional readable EXIF data.
- Configurable text or image watermark with 3x3 placement, opacity, size, and inset.
- Preview First Image renders the selected stamping options before batch processing.
- Recursive folder processing for JPEG, JPG, PNG, HEIC, and HEIF images.
- Multi-threaded batch processing with progress, pause, resume, cancel, ETA, and per-file results.
- JPEG metadata preservation through ExifTool.
- Help menu with user help and About information.
- Packaged builds store runtime settings, logs, and caches under the user's LocalAppData folder.
- PyInstaller and Inno Setup packaging files.

## Requirements

- Windows 10 or Windows 11.
- Python 3.10+ for development builds.
- ExifTool available on PATH as `exiftool.exe` for full JPEG metadata restoration.
- Python packages from `requirements.txt`.

## Developer Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -r requirements-build.txt
```

Run the app:

```powershell
python main.py
```

## Packaging

Build the PyInstaller app from `windows-app`:

```powershell
pyinstaller installer\TwalityGeoStamp.spec
```

Build the Inno Setup installer:

```powershell
iscc installer\TwalityGeoStamp.iss
```

Expected installer:

```text
installer\TwalityGeoStampProSetup.exe
```

For Microsoft Store publication, see [STORE_PUBLISHING_GUIDE.md](STORE_PUBLISHING_GUIDE.md).

## Documentation

- [LICENSE.txt](LICENSE.txt)
- [PRIVACY.md](PRIVACY.md)
- [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)
- [STORE_LISTING_DRAFT.md](STORE_LISTING_DRAFT.md)
- [STORE_PUBLISHING_GUIDE.md](STORE_PUBLISHING_GUIDE.md)

## Troubleshooting

- `ExifTool is required`: install ExifTool and confirm `exiftool -ver` works.
- No GPS metadata: the source photo does not contain GPS EXIF tags.
- Network timeout: address lookup may fail; Geo Stamping can still use available coordinates.
- Permission denied: choose an output folder where your Windows user can write.
- HEIC unsupported: install `pillow-heif` and confirm the file is readable by Pillow.
