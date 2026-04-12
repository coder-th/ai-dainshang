# Publish script: detect version change and release to GitHub
# Usage: .\publish.ps1
# Requires: .env.local with github_token=xxx

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path

# --- Read current version from package.json ---
$pkgJson = Get-Content (Join-Path $root "package.json") -Raw | ConvertFrom-Json
$currentVersion = $pkgJson.version
$versionTag = "v$currentVersion"

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Publish: AI-Dianshang $versionTag" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan

# --- Check if tag already exists (check remote to avoid local cache issues) ---
$remoteTag = git ls-remote --tags origin "refs/tags/$versionTag" 2>$null
if (-not [string]::IsNullOrEmpty($remoteTag)) {
    Write-Host "`n[Skip] Version $currentVersion already released ($versionTag exists on remote), nothing to publish." -ForegroundColor Gray
    exit 0
}

Write-Host "`n[Version] New version detected: $currentVersion (tag $versionTag not found)" -ForegroundColor Yellow

# --- Load github_token from .env.local ---
$envFile = Join-Path $root ".env.local"
if (-not (Test-Path $envFile)) {
    Write-Host "[ERROR] .env.local not found." -ForegroundColor Red
    exit 1
}
$envLine = Get-Content $envFile | Where-Object { $_ -match "^github_token\s*=" }
if (-not $envLine) {
    Write-Host "[ERROR] github_token not found in .env.local." -ForegroundColor Red
    exit 1
}
$ghToken = ($envLine -split "=", 2)[1].Trim()
$env:GH_TOKEN = $ghToken
Write-Host "[OK] GitHub token loaded." -ForegroundColor Green

# --- Full rebuild before publish ---
Write-Host "`n[Build] Running full build before publish..." -ForegroundColor Cyan
& (Join-Path $root "build.ps1") -KeepBackendExe
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] build.ps1 failed, aborting publish." -ForegroundColor Red
    exit 1
}
Write-Host "  [OK] Build complete." -ForegroundColor Green

# --- Publish to GitHub ---
Write-Host "`n[Publish] Running electron-builder with --publish always..." -ForegroundColor Cyan
npx electron-builder --win --x64 --publish always
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] electron-builder publish failed (exit code $LASTEXITCODE)" -ForegroundColor Red
    exit 1
}

# --- Create and push git tag ---
Write-Host "`n[Tag] Creating git tag $versionTag..." -ForegroundColor Cyan
git tag $versionTag
if ($LASTEXITCODE -ne 0) {
    Write-Host "[WARN] Failed to create tag $versionTag, skipping push." -ForegroundColor Yellow
} else {
    git push origin $versionTag
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[WARN] Failed to push tag $versionTag to origin." -ForegroundColor Yellow
    } else {
        Write-Host "  [OK] Tag $versionTag pushed to origin." -ForegroundColor Green
    }
}

Write-Host "`n================================================" -ForegroundColor Green
Write-Host "  Published: $versionTag -> GitHub Release" -ForegroundColor Green
Write-Host "================================================`n" -ForegroundColor Green
