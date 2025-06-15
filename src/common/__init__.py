"""
Common utilities and shared components for DevManager.
"""

from .constants import *
from .utils import *
from .version import Version

__all__ = [
    "Version",
    "get_platform_info",
    "calculate_checksum",
    "ensure_directory",
    "safe_extract_zip",
    "APP_NAME",
    "DEVAUTOMATOR_NAME",
    "DEFAULT_INSTALL_DIR",
    "GITHUB_REPO_OWNER",
    "GITHUB_REPO_NAME",
    "MANIFEST_URL",
    "SUPPORTED_PLATFORMS",
]
