#!/bin/bash
# Build script for DevManager on Linux

set -e  # Exit on any error

echo "Building DevManager for Linux..."

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed or not in PATH"
    exit 1
fi

# Check if PyInstaller is available
if ! python3 -c "import PyInstaller" &> /dev/null; then
    echo "Installing PyInstaller..."
    pip3 install PyInstaller
fi

# Create build directories
mkdir -p build
mkdir -p dist

# Clean previous builds
rm -rf build/dev_manager
rm -f dist/dev_manager

echo "Building executable..."

# Build with PyInstaller
python3 -m PyInstaller \
    --onefile \
    --name dev_manager \
    --distpath dist \
    --workpath build \
    --clean \
    --noconfirm \
    --console \
    src/main.py

# Check if executable was created
if [ ! -f "dist/dev_manager" ]; then
    echo "ERROR: Executable not found after build"
    exit 1
fi

echo "Build completed successfully!"
echo "Executable location: dist/dev_manager"

# Create ZIP package
echo "Creating ZIP package..."
cd dist
zip -r devmanager_linux.zip dev_manager
cd ..

if [ -f "dist/devmanager_linux.zip" ]; then
    echo "ZIP package created: dist/devmanager_linux.zip"
else
    echo "WARNING: Failed to create ZIP package"
fi

echo ""
echo "Build process completed!"
