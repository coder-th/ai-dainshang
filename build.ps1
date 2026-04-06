# Full build script: Vue + Django(PyInstaller) + Electron installer
# Usage: .\build.ps1

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path

function Step($n, $total, $msg) {
    Write-Host "`n[$n/$total] $msg" -ForegroundColor Cyan
}

function Assert-Ok($label) {
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] $label failed (exit code $LASTEXITCODE)" -ForegroundColor Red
        exit 1
    }
}

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Full Build: Vue + Django + Electron Installer" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan

# --- Step 1: Build Vue3 frontend ---
Step 1 5 "Building Vue3 frontend..."
Set-Location (Join-Path $root "frontend")

if (-not (Test-Path "node_modules")) {
    Write-Host "  Installing npm dependencies..." -ForegroundColor Gray
    npm install
    Assert-Ok "npm install (frontend)"
}

npm run build
Assert-Ok "npm run build"
Write-Host "  [OK] Frontend built -> frontend/dist/" -ForegroundColor Green
Set-Location $root

# --- Step 2: Install Python dependencies ---
Step 2 5 "Installing Python dependencies..."
pip install -r requirements.txt -q
Assert-Ok "pip install"
Write-Host "  [OK] Python dependencies ready." -ForegroundColor Green

# --- Step 3: Bundle Django with PyInstaller ---
Step 3 5 "Bundling Django backend with PyInstaller..."
$env:DJANGO_SETTINGS_MODULE = "config.settings"
$env:APP_BUNDLE_DIR = $root
$env:APP_DATA_DIR = $root

# Collect static files first
Set-Location (Join-Path $root "backend")
python manage.py collectstatic --noinput -v 0
if ($LASTEXITCODE -ne 0) {
    Write-Host "  [WARN] collectstatic failed, continuing..." -ForegroundColor Yellow
}
Set-Location $root

pyinstaller build.spec --clean --noconfirm
Assert-Ok "pyinstaller"
Write-Host "  [OK] Django bundled -> dist/app/app.exe" -ForegroundColor Green

# --- Step 4: Install Electron dependencies ---
Step 4 5 "Installing Electron dependencies..."
if (-not (Test-Path "node_modules")) {
    npm install
    Assert-Ok "npm install (electron)"
} else {
    Write-Host "  node_modules already exists, skipping." -ForegroundColor Gray
}
Write-Host "  [OK] Electron dependencies ready." -ForegroundColor Green

# --- Step 5: Build Electron installer ---
Step 5 5 "Building Electron installer (Windows NSIS)..."
npm run build:win
Assert-Ok "electron-builder"

Write-Host "`n================================================" -ForegroundColor Green
Write-Host "  Build complete!" -ForegroundColor Green
Write-Host "  Installer: dist-electron\AI-1.0.0-Setup.exe" -ForegroundColor Green
Write-Host "================================================`n" -ForegroundColor Green
