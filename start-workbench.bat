@echo off
setlocal

powershell -ExecutionPolicy Bypass -NoProfile -File "%~dp0scripts\launch_workbench.ps1"
set EXIT_CODE=%ERRORLEVEL%

if not "%EXIT_CODE%"=="0" (
  echo.
  echo Workbench launch failed. Review the messages above.
  pause
)

exit /b %EXIT_CODE%
