# Generate a proper multi-resolution .ico file for Electron Builder
# Usage: .\scripts\create-icon.ps1

Add-Type -AssemblyName System.Drawing

$outDir  = Join-Path (Split-Path -Parent $PSScriptRoot) "electron\assets"
$icoPath = Join-Path $outDir "icon.ico"

if (-not (Test-Path $outDir)) {
    New-Item -ItemType Directory -Path $outDir | Out-Null
}

# ICO must contain these sizes for Windows to display correctly at all scales
$sizes = @(16, 24, 32, 48, 64, 128, 256)

function New-IconBitmap($size) {
    $bmp = New-Object System.Drawing.Bitmap($size, $size)
    $g   = [System.Drawing.Graphics]::FromImage($bmp)
    $g.SmoothingMode   = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $g.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit

    # Background: dark blue rounded rect
    $bg = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(0, 21, 41))
    $g.FillRectangle($bg, 0, 0, $size, $size)

    # Letter "A" centered
    $fontSize = [int]($size * 0.6)
    if ($fontSize -lt 6) { $fontSize = 6 }
    $font  = New-Object System.Drawing.Font("Arial", $fontSize, [System.Drawing.FontStyle]::Bold)
    $brush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(22, 119, 255))
    $sf    = New-Object System.Drawing.StringFormat
    $sf.Alignment     = [System.Drawing.StringAlignment]::Center
    $sf.LineAlignment = [System.Drawing.StringAlignment]::Center
    $rect  = New-Object System.Drawing.RectangleF(0, 0, $size, $size)
    $g.DrawString("A", $font, $brush, $rect, $sf)

    $g.Dispose()
    $bg.Dispose()
    $brush.Dispose()
    $font.Dispose()
    return $bmp
}

# Build ICO: header + directory + all PNG-compressed image data
$fs = [System.IO.File]::Open($icoPath, [System.IO.FileMode]::Create)
$bw = New-Object System.IO.BinaryWriter($fs)

$count = $sizes.Count

# ICO header (6 bytes)
$bw.Write([uint16]0)           # Reserved
$bw.Write([uint16]1)           # Type: 1 = ICO
$bw.Write([uint16]$count)      # Number of images

# Collect PNG bytes for each size
$images = @()
foreach ($size in $sizes) {
    $bmp = New-IconBitmap $size
    $ms  = New-Object System.IO.MemoryStream
    $bmp.Save($ms, [System.Drawing.Imaging.ImageFormat]::Png)
    $bmp.Dispose()
    $images += , $ms.ToArray()
    $ms.Dispose()
}

# Directory entries (16 bytes each), offset = 6 + 16*count
$offset = 6 + 16 * $count
foreach ($i in 0..($count - 1)) {
    $size = $sizes[$i]
    $w    = if ($size -eq 256) { 0 } else { [byte]$size }
    $h    = if ($size -eq 256) { 0 } else { [byte]$size }
    $bw.Write([byte]$w)
    $bw.Write([byte]$h)
    $bw.Write([byte]0)             # Color count
    $bw.Write([byte]0)             # Reserved
    $bw.Write([uint16]1)           # Planes
    $bw.Write([uint16]32)          # Bit count
    $bw.Write([uint32]$images[$i].Length)
    $bw.Write([uint32]$offset)
    $offset += $images[$i].Length
}

# Image data
foreach ($data in $images) {
    $bw.Write($data)
}

$bw.Close()
$fs.Close()

Write-Host "Icon created: $icoPath ($count sizes: $($sizes -join ', ')px)" -ForegroundColor Green
