"""
DevManager - Sophisticated installer and auto-updater for DevAutomator Python application.

This package provides both client-side and developer-side functionality:
- Client-side: GUI application for installing and updating DevAutomator
- Developer-side: Build tools for packaging and deploying DevAutomator releases
"""

__version__ = "0.1.1"
__author__ = "CSS Development Team"
__description__ = (
    "DevManager - Sophisticated installer and auto-updater for DevAutomator"
)

from .common.constants import (
    APP_NAME,
    DEFAULT_INSTALL_DIR,
    DEVAUTOMATOR_NAME,
    DEVAUTOMATOR_REPO_NAME,
    DEVMANAGER_REPO_NAME,
    GITHUB_REPO_OWNER,
)
from .common.version import Version

__all__ = [
    "Version",
    "APP_NAME",
    "DEVAUTOMATOR_NAME",
    "DEFAULT_INSTALL_DIR",
    "GITHUB_REPO_OWNER",
    "DEVMANAGER_REPO_NAME",
    "DEVAUTOMATOR_REPO_NAME",
]
