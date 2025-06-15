# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for packaging DevManager.

This spec file creates a standalone executable of DevManager
for distribution to end users.
"""

import os
import sys
from pathlib import Path

# Configuration
VERSION = os.environ.get('BUILD_VERSION', '0.1.1')
PLATFORM = os.environ.get('TARGET_PLATFORM', 'windows')

# Paths
spec_dir = Path(SPECPATH)
devmanager_root = spec_dir.parent.parent  # Go up from specs/ to project root

# Main script
main_script = devmanager_root / 'src' / 'main.py'

print(f"Building DevManager from: {main_script}")
print(f"Version: {VERSION}")
print(f"Platform: {PLATFORM}")

# Data files to include
datas = []

# Include .env file for configuration (without sensitive data)
env_file = devmanager_root / '.env'
if env_file.exists():
    datas.append((str(env_file), '.'))

# Include .env.example for reference
env_example_file = devmanager_root / '.env.example'
if env_example_file.exists():
    datas.append((str(env_example_file), '.'))

# Include any configuration templates
config_dir = devmanager_root / 'src' / 'config'
if config_dir.exists():
    for config_file in config_dir.glob('*.json'):
        datas.append((str(config_file), 'config'))

# Hidden imports for DevManager
hiddenimports = [
    # PySide6 modules
    'PySide6.QtCore',
    'PySide6.QtWidgets',
    'PySide6.QtGui',

    # HTTP client
    'httpx',
    'httpx._client',
    'httpx._config',
    'httpx._models',
    'httpx._transports',

    # GitHub API
    'github',
    'github.Repository',
    'github.GitRelease',

    # Packaging
    'packaging.version',
    'packaging.specifiers',
    'packaging.requirements',

    # YAML support
    'yaml',
    'yaml.loader',
    'yaml.dumper',

    # Crypto and encryption modules
    'cryptography',
    'cryptography.fernet',
    'cryptography.hazmat.primitives',
    'cryptography.hazmat.primitives.hashes',
    'cryptography.hazmat.primitives.kdf.pbkdf2',

    # DevManager encryption modules
    'src.common.crypto_utils',
    'src.common.encrypted_constants',

    # JWT support
    'jwt',
    'jwt.algorithms',

    # Standard library modules that might be missed
    'zipfile',
    'hashlib',
    'json',
    'pathlib',
    'subprocess',
    'threading',
    'logging.handlers',
    'base64',

    # Essential setuptools dependencies only
    'setuptools._vendor.jaraco.text',
    'setuptools._vendor.jaraco.functools',
    'setuptools._vendor.jaraco.context',
]

# Platform-specific settings
if PLATFORM == 'windows':
    console = False  # GUI application
    icon = None
    # Look for Windows icon
    icon_path = devmanager_root / 'assets' / 'devmanager.ico'
    if icon_path.exists():
        icon = str(icon_path)
elif PLATFORM in ['darwin', 'macos']:
    console = False
    icon = None
    # Look for macOS icon
    icon_path = devmanager_root / 'assets' / 'devmanager.icns'
    if icon_path.exists():
        icon = str(icon_path)
else:  # Linux and others
    console = False
    icon = None

# Analysis
a = Analysis(
    [str(main_script)],
    pathex=[str(devmanager_root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unnecessary packages to reduce size
        'tkinter',
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'PIL',
        'PyQt5',
        'PyQt6',
        'PySide2',
        'jupyter',
        'IPython',
        'notebook',
        'sphinx',
        'pytest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# Remove duplicate entries and optimize
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# Create single executable (onefile mode)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='devmanager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=console,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon,
)

# Platform-specific bundle creation
if PLATFORM in ['darwin', 'macos']:
    # Create macOS app bundle
    app = BUNDLE(
        exe,
        name='DevManager.app',
        icon=icon,
        bundle_identifier='com.css.devmanager',
        version=VERSION,
        info_plist={
            'CFBundleDisplayName': 'DevManager',
            'CFBundleVersion': VERSION,
            'CFBundleShortVersionString': VERSION,
            'NSHighResolutionCapable': True,
            'LSMinimumSystemVersion': '10.14',  # macOS Mojave minimum
        },
    )
