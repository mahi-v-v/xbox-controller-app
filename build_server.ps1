<#
.SYNOPSIS
Builds the XboxController Server executable using PyInstaller.

.DESCRIPTION
This script creates a virtual environment if one doesn't exist, installs the required Python packages, and runs PyInstaller to bundle the Flask server, the controller web app, the landing website, and the Android APK into a single stand-alone Windows executable.

.DEPENDENCIES
- Python 3.10+
- The `vgamepad` driver dependencies must be met (Windows only).
#>

$ErrorActionPreference = "Stop"

Write-Host ">>> Starting XboxController Server Build Process" -ForegroundColor Cyan

# 1. Create Virtual Environment if it doesn't exist
if (-not (Test-Path "venv")) {
    Write-Host ">>> Creating Python virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# 2. Activate Venv and Install Requirements
Write-Host ">>> Installing Python requirements..." -ForegroundColor Yellow
& .\venv\Scripts\python.exe -m pip install -r server\requirements.txt
& .\venv\Scripts\python.exe -m pip install pyinstaller

# 3. Build with PyInstaller
Write-Host ">>> Bundling application with PyInstaller..." -ForegroundColor Yellow
& .\venv\Scripts\python.exe -m PyInstaller --onefile --windowed --name "XboxController Server" `
    --add-data "webapp;webapp" `
    --add-data "website;website" `
    --add-data "apk;apk" `
    --add-data "drivers;drivers" `
    --collect-all vgamepad `
    --hidden-import engineio.async_drivers.threading `
    server\server_gui.py -y

if ($LASTEXITCODE -eq 0) {
    Write-Host ">>> Build Successful! Executable is located at dist\XboxController Server.exe" -ForegroundColor Green
}
else {
    Write-Host ">>> Build Failed with exit code $LASTEXITCODE" -ForegroundColor Red
}
