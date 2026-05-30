@echo off
setlocal
cd /d "%~dp0"

net session >nul 2>&1
if not "%errorlevel%"=="0" (
    echo Requesting administrator permission...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath 'cmd.exe' -ArgumentList '/k', '\"%~f0\"' -Verb RunAs"
    exit /b
)

if not exist "%~dp0logs" mkdir "%~dp0logs"
set "LOG=%~dp0logs\interception_uninstall.log"
set "INSTALLER=%~dp0driver\interception\install-interception.exe"
if not exist "%INSTALLER%" (
    echo Missing Interception installer:
    echo %INSTALLER%
    echo.
    echo Please download the latest MaaLK package again.
    pause
    exit /b 1
)

echo MaaLK Interception driver uninstall > "%LOG%"
echo Time: %date% %time% >> "%LOG%"
echo Installer: %INSTALLER% >> "%LOG%"
echo. >> "%LOG%"

echo Uninstalling Interception driver...
echo Log: %LOG%
echo.
"%INSTALLER%" /uninstall >> "%LOG%" 2>&1
set "ERR=%errorlevel%"
echo Exit code: %ERR% >> "%LOG%"
echo.

if "%ERR%"=="0" (
    echo Interception uninstall command completed.
    echo Please reboot your computer to finish removing the driver.
    echo Interception uninstall command completed. >> "%LOG%"
    echo Please reboot your computer to finish removing the driver. >> "%LOG%"
) else (
    echo Interception uninstaller exited with code %ERR%.
    echo Try running this file again as administrator.
    echo Interception uninstaller exited with code %ERR%. >> "%LOG%"
)

echo.
echo Press any key to close this window.
pause
exit /b %ERR%
