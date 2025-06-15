# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for packaging DevAutomator.

This spec file is designed to be used by DevManager's build system
to create standalone executables of DevAutomator for distribution.
"""

import os
import sys
from pathlib import Path

# Configuration - these will be set by the build system
DEVAUTOMATOR_PATH = os.environ.get('DEVAUTOMATOR_PATH', '.')
VERSION = os.environ.get('BUILD_VERSION', '0.1.1')
PLATFORM = os.environ.get('TARGET_PLATFORM', 'windows')

# Convert to Path objects
devautomator_path = Path(DEVAUTOMATOR_PATH)
spec_dir = Path(SPECPATH)

# Determine main script
main_script = devautomator_path / 'main.py'
if not main_script.exists():
    # Try alternative locations
    alternatives = [
        devautomator_path / 'devautomator' / 'main.py',
        devautomator_path / 'src' / 'main.py',
        devautomator_path / 'app.py',
    ]
    for alt in alternatives:
        if alt.exists():
            main_script = alt
            break
    else:
        raise FileNotFoundError(f"Could not find main script in {devautomator_path}")

print(f"Building DevAutomator from: {main_script}")
print(f"Version: {VERSION}")
print(f"Platform: {PLATFORM}")

# Data files to include
datas = []

# Include Templates directory (case-sensitive)
templates_dir = devautomator_path / 'Templates'
if templates_dir.exists():
    datas.append((str(templates_dir), 'Templates'))

# Include static files if they exist
static_dir = devautomator_path / 'static'
if static_dir.exists():
    datas.append((str(static_dir), 'static'))

# Include config files
config_files = [
    'config.yaml',
    'config.yml', 
    'config.json',
    'settings.yaml',
    'settings.yml',
    'settings.json'
]

for config_file in config_files:
    config_path = devautomator_path / config_file
    if config_path.exists():
        datas.append((str(config_path), '.'))

# Include any data directories
data_dirs = ['data', 'assets', 'resources']
for data_dir in data_dirs:
    data_path = devautomator_path / data_dir
    if data_path.exists():
        datas.append((str(data_path), data_dir))

# Hidden imports - common packages that PyInstaller might miss
hiddenimports = [
    'pkg_resources.py2_warn',
    'packaging.version',
    'packaging.specifiers',
    'packaging.requirements',
    'yaml',
    'jinja2',
    'jinja2.ext',
    'requests',
    'urllib3',
    'certifi',
]

# Platform-specific settings
if PLATFORM == 'windows':
    console = True  # Set to False for windowed apps
    icon = None
    # Look for Windows icon
    icon_path = devautomator_path / 'icon.ico'
    if icon_path.exists():
        icon = str(icon_path)
elif PLATFORM in ['darwin', 'macos']:
    console = True
    icon = None
    # Look for macOS icon
    icon_path = devautomator_path / 'icon.icns'
    if icon_path.exists():
        icon = str(icon_path)
else:  # Linux and others
    console = True
    icon = None

# Analysis
a = Analysis(
    [str(main_script)],
    pathex=[str(devautomator_path)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'PIL',
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# Remove duplicate entries
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# Create single executable (onefile mode)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='devautomator',
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
        name='DevAutomator.app',
        icon=icon,
        bundle_identifier='com.css.devautomator',
        version=VERSION,
        info_plist={
            'CFBundleDisplayName': 'DevAutomator',
            'CFBundleVersion': VERSION,
            'CFBundleShortVersionString': VERSION,
            'NSHighResolutionCapable': True,
        },
    )
