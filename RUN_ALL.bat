@echo off
setlocal enabledelayedexpansion

:: ==============================================================================
:: SOUTHERN KEBBI PhD REMOTE SENSING & GIS CARTOGRAPHIC PRODUCTION ENGINE
:: Automated One-Click Runner for Windows Systems
:: Doctoral Advisory Committee / Guide Execution Script
:: ==============================================================================

title Southern Kebbi Remote Sensing Pipeline Runner
cd /d "%~dp0"

echo ==============================================================================
echo    SOUTHERN KEBBI PhD REMOTE SENSING RESEARCH PIPELINE (2000-2026)
echo              Automated One-Click Production and Evaluation Engine
echo ==============================================================================
echo.
echo Current Directory: %cd%

:: Check Python availability
where python >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set PY_CMD=python
    goto :PYTHON_FOUND
)

where py >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set PY_CMD=py
    goto :PYTHON_FOUND
)

echo.
echo [ERROR] Python was not found in your system PATH!
echo Please install Python 3.9+ or ensure it is added to your environment PATH.
echo.
pause
exit /b 1

:PYTHON_FOUND
echo Python Executable: %PY_CMD%
echo.

:: Check if requirements need installing
if exist "requirements.txt" (
    echo Checking core Python libraries...
    %PY_CMD% -c "import rasterio, geopandas, matplotlib, seaborn, docx, openpyxl, sklearn" >nul 2>&1
    if !ERRORLEVEL! neq 0 (
        echo [NOTICE] Installing missing Python dependencies from requirements.txt...
        %PY_CMD% -m pip install -r requirements.txt
    )
)

echo.
echo ==============================================================================
echo Starting Master Scientific Processing Pipeline...
echo ==============================================================================
echo.

%PY_CMD% main.py %*

echo.
echo ==============================================================================
echo Execution Finished.
echo You can inspect the generated outputs in:
echo   - Interactive HTML: view_results.html (Double-click to view all maps & plots)
echo   - Maps:             outputs\maps\
echo   - Plots:            outputs\plots\
echo   - Animated GIFs:    outputs\gifs\
echo   - Tables:           outputs\tables\
echo   - Report:           outputs\reports\
echo ==============================================================================
echo.
pause

