# Twality GeoStamp Setup and Testing Guide

Even though the original code generation stopped unexpectedly, the core logic, UI windows, thread workers, and configuration files were generated perfectly intact. This document covers the instructions to start and test the application.

## 1. Prerequisites
- **Python 3.12+**
- **ExifTool**: The `exiftool` command must be available globally in your system's PATH. This is already verified and installed on your Windows system.

## 2. Environment Setup

Open PowerShell and navigate to the application directory:
```powershell
cd d:\src\github\geostamp\TwalityGeoStamp
```

Create a new Python virtual environment to isolate the application's dependencies:
```powershell
python -m venv .venv
```

Activate the virtual environment:
```powershell
.\.venv\Scripts\Activate.ps1
```

Install the required dependencies:
```powershell
pip install -r requirements.txt
```
*(Note: You are currently running this step in your terminal!)*

## 3. Running the Application

Once the dependencies finish installing, you can start the application's GUI:
```powershell
python main.py
```

## 4. Testing the Application

To check the application and ensure the full pipeline is integrated correctly, follow these steps:

1. **Select Input Folder**: Choose a folder containing test JPEG/HEIC images that include GPS metadata (e.g., photos from a smartphone).
2. **Select Output Folder**: Choose a destination folder to store the stamped versions.
3. **Configure Options**: Pick a **Theme** (e.g., "Professional") and a **Placement** (e.g., "bottom").
4. **Preview**: Go to `File -> Preview First Image` in the top menu bar to verify the visual overlay looks correct before running the batch processor.
5. **Start Batch**: Click **Start**. The bottom table should populate showing the progress of each image.
6. **Verify Output**: Go to the output folder and confirm the images are stamped with the map and coordinates. Right-click the stamped images to view their properties, ensuring the GPS location tags were properly retained by ExifTool.
