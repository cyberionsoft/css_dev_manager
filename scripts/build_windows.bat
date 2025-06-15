@echo off
REM Build script for DevManager on Windows

echo Building DevManager for Windows...

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    exit /b 1
)

REM Check if PyInstaller is available
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install PyInstaller
)

REM Create build directories
if not exist "build" mkdir build
if not exist "dist" mkdir dist

REM Clean previous builds
if exist "build\dev_manager" rmdir /s /q "build\dev_manager"
if exist "dist\dev_manager.exe" del "dist\dev_manager.exe"

echo Building executable...

REM Build with PyInstaller
pyinstaller ^
    --onefile ^
    --name dev_manager ^
    --distpath dist ^
    --workpath build ^
    --clean ^
    --noconfirm ^
    --console ^
    src\main.py

if errorlevel 1 (
    echo ERROR: Build failed
    exit /b 1
)

REM Check if executable was created
if not exist "dist\dev_manager.exe" (
    echo ERROR: Executable not found after build
    exit /b 1
)

echo Build completed successfully!
echo Executable location: dist\dev_manager.exe

REM Create ZIP package
echo Creating ZIP package...
powershell -Command "Compress-Archive -Path 'dist\dev_manager.exe' -DestinationPath 'dist\devmanager_windows.zip' -Force"

if exist "dist\devmanager_windows.zip" (
    echo ZIP package created: dist\devmanager_windows.zip
) else (
    echo WARNING: Failed to create ZIP package
)

echo.
echo Build process completed!
pause
