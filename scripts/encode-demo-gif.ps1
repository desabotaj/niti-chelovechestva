# Re-encode a screen capture (MKV/MP4/…) to a GitHub-friendly GIF for README.
# Requires: pip install imageio-ffmpeg
# Usage (repo root):
#   .\scripts\encode-demo-gif.ps1 -InputPath "docs\2026-05-13 23-48-59.mkv"

param(
  [Parameter(Mandatory = $true)]
  [string] $InputPath,
  [string] $OutputPath = "docs\demo-preview.gif"
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $repoRoot

$inFull = (Resolve-Path $InputPath).Path
$outFull = Join-Path $repoRoot $OutputPath
$outDir = Split-Path $outFull -Parent
if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir | Out-Null }

$ff = python -c "import imageio_ffmpeg as i; print(i.get_ffmpeg_exe())"
if (-not $ff -or -not (Test-Path $ff)) { throw "Run: pip install imageio-ffmpeg" }

$vf = "fps=6,scale=480:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=96:stats_mode=diff[p];[s1][p]paletteuse=dither=bayer:bayer_scale=5"
& $ff -y -i $inFull -an -vf $vf $outFull

$len = (Get-Item $outFull).Length
Write-Host "OK: $outFull ($([math]::Round($len / 1MB, 2)) MB)"
