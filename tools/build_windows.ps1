$ErrorActionPreference = "Stop"

python -m pip install -r requirements.txt
python -m pip install pyinstaller

if (-not (Test-Path "runtime\ffmpeg.exe")) {
    Write-Warning "runtime\ffmpeg.exe was not found. Place an LGPL-compatible FFmpeg build in runtime before release."
}
if (-not (Test-Path "runtime\ffprobe.exe")) {
    Write-Warning "runtime\ffprobe.exe was not found. Place the matching ffprobe binary in runtime before release."
}

Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue
pyinstaller --clean findcut_windows.spec

if (Test-Path "runtime") {
    Copy-Item runtime dist\FindCut\runtime -Recurse -Force
}
Copy-Item THIRD_PARTY_LICENSES dist\FindCut\THIRD_PARTY_LICENSES -Recurse -Force
Copy-Item README.md, USER_GUIDE.md, LICENSE dist\FindCut -Force
Write-Host "FindCut package staged at dist\FindCut"
