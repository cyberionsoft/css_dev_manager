"""
DevManager installer module.

This module provides functionality for installing DevManager on first run
and managing the installation process.
"""

from .first_run_installer import FirstRunInstaller

# Try to import GUI components, but don't fail if PySide6 is not available
try:
    from .install_dialog import show_install_dialog
    __all__ = ["FirstRunInstaller", "show_install_dialog"]
except ImportError:
    # GUI components not available
    def show_install_dialog(*args, **kwargs):
        """Fallback function when GUI is not available."""
        raise ImportError("GUI components not available - PySide6 not installed")

    __all__ = ["FirstRunInstaller", "show_install_dialog"]
