@echo off
setlocal
powershell -ExecutionPolicy Bypass -File "%~dp0build_windows.ps1"
if errorlevel 1 (
  echo FindCut Windows build failed.
  exit /b 1
)
echo FindCut Windows build completed. See dist\FindCut.
