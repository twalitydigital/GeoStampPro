param(
    [ValidateSet("x64", "arm64", "x86")]
    [string]$TargetArch = "x64",

    [switch]$SkipInstaller,

    [switch]$RegenerateStoreAssets
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

try {
    $runtimeArch = [System.Runtime.InteropServices.RuntimeInformation]::ProcessArchitecture
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
    .\.venv\Scripts\python.exe tools\generate_store_assets.py
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

.\.venv\Scripts\pyinstaller.exe -y installer\TwalityGMark.spec

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
