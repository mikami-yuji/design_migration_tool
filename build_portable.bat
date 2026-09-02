@echo off
setlocal enabledelayedexpansion

echo ===================================================
echo   Design Order Data Folder Migration Tool
echo   Safe Portable Distribution Package (ZIP) Builder
echo ===================================================
echo.

set BUILD_ENV=.venv_build_portable
set APP_NAME=design_migration_tool
set DIST_DIRECTORY=dist_portable
set ZIP_FILE_PATH=%DIST_DIRECTORY%\%APP_NAME%.zip

echo [1/6] Cleaning up old build directories...
if exist "%DIST_DIRECTORY%" rd /s /q "%DIST_DIRECTORY%"
if exist "build" rd /s /q "build"
if exist "dist" rd /s /q "dist"
if exist "%BUILD_ENV%" rd /s /q "%BUILD_ENV%"
mkdir "%DIST_DIRECTORY%"

echo [2/6] Creating a clean temporary virtual environment...
python -m venv %BUILD_ENV%
if %ERRORLEVEL% neq 0 (
    py -m venv %BUILD_ENV%
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        goto error
    )
)

echo [3/6] Activating virtual environment...
call %BUILD_ENV%\Scripts\activate.bat
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to activate virtual environment.
    goto error
)

echo [4/6] Installing dependencies...
python -m pip install --upgrade pip --no-warn-script-location
python -m pip install "watchdog>=3.0.0" "pystray>=0.19.0" "Pillow>=10.0.0" "pymupdf>=1.24.0" pyinstaller --no-warn-script-location
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to install dependencies in venv.
    goto error
)

echo [5/6] Building clean directory package...
pyinstaller --clean --onedir --windowed --noupx --name "%APP_NAME%" main.py
if %ERRORLEVEL% neq 0 (
    echo [ERROR] PyInstaller build failed.
    goto error
)

if exist "PC起動時の自動起動設定手順.txt" (
    copy "PC起動時の自動起動設定手順.txt" "dist\%APP_NAME%\" >nul
)
if exist "config.json.template" (
    copy "config.json.template" "dist\%APP_NAME%\config.json.template" >nul
)

echo [6/6] Creating distribution ZIP file...
powershell -Command "Compress-Archive -Path 'dist\%APP_NAME%' -DestinationPath '%ZIP_FILE_PATH%' -Force"

call deactivate 2>nul
if exist "%BUILD_ENV%" rd /s /q "%BUILD_ENV%"
if exist "build" rd /s /q "build"
if exist "dist" rd /s /q "dist"

echo.
echo ===================================================
echo   Build completed successfully!
echo ===================================================
echo   Package path:
echo   [ZIP] %ZIP_FILE_PATH%
echo.
echo   You can distribute this ZIP file to other users.
echo   Instruct them to extract the ZIP and run "design_migration_tool.exe".
echo ===================================================
goto end

:error
echo.
echo [ERROR] Build failed.
if exist "%BUILD_ENV%" (
    call deactivate 2>nul
    rd /s /q "%BUILD_ENV%" 2>nul
)
if not "%~1"=="--no-pause" pause
exit /b 1

:end
if not "%~1"=="--no-pause" pause
exit /b 0
