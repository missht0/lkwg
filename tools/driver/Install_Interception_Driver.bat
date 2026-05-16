@echo off
setlocal
cd /d "%~dp0"

net session >nul 2>&1
if not "%errorlevel%"=="0" (
    echo Requesting administrator permission...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

set "INSTALLER=%~dp0driver\interception\install-interception.exe"
if not exist "%INSTALLER%" (
    echo Missing Interception installer:
    echo %INSTALLER%
    echo.
    echo Please download the latest MaaLK package again.
    pause
    exit /b 1
)

echo Installing Interception driver...
echo.
"%INSTALLER%" /install
set "ERR=%errorlevel%"
echo.

if "%ERR%"=="0" (
    echo Interception install command completed.
    echo Please reboot your computer before using MaaLK.
) else (
    echo Interception installer exited with code %ERR%.
    echo If this is the first install attempt, try running this file again as administrator.
)

echo.
pause
exit /b %ERR%
