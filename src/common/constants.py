"""
Constants and configuration values for DevManager.
"""

import platform
from pathlib import Path

# Application Information
APP_NAME = "DevManager"
DEVAUTOMATOR_NAME = "DevAutomator"
VERSION = "0.1.5"

# GitHub Configuration
GITHUB_REPO_OWNER = "cyberionsoft"  # Actual GitHub organization
GITHUB_REPO_NAME = "css_dev_manager"  # For backward compatibility
DEVMANAGER_REPO_NAME = "css_dev_manager"  # Match actual repository name
DEVAUTOMATOR_REPO_NAME = "css_dev_automator"  # Match actual repository name
GITHUB_API_BASE = "https://api.github.com"

# URLs
DEVMANAGER_RELEASES_URL = (
    f"https://github.com/{GITHUB_REPO_OWNER}/{DEVMANAGER_REPO_NAME}/releases"
)
DEVAUTOMATOR_RELEASES_URL = (
    f"https://github.com/{GITHUB_REPO_OWNER}/{DEVAUTOMATOR_REPO_NAME}/releases"
)

# Platform Detection
CURRENT_PLATFORM = platform.system().lower()
CURRENT_ARCH = platform.machine().lower()

# Supported Platforms
SUPPORTED_PLATFORMS = {
    "windows": {
        "name": "Windows",
        "executable_ext": ".exe",
        "archive_ext": ".zip",
        "platform_key": "windows",
    },
    "darwin": {
        "name": "macOS",
        "executable_ext": "",
        "archive_ext": ".zip",
        "platform_key": "macos",
    },
    "linux": {
        "name": "Linux",
        "executable_ext": "",
        "archive_ext": ".zip",
        "platform_key": "linux",
    },
}

# Installation Directories (Windows focus as per requirements)
if CURRENT_PLATFORM == "windows":
    # DevManager installation directory
    DEVMANAGER_INSTALL_DIR = Path("C:/Program Files/DevManager")
    # DevAutomator will be installed in the same directory
    DEVAUTOMATOR_INSTALL_DIR = DEVMANAGER_INSTALL_DIR
    # Configuration and data directory
    CONFIG_DIR = Path.home() / "AppData" / "Local" / APP_NAME
elif CURRENT_PLATFORM == "darwin":
    DEVMANAGER_INSTALL_DIR = Path.home() / "Applications" / APP_NAME
    DEVAUTOMATOR_INSTALL_DIR = DEVMANAGER_INSTALL_DIR
    CONFIG_DIR = Path.home() / "Library" / "Application Support" / APP_NAME
else:  # Linux and others
    DEVMANAGER_INSTALL_DIR = Path.home() / ".local" / "share" / APP_NAME.lower()
    DEVAUTOMATOR_INSTALL_DIR = DEVMANAGER_INSTALL_DIR
    CONFIG_DIR = Path.home() / ".config" / APP_NAME.lower()

# Legacy support
DEFAULT_INSTALL_DIR = DEVAUTOMATOR_INSTALL_DIR

# File Names
CONFIG_FILE = "config.json"
VERSION_FILE = "installed_version.json"
LOG_FILE = "devmanager.log"
TOKEN_FILE = "auth_token.json"

# Token Configuration
TOKEN_LENGTH = 32  # Length of generated tokens
TOKEN_EXPIRY_HOURS = 24  # Token expiry time in hours

# Download Configuration
CHUNK_SIZE = 8192  # 8KB chunks for downloads
MAX_RETRIES = 3
TIMEOUT_SECONDS = 30

# GUI Configuration
WINDOW_WIDTH = 600
WINDOW_HEIGHT = 400
PROGRESS_UPDATE_INTERVAL = 100  # milliseconds

# Build Configuration (for developer-side)
BUILD_DIR = Path("build")
DIST_DIR = Path("dist")
SPEC_DIR = Path("src") / "specs"

# Default build platforms (Windows-only for faster builds)
DEFAULT_BUILD_PLATFORMS = ["windows"]

# PyInstaller Configuration
PYINSTALLER_OPTIONS = {
    "onefile": True,  # Changed to onefile mode for single executable
    "windowed": False,  # Set to True for GUI-only applications
    "clean": True,
    "noconfirm": True,
}

# Logging Configuration
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL = "INFO"
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
LOG_BACKUP_COUNT = 5

# Installation Configuration
INSTALLER_TEMP_DIRS = [
    "Downloads",
    "Desktop",
    "Temp",
    "AppData\\Local\\Temp",
    "Users\\Public\\Downloads"
]

# Registry Configuration (Windows)
REGISTRY_KEY = r"SOFTWARE\CSS Development\DevManager"
UNINSTALL_KEY = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\DevManager"

# Shortcut Configuration
START_MENU_FOLDER = "CSS Development"
DESKTOP_SHORTCUT_NAME = "DevManager.lnk"
START_MENU_SHORTCUT_NAME = "DevManager.lnk"

# Encrypted Constants Access
# These functions provide access to encrypted sensitive data bundled with the application
def get_bundled_github_token():
    """
    Get GitHub token from encrypted constants bundled with the application.

    Returns:
        Decrypted GitHub token or None if not available
    """
    try:
        from .encrypted_constants import get_github_token_from_constants
        return get_github_token_from_constants()
    except ImportError:
        return None


def get_bundled_config_data():
    """
    Get additional configuration data from encrypted constants.

    Returns:
        Decrypted configuration dictionary or None if not available
    """
    try:
        from .encrypted_constants import get_config_from_constants
        return get_config_from_constants()
    except ImportError:
        return None


def has_bundled_github_token():
    """
    Check if a GitHub token is available in bundled encrypted constants.

    Returns:
        True if token is available and can be decrypted
    """
    try:
        from .encrypted_constants import has_encrypted_github_token
        return has_encrypted_github_token()
    except ImportError:
        return False
