# Dev mode with HMR: Django(:9527) + Vite(:5173) + Electron
# Usage: .\dev.ps1

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir  = Join-Path $root "backend"
$frontendDir = Join-Path $root "frontend"

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Dev Mode: Django + Vite HMR + Electron" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan

# --- Install Electron deps ---
if (-not (Test-Path (Join-Path $root "node_modules"))) {
    Write-Host "`nInstalling root dependencies..." -ForegroundColor Gray
    Set-Location $root; npm install
}

# --- Install frontend deps ---
if (-not (Test-Path (Join-Path $frontendDir "node_modules"))) {
    Write-Host "`nInstalling frontend dependencies..." -ForegroundColor Gray
    Set-Location $frontendDir; npm install
}

# --- Start Django in a new window ---
Write-Host "`n[1/3] Starting Django (127.0.0.1:9527)..." -ForegroundColor Yellow
$djangoCmd = "cd '$backendDir'; " +
    "`$env:DJANGO_SETTINGS_MODULE='config.settings'; " +
    "`$env:APP_BUNDLE_DIR='$root'; " +
    "`$env:APP_DATA_DIR='$root'; " +
    "python manage.py migrate; python manage.py runserver 127.0.0.1:9527"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $djangoCmd -WindowStyle Normal

# --- Start Vite dev server in a new window ---
Write-Host "[2/3] Starting Vite dev server (localhost:5173)..." -ForegroundColor Yellow
$viteCmd = "cd '$frontendDir'; npm run dev"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $viteCmd -WindowStyle Normal

# --- Wait for both services ---
Write-Host "`nWaiting for Django..." -ForegroundColor Gray
$ready = $false
for ($i = 0; $i -lt 40; $i++) {
    Start-Sleep -Seconds 1
    try {
        $null = Invoke-WebRequest -Uri "http://127.0.0.1:9527/api/" -UseBasicParsing -TimeoutSec 1 -ErrorAction Stop
        $ready = $true; break
    } catch { if ($_.Exception.Response) { $ready = $true; break } }
}
if ($ready) { Write-Host "  Django ready." -ForegroundColor Green }
else { Write-Host "  [WARN] Django timeout. Check backend window." -ForegroundColor Yellow }

Write-Host "Waiting for Vite..." -ForegroundColor Gray
$ready = $false
for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Seconds 1
    try {
        $null = Invoke-WebRequest -Uri "http://localhost:5173" -UseBasicParsing -TimeoutSec 1 -ErrorAction Stop
        $ready = $true; break
    } catch { if ($_.Exception.Response) { $ready = $true; break } }
}
if ($ready) { Write-Host "  Vite ready." -ForegroundColor Green }
else { Write-Host "  [WARN] Vite timeout. Check frontend window." -ForegroundColor Yellow }

# --- Launch Electron ---
Write-Host "`n[3/3] Starting Electron (loading Vite HMR)..." -ForegroundColor Yellow
Set-Location $root
npx electron .
