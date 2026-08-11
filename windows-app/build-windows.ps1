param(
    [ValidateSet("x64", "arm64", "x86")]
    [string]$TargetArch = "x64",

    [switch]$SkipInstaller,

    [switch]$RegenerateStoreAssets,

    [switch]$FetchExifTool
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$venvRoot = if (-not [string]::IsNullOrWhiteSpace($env:VIRTUAL_ENV)) {
    $env:VIRTUAL_ENV
} else {
    Join-Path $root ".venv"
}
$pythonExe = Join-Path $venvRoot "Scripts\python.exe"
$pyInstallerExe = Join-Path $venvRoot "Scripts\pyinstaller.exe"

if (-not (Test-Path -LiteralPath $pythonExe)) {
    throw "Python executable was not found: $pythonExe. Activate the intended venv or create .venv."
}
if (-not (Test-Path -LiteralPath $pyInstallerExe)) {
    throw "PyInstaller executable was not found: $pyInstallerExe. Install requirements-build.txt in the active venv."
}

try {
    $runtimeArch = & $pythonExe -c "import platform; print(platform.machine())"
} catch {
    $runtimeArch = $null
}

if ($null -ne $runtimeArch) {
    $processArch = "$runtimeArch"
} elseif (-not [string]::IsNullOrWhiteSpace($env:PROCESSOR_ARCHITECTURE)) {
    $processArch = $env:PROCESSOR_ARCHITECTURE
} elseif (-not [string]::IsNullOrWhiteSpace($env:PROCESSOR_ARCHITEW6432)) {
    $processArch = $env:PROCESSOR_ARCHITEW6432
} else {
    $processArch = "unknown"
}

$processArch = $processArch.ToLowerInvariant()

if ($processArch -eq "amd64") {
    $processArch = "x64"
} elseif ($processArch -eq "x86") {
    $processArch = "x86"
} elseif ($processArch -eq "x86_64") {
    $processArch = "x64"
} elseif ($processArch -eq "arm64") {
    $processArch = "arm64"
}
$archMap = @{
    "x64" = "x64"
    "arm64" = "arm64"
    "x86" = "x86"
}

if ($archMap[$TargetArch] -ne $processArch) {
    Write-Warning "PyInstaller builds architecture-specific binaries. TargetArch '$TargetArch' should be built with a $TargetArch Python/runtime. Current process architecture is '$processArch'."
}

if ($RegenerateStoreAssets) {
    & $pythonExe tools\generate_store_assets.py
}

if ($FetchExifTool) {
    if ($TargetArch -eq "x86") {
        .\tools\fetch_exiftool.ps1 -TargetArch x86 -Bitness 32
    } else {
        .\tools\fetch_exiftool.ps1 -TargetArch x64 -Bitness 64
    }
}

$storeAssets = Join-Path $root "assets\store"
if (-not (Test-Path -LiteralPath $storeAssets)) {
    throw "Store assets were not found: $storeAssets. Run .\build-windows.ps1 -RegenerateStoreAssets once, then commit assets\store."
}

$requiredStoreAssets = @(
    "StoreLogo.png",
    "Square44x44Logo.png",
    "Square150x150Logo.png",
    "Square310x310Logo.png",
    "Wide310x150Logo.png",
    "SplashScreen.png"
)
foreach ($asset in $requiredStoreAssets) {
    $assetPath = Join-Path $storeAssets $asset
    if (-not (Test-Path -LiteralPath $assetPath)) {
        throw "Required Store asset was not found: $assetPath. Run .\build-windows.ps1 -RegenerateStoreAssets once, then commit assets\store."
    }
}

$exifToolArch = if ($TargetArch -eq "x86") { "x86" } else { "x64" }
if ($TargetArch -eq "arm64") {
    Write-Warning "No native Windows Arm64 ExifTool package is configured. Staging the x64 ExifTool helper for this build; test on Windows on Arm before publishing."
}

$exifToolRoot = Join-Path $root "vendor\exiftool\$exifToolArch"
$exifToolExe = Join-Path $exifToolRoot "exiftool.exe"
$exifToolFiles = Join-Path $exifToolRoot "exiftool_files"
if (-not (Test-Path -LiteralPath $exifToolExe) -or -not (Test-Path -LiteralPath $exifToolFiles)) {
    throw "Bundled ExifTool for $exifToolArch was not found under $exifToolRoot. Run .\build-windows.ps1 -TargetArch $TargetArch -FetchExifTool once, then commit vendor\exiftool\$exifToolArch."
}

$stagedVendorRoot = Join-Path $root "build-vendor"
$stagedExifToolRoot = Join-Path $stagedVendorRoot "exiftool"
if (Test-Path -LiteralPath $stagedVendorRoot) {
    Remove-Item -LiteralPath $stagedVendorRoot -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $stagedExifToolRoot | Out-Null
Copy-Item -LiteralPath $exifToolExe -Destination (Join-Path $stagedExifToolRoot "exiftool.exe") -Force
Copy-Item -LiteralPath $exifToolFiles -Destination $stagedExifToolRoot -Recurse -Force
Copy-Item -Path (Join-Path $exifToolRoot "README*.txt") -Destination $stagedExifToolRoot -Force -ErrorAction SilentlyContinue

& $pyInstallerExe -y installer\TwalityGMark.spec

$distRoot = Join-Path $root "dist\TwalityGMark"
$distAssets = Join-Path $distRoot "Assets"
if (-not (Test-Path -LiteralPath $distRoot)) {
    throw "Expected PyInstaller output was not found: $distRoot"
}
New-Item -ItemType Directory -Force -Path $distAssets | Out-Null
Copy-Item -Path (Join-Path $storeAssets "*.png") -Destination $distAssets -Force
Copy-Item -LiteralPath (Join-Path $root "Logo.png") -Destination $distRoot -Force

if (-not $SkipInstaller) {
    $isccCommand = Get-Command iscc -ErrorAction SilentlyContinue
    if ($null -ne $isccCommand) {
        $isccPath = $isccCommand.Source
    } else {
        $candidatePaths = @(
            "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
            "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
        )
        $isccPath = $candidatePaths | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
    }

    if ([string]::IsNullOrWhiteSpace($isccPath)) {
        throw "Inno Setup compiler was not found. Install Inno Setup 6.3 or newer, or add ISCC.exe to PATH. Use -SkipInstaller to build only the PyInstaller app."
    }

    & $isccPath "/DTargetArch=$TargetArch" installer\TwalityGMark.iss
}
