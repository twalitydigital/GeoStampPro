param(
    [string]$Version = "13.59",

    [ValidateSet("x64", "x86")]
    [string]$TargetArch = "x64",

    [ValidateSet("64", "32")]
    [string]$Bitness = "64",

    [string]$SourcePath = ""
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$vendorRoot = Join-Path $root "vendor\exiftool\$TargetArch"
$tempRoot = Join-Path $root "vendor\.tmp"
$zipName = "exiftool-$Version`_$Bitness.zip"
$downloadUrl = "https://downloads.sourceforge.net/project/exiftool/$zipName"
$zipPath = Join-Path $tempRoot $zipName
$extractRoot = Join-Path $tempRoot "extract"
$expectedExtracted = Join-Path $extractRoot "exiftool-$Version`_$Bitness"

New-Item -ItemType Directory -Force -Path $vendorRoot | Out-Null
New-Item -ItemType Directory -Force -Path $tempRoot | Out-Null
if (Test-Path -LiteralPath $extractRoot) {
    Remove-Item -LiteralPath $extractRoot -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $extractRoot | Out-Null

if (-not [string]::IsNullOrWhiteSpace($SourcePath)) {
    $sourceRoot = Resolve-Path -LiteralPath $SourcePath
    $sourceExe = Join-Path $sourceRoot "exiftool.exe"
    if (-not (Test-Path -LiteralPath $sourceExe)) {
        $sourceExe = Join-Path $sourceRoot "exiftool(-k).exe"
    }
    $sourceFiles = Join-Path $sourceRoot "exiftool_files"
    $sourceDescription = "$sourceRoot"
} else {
    Write-Host "Downloading ExifTool $Version ($Bitness-bit) from $downloadUrl"
    Invoke-WebRequest -Uri $downloadUrl -OutFile $zipPath

    $signature = Get-Content -LiteralPath $zipPath -Encoding Byte -TotalCount 4
    if ($signature.Length -lt 4 -or $signature[0] -ne 0x50 -or $signature[1] -ne 0x4B) {
        Write-Warning "Downloaded file is not a ZIP archive. Falling back to an installed exiftool.exe on PATH."
        $installed = Get-Command exiftool.exe -ErrorAction SilentlyContinue
        if ($null -eq $installed) {
            throw "Downloaded file was not a ZIP archive and exiftool.exe was not found on PATH."
        }
        $sourceExe = $installed.Source
        $sourceFiles = Join-Path (Split-Path -Parent $sourceExe) "exiftool_files"
        $sourceDescription = $sourceExe
    } else {
        Expand-Archive -LiteralPath $zipPath -DestinationPath $extractRoot -Force

        if (-not (Test-Path -LiteralPath $expectedExtracted)) {
            throw "Expected extracted ExifTool folder was not found: $expectedExtracted"
        }

        $sourceExe = Join-Path $expectedExtracted "exiftool(-k).exe"
        $sourceFiles = Join-Path $expectedExtracted "exiftool_files"
        $sourceDescription = $downloadUrl
    }
}

if (-not (Test-Path -LiteralPath $sourceExe)) {
    throw "Expected ExifTool executable was not found: $sourceExe"
}
if (-not (Test-Path -LiteralPath $sourceFiles)) {
    throw "Expected ExifTool support folder was not found: $sourceFiles"
}

$bytes = [System.IO.File]::ReadAllBytes($sourceExe)
$peOffset = [BitConverter]::ToInt32($bytes, 0x3C)
$machine = [BitConverter]::ToUInt16($bytes, $peOffset + 4)
$expectedMachine = if ($Bitness -eq "32") { 0x14c } else { 0x8664 }
if ($machine -ne $expectedMachine) {
    throw ("ExifTool executable architecture mismatch. Expected {0}-bit PE machine 0x{1:x}, found 0x{2:x}: {3}" -f $Bitness, $expectedMachine, $machine, $sourceExe)
}

Copy-Item -LiteralPath $sourceExe -Destination (Join-Path $vendorRoot "exiftool.exe") -Force
if (Test-Path -LiteralPath (Join-Path $vendorRoot "exiftool_files")) {
    Remove-Item -LiteralPath (Join-Path $vendorRoot "exiftool_files") -Recurse -Force
}
Copy-Item -LiteralPath $sourceFiles -Destination $vendorRoot -Recurse -Force

@"
ExifTool $Version Windows $Bitness-bit executable
Source used for this vendor copy: $sourceDescription
Bundled for private use by Twality GMark Pro.

The Windows executable must remain beside the exiftool_files folder.
Official installation notes: https://exiftool.org/install.html
"@ | Set-Content -LiteralPath (Join-Path $vendorRoot "README-Twality.txt") -Encoding UTF8

& (Join-Path $vendorRoot "exiftool.exe") -ver
Write-Host "Bundled ExifTool installed in $vendorRoot"
