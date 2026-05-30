@echo off
setlocal
cd /d "%~dp0"

if not exist "%~dp0logs" mkdir "%~dp0logs"
set "LOG=%~dp0logs\interception_check.log"
set "PYTHON=%~dp0python\python.exe"

echo MaaLK Interception driver check > "%LOG%"
echo Time: %date% %time% >> "%LOG%"
echo. >> "%LOG%"

if not exist "%PYTHON%" (
    echo Missing bundled Python:
    echo %PYTHON%
    echo Missing bundled Python: %PYTHON% >> "%LOG%"
    echo.
    pause
    exit /b 1
)

echo Checking Interception driver...
echo Log: %LOG%
echo.

"%PYTHON%" -c "import sys; sys.path.insert(0, r'.\agent'); from custom.interception_controller import get_controller; c=get_controller(); c.initialize(); c.shutdown(); print('Interception driver is available.')" >> "%LOG%" 2>&1
set "ERR=%errorlevel%"

if "%ERR%"=="0" (
    type "%LOG%"
    echo.
    echo Check passed. Interception driver is available.
    echo If input still does not work in game, run MFAAvalonia.exe as administrator.
) else (
    type "%LOG%"
    echo.
    echo Check failed. Interception driver is not available yet.
    echo Please run Install_Interception_Driver.bat as administrator, reboot, then run this check again.
)

echo.
echo Press any key to close this window.
pause
exit /b %ERR%
