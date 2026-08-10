# Twality GeoStamp Pro Setup and Testing Guide

## Development Setup

```powershell
cd D:\src\github\GeoStampPro\windows-app
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

ExifTool must be available globally on PATH as `exiftool.exe` for full JPEG metadata preservation.

## Run Locally

```powershell
python main.py
```

## Smoke Test

1. Select an input folder with sample photos.
2. Confirm the output folder changes to `geostamp_output`.
3. Select at least one stamping option.
4. Use File > Preview First Image.
5. Run a small batch.
6. Confirm output files are created without modifying originals.
7. Confirm JPEG metadata is restored when ExifTool is available.

## Build

```powershell
pyinstaller installer\TwalityGeoStamp.spec
```

## Installer

```powershell
iscc installer\TwalityGeoStamp.iss
```

See `STORE_PUBLISHING_GUIDE.md` for Microsoft Store release steps.
