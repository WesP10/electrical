@echo off
REM Batch launcher for the Cornell Hyperloop GUI with centralized Python cache
REM This script sets up a centralized __pycache__ directory and launches Python

setlocal EnableDelayedExpansion

REM Get the directory where this batch file is located (config) and go up to GUI root
set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%\..") do set "GUI_ROOT=%%~fI"
set "CACHE_DIR=%GUI_ROOT%\__pycache__"

REM Remove trailing backslash if present
if "%GUI_ROOT:~-1%"=="\" set "GUI_ROOT=%GUI_ROOT:~0,-1%"

REM Create cache directory if it doesn't exist
if not exist "%CACHE_DIR%" (
    mkdir "%CACHE_DIR%"
    echo Created centralized cache directory: %CACHE_DIR%
)

REM Set environment variables for centralized cache
set "PYTHONPYCACHEPREFIX=%CACHE_DIR%"
set "PYTHONDONTWRITEBYTECODE="

REM Display configuration
echo Cornell Hyperloop GUI Launcher
echo ================================
echo Cache Directory: %CACHE_DIR%
echo PYTHONPYCACHEPREFIX: %PYTHONPYCACHEPREFIX%
echo.

REM Change to GUI directory and launch Python
cd /d "%GUI_ROOT%"
python src\app.py %*

REM Preserve exit code
set "EXIT_CODE=%ERRORLEVEL%"
if %EXIT_CODE% EQU 0 (
    echo.
    echo Application completed successfully.
) else (
    echo.
    echo Application exited with code: %EXIT_CODE%
)

exit /b %EXIT_CODE%