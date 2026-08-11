# Twality GMark Pro Setup and Testing Guide

## Development Setup

```powershell
cd D:\src\github\GeoStampPro\windows-app
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

ExifTool must be available globally on PATH as `exiftool.exe` for full JPEG metadata preservation.
Use Inno Setup 6.3 or newer when creating installers.

## Run Locally

```powershell
python main.py
```

## Smoke Test

1. Select an input folder with sample photos.
2. Confirm the output folder changes to `gmark_output`.
3. Select at least one stamping option.
4. Use File > Preview First Image.
5. Run a small batch.
6. Confirm output files are created without modifying originals.
7. Confirm JPEG metadata is restored when ExifTool is available.

## Build

```powershell
.\build-windows.ps1 -TargetArch x64 -SkipInstaller
```

Store/MSIX logo PNGs are committed under `assets\store` and copied into the build
output. Regenerate them from `Logo.png` only when the source logo changes:

```powershell
.\build-windows.ps1 -TargetArch x64 -SkipInstaller -RegenerateStoreAssets
```

## Installer

```powershell
iscc installer\TwalityGMark.iss
```

## Multi-Architecture Windows Builds

PyInstaller builds for the architecture of the active Python/runtime. Build each
Windows architecture from a matching environment:

```powershell
.\build-windows.ps1 -TargetArch x64
.\build-windows.ps1 -TargetArch arm64
.\build-windows.ps1 -TargetArch x86
```

The generated installers are named with their target architecture, for example
`installer\TwalityGMarkProSetup-x64.exe`.

See `STORE_PUBLISHING_GUIDE.md` for Microsoft Store release steps.
