@echo off
setlocal enabledelayedexpansion

:: Set paths
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."
set "CSV_PATH=%PROJECT_ROOT%\data\philosophers.csv"
set "PYTHON_SCRIPT=%SCRIPT_DIR%\import_philosophers.py"

:: Check if Python is installed
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Python is not in your PATH. Please install Python and ensure it's in your PATH.
    exit /b 1
)

:: Check if psycopg2 is installed
python -c "import psycopg2" 2>nul
if %ERRORLEVEL% neq 0 (
    echo Installing psycopg2-binary...
    pip install psycopg2-binary
    if %ERRORLEVEL% neq 0 (
        echo Failed to install psycopg2-binary. Please install it manually.
        exit /b 1
    )
)

:: Run the import script
echo Starting philosopher data import...
python "%PYTHON_SCRIPT%" "%CSV_PATH%"

if %ERRORLEVEL% equ 0 (
    echo.
    echo Import completed successfully!
) else (
    echo.
    echo Import failed with error code %ERRORLEVEL%
    exit /b %ERRORLEVEL%
)
