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
set "LOG=%~dp0logs\interception_install.log"
set "INSTALLER=%~dp0driver\interception\install-interception.exe"
if not exist "%INSTALLER%" (
    echo Missing Interception installer:
    echo %INSTALLER%
    echo.
    echo Please download the latest MaaLK package again.
    pause
    exit /b 1
)

echo MaaLK Interception driver install > "%LOG%"
echo Time: %date% %time% >> "%LOG%"
echo Installer: %INSTALLER% >> "%LOG%"
echo. >> "%LOG%"

echo Installing Interception driver...
echo Log: %LOG%
echo.
"%INSTALLER%" /install >> "%LOG%" 2>&1
set "ERR=%errorlevel%"
echo Exit code: %ERR% >> "%LOG%"
echo.

if "%ERR%"=="0" (
    echo Interception install command completed.
    echo Please reboot your computer before using MaaLK.
    echo Interception install command completed. >> "%LOG%"
    echo Please reboot your computer before using MaaLK. >> "%LOG%"
) else (
    echo Interception installer exited with code %ERR%.
    echo If this is the first install attempt, try running this file again as administrator.
    echo Interception installer exited with code %ERR%. >> "%LOG%"
)

echo.
echo Press any key to close this window.
pause
exit /b %ERR%
