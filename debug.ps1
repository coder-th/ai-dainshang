# 前后端调试模式：Django(:8000) + Vite(:5173)，在浏览器中打开，无 Electron
# 用法：.\debug.ps1
# Django 日志直接输出到当前终端，Vite 在独立窗口运行

$root        = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir  = Join-Path $root "backend"
$frontendDir = Join-Path $root "frontend"

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Debug Mode: Django + Vite (Browser)" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# ── 安装依赖（仅首次）────────────────────────────────────────────────────────
if (-not (Test-Path (Join-Path $frontendDir "node_modules"))) {
    Write-Host "Installing frontend dependencies..." -ForegroundColor Gray
    Push-Location $frontendDir; npm install; Pop-Location
}

# ── 启动 Vite（独立窗口）────────────────────────────────────────────────────
Write-Host "[1/2] Starting Vite dev server (localhost:5173)..." -ForegroundColor Yellow
$viteCmd = "cd '$frontendDir'; npm run dev"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $viteCmd -WindowStyle Normal

# ── 等待 Vite 就绪后打开浏览器 ─────────────────────────────────────────────
$job = Start-Job -ScriptBlock {
    param($url)
    for ($i = 0; $i -lt 30; $i++) {
        Start-Sleep -Seconds 1
        try {
            $null = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 1 -ErrorAction Stop
            Start-Process $url
            break
        } catch { }
    }
} -ArgumentList "http://localhost:5173"

# ── 启动 Django（当前终端，日志实时可见）────────────────────────────────────
Write-Host "[2/2] Starting Django (127.0.0.1:8000)  — Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""
Write-Host "  Log file : $root\logs\api-calls\$(Get-Date -Format 'yyyy-MM-dd').jsonl" -ForegroundColor DarkCyan
Write-Host "  outbound : $root\logs\outbound.log" -ForegroundColor DarkCyan
Write-Host ""

$env:DJANGO_SETTINGS_MODULE = "config.settings"
$env:APP_BUNDLE_DIR          = $root
$env:APP_DATA_DIR            = $root

Push-Location $backendDir
# python manage.py migrate --run-syncdb 2>&1 | Out-Null
# python manage.py runserver 127.0.0.1:8000
Pop-Location
