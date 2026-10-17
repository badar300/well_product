# Build WellProduct.exe (one-folder) on Windows and create client ZIP.
# From repo root in PowerShell:
#   powershell -ExecutionPolicy Bypass -File .\packaging\build_windows.ps1
#
# Or double-click: packaging\build_windows.cmd

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

function Find-Python {
    if (Get-Command python -ErrorAction SilentlyContinue) {
        return (Get-Command python).Source
    }
    if (Get-Command py -ErrorAction SilentlyContinue) {
        return "py -3.12"
    }
    throw "Python 3.12+ not found. Install from https://www.python.org/downloads/ and check 'Add python.exe to PATH'."
}

$PythonCmd = Find-Python
$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"

if (-not (Test-Path $VenvPython)) {
    Write-Host "Creating virtual environment in .venv ..."
    if ($PythonCmd -eq "py -3.12") {
        & py -3.12 -m venv (Join-Path $Root ".venv")
    } else {
        & $PythonCmd -m venv (Join-Path $Root ".venv")
    }
}

if (-not (Test-Path $VenvPython)) {
    throw "Virtual env missing at $VenvPython — delete .venv folder and run this script again."
}

Write-Host "Using: $VenvPython"

& $VenvPython -m pip install --upgrade pip
& $VenvPython -m pip install -e .
& $VenvPython -m pip install pyinstaller

& $VenvPython -m PyInstaller --noconfirm packaging/well_product.spec

$DistFolder = Join-Path $Root "dist\WellProduct"
$ReleaseDir = Join-Path $Root "release"
$ZipPath = Join-Path $ReleaseDir "WellProduct-Windows.zip"

if (-not (Test-Path $DistFolder)) {
    throw "Expected build output at $DistFolder"
}

Copy-Item -Force (Join-Path $Root "packaging\CLIENT_SETUP.txt") (Join-Path $DistFolder "CLIENT_SETUP.txt")

New-Item -ItemType Directory -Force -Path $ReleaseDir | Out-Null
if (Test-Path $ZipPath) {
    Remove-Item -Force $ZipPath
}
Compress-Archive -Path $DistFolder -DestinationPath $ZipPath -CompressionLevel Optimal

Write-Host ""
Write-Host "App folder:  $DistFolder\WellProduct.exe"
Write-Host "Share this:  $ZipPath"
Write-Host "Client data: Desktop\WellProduct\  (backup that folder)"
Write-Host ""
