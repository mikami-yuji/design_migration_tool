@echo off
setlocal enabledelayedexpansion

echo ===================================================
echo   Design Order Data Folder Migration Tool
echo   Safe Single EXE Builder (No UPX, Clean Build)
echo ===================================================
echo.

rem Define paths
set BUILD_ENV=.venv_build
set APP_NAME=design_migration_tool
set DIST_DIR=dist
set BUILD_DIR=build

rem 1. Clean previous build artifacts
echo [1/6] Cleaning up old build directories...
if exist "%DIST_DIR%" rd /s /q "%DIST_DIR%"
if exist "%BUILD_DIR%" rd /s /q "%BUILD_DIR%"
if exist "%BUILD_ENV%" rd /s /q "%BUILD_ENV%"

rem 2. Create clean virtual environment
echo [2/6] Creating a clean temporary virtual environment...
py -m venv %BUILD_ENV%
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to create virtual environment using 'py'. Trying 'python'...
    python -m venv %BUILD_ENV%
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Both 'py' and 'python' failed to create a virtual environment.
        goto error
    )
)

rem 3. Activate build environment
echo [3/6] Activating virtual environment...
call %BUILD_ENV%\Scripts\activate.bat
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to activate virtual environment.
    goto error
)

rem 4. Install clean dependencies
echo [4/6] Installing minimum production dependencies...
python -m pip install --upgrade pip --no-warn-script-location
python -m pip install watchdog>=3.0.0 pystray>=0.19.0 Pillow>=10.0.0 pyinstaller --no-warn-script-location
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to install dependencies in venv.
    goto error
)

rem 5. Run PyInstaller build
echo [5/6] Building clean executable (This may take a minute)...
pyinstaller --clean --onefile --windowed --noupx --name "%APP_NAME%" main.py
if %ERRORLEVEL% neq 0 (
    echo [ERROR] PyInstaller build failed.
    goto error
)

rem 6. Cleanup temporary virtual environment
echo [6/6] Cleaning up build virtual environment...
call deactivate
rd /s /q "%BUILD_ENV%"

echo.
echo ===================================================
echo   Build completed successfully!
echo ===================================================
echo   Executable path:
echo   [EXE] dist\%APP_NAME%.exe
echo.
echo   You can now distribute this EXE file to other users.
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
