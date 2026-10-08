@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\run-windows.ps1"
if errorlevel 1 (
  echo.
  echo Ocorreu um erro. Leia a mensagem acima e consulte:
  echo docs\TUTORIAL-INSTALACAO-WINDOWS.md
  echo.
  pause
)
endlocal
