# Twality GMark Pro Setup and Testing Guide

## Development Setup

```powershell
cd D:\src\github\GeoStampPro\windows-app
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Use Inno Setup 6.3 or newer when creating installers.

ExifTool is bundled privately under architecture-specific folders in
`vendor\exiftool` for full JPEG metadata preservation. Refresh it only when
intentionally updating the pinned vendor copy:

```powershell
.\build-windows.ps1 -TargetArch x64 -SkipInstaller -FetchExifTool
.\build-windows.ps1 -TargetArch x86 -SkipInstaller -FetchExifTool
```

If the network download is unavailable, extract the official Windows ZIP manually and
import it with:

```powershell
.\tools\fetch_exiftool.ps1 -TargetArch x86 -Bitness 32 -SourcePath C:\Path\To\exiftool-13.59_32
```

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
7. Confirm JPEG metadata is restored using the bundled ExifTool.

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
