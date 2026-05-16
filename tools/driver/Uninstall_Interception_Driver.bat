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

echo Uninstalling Interception driver...
echo.
"%INSTALLER%" /uninstall
set "ERR=%errorlevel%"
echo.

if "%ERR%"=="0" (
    echo Interception uninstall command completed.
    echo Please reboot your computer to finish removing the driver.
) else (
    echo Interception uninstaller exited with code %ERR%.
    echo Try running this file again as administrator.
)

echo.
pause
exit /b %ERR%
