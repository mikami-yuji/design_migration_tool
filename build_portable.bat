@echo off
setlocal enabledelayedexpansion

echo ===================================================
echo   Design Order Data Folder Migration Tool
echo   Portable Distribution Package (ZIP) Builder
echo ===================================================
echo.

rem Define variables
set PYTHON_VERSION=3.10.11
set PYTHON_ZIP_NAME=python-%PYTHON_VERSION%-embed-amd64.zip
set DOWNLOAD_URL=https://www.python.org/ftp/python/%PYTHON_VERSION%/%PYTHON_ZIP_NAME%
set DIST_DIRECTORY=dist_portable
set APP_DIRECTORY_NAME=design_migration_tool
set TARGET_APP_PATH=%DIST_DIRECTORY%\%APP_DIRECTORY_NAME%
set ZIP_FILE_PATH=%DIST_DIRECTORY%\%APP_DIRECTORY_NAME%.zip

rem Clean old build directories if they exist
if exist "%DIST_DIRECTORY%" (
    echo [1/7] Cleaning old build directory...
    rd /s /q "%DIST_DIRECTORY%"
)
mkdir "%TARGET_APP_PATH%"

rem 1. Download portable Python
echo [2/7] Downloading Python %PYTHON_VERSION% embeddable...
powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%DOWNLOAD_URL%' -OutFile '%PYTHON_ZIP_NAME%'"
if not exist "%PYTHON_ZIP_NAME%" (
    echo [ERROR] Failed to download Python. Please check your internet connection.
    goto error
)

rem 2. Extract Python to python_env
echo [3/7] Extracting Python package...
powershell -Command "Expand-Archive -Path '%PYTHON_ZIP_NAME%' -DestinationPath '%TARGET_APP_PATH%\python_env'"
del "%PYTHON_ZIP_NAME%"

rem 3. Enable site-packages in embeddable Python
echo [4/7] Adjusting Python configuration...
set PTH_FILE_PATH=
for %%f in ("%TARGET_APP_PATH%\python_env\python*._pth") do set PTH_FILE_PATH=%%f
if exist "!PTH_FILE_PATH!" (
    powershell -Command "(Get-Content '!PTH_FILE_PATH!') -replace '#import site', 'import site' | Set-Content '!PTH_FILE_PATH!'"
) else (
    echo [ERROR] Python configuration file not found.
    goto error
)

rem 4. Install pip
echo [5/7] Setting up package manager (pip)...
powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile 'get-pip.py'"
if not exist "get-pip.py" (
    echo [ERROR] Failed to download get-pip.py script.
    goto error
)
"%TARGET_APP_PATH%\python_env\python.exe" get-pip.py --no-warn-script-location
del get-pip.py

rem 5. Install dependencies (watchdog, pystray, Pillow)
echo [6/7] Installing dependency libraries...
"%TARGET_APP_PATH%\python_env\python.exe" -m pip install watchdog>=3.0.0 pystray>=0.19.0 Pillow>=10.0.0 --no-warn-script-location
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to install dependency libraries.
    goto error
)

rem 6. Copy source files
echo [7/7] Copying program files...
mkdir "%TARGET_APP_PATH%\src"
xcopy /E /I /Y "src" "%TARGET_APP_PATH%\src" >nul
copy "main.py" "%TARGET_APP_PATH%\" >nul

rem Create launch batch file inside the portable directory
(
echo @echo off
echo cd /d "%%~dp0"
echo start "" "%%~dp0python_env\pythonw.exe" "%%~dp0main.py"
echo exit
) > "%TARGET_APP_PATH%\start_tool.bat"

rem 7. Compress into ZIP file
echo ---------------------------------------------------
echo Creating distribution ZIP file...
powershell -Command "Compress-Archive -Path '%TARGET_APP_PATH%' -DestinationPath '%ZIP_FILE_PATH%' -Force"

rem Cleanup temporary directory
if exist "%TARGET_APP_PATH%" (
    rd /s /q "%TARGET_APP_PATH%"
)

echo.
echo ===================================================
echo   Build completed successfully!
echo ===================================================
echo   Package path:
echo   [ZIP] %ZIP_FILE_PATH%
echo.
echo   You can distribute this ZIP file to other users.
echo   Instruct them to extract the ZIP and run "start_tool.bat".
echo ===================================================
goto end

:error
echo.
echo [ERROR] Build failed.
if not "%~1"=="--no-pause" pause
exit /b 1

:end
if not "%~1"=="--no-pause" pause
exit /b 0
