"""
First-run installer for DevManager.

This module handles the initial installation of DevManager to the proper
system directory when run for the first time from a temporary location.
"""

import logging
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Optional

try:
    from ..common.constants import (
        APP_NAME,
        CURRENT_PLATFORM,
        DESKTOP_SHORTCUT_NAME,
        DEVMANAGER_INSTALL_DIR,
        INSTALLER_TEMP_DIRS,
        REGISTRY_KEY,
        START_MENU_FOLDER,
        START_MENU_SHORTCUT_NAME,
        UNINSTALL_KEY,
        VERSION,
    )
    from ..common.utils import ensure_directory, get_executable_path, is_admin
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from common.constants import (
        APP_NAME,
        CURRENT_PLATFORM,
        DESKTOP_SHORTCUT_NAME,
        DEVMANAGER_INSTALL_DIR,
        INSTALLER_TEMP_DIRS,
        REGISTRY_KEY,
        START_MENU_FOLDER,
        START_MENU_SHORTCUT_NAME,
        UNINSTALL_KEY,
        VERSION,
    )
    from common.utils import ensure_directory, get_executable_path, is_admin


class FirstRunInstaller:
    """
    Handles first-run installation of DevManager.
    """

    def __init__(self):
        """Initialize the first-run installer."""
        self.current_exe = get_executable_path()
        self.install_dir = DEVMANAGER_INSTALL_DIR
        self.installed_exe = self.install_dir / "DevManager.exe"

    def needs_installation(self) -> bool:
        """
        Check if DevManager needs to be installed.

        Returns:
            True if installation is needed, False otherwise
        """
        try:
            # Check if we're already running from the install directory
            if self._is_running_from_install_dir():
                logging.info("DevManager is already running from install directory")
                return False

            # Check if we're running from a temporary location
            if self._is_running_from_temp_location():
                logging.info("DevManager is running from temporary location, installation needed")
                return True

            # Check if install directory exists and has DevManager
            if self.installed_exe.exists():
                logging.info("DevManager already installed, but running from different location")
                return False

            logging.info("DevManager not found in install directory, installation needed")
            return True

        except Exception as e:
            logging.error(f"Error checking installation status: {e}")
            return False

    def _is_running_from_install_dir(self) -> bool:
        """
        Check if DevManager is running from the install directory.

        Returns:
            True if running from install directory
        """
        try:
            current_dir = self.current_exe.parent.resolve()
            install_dir = self.install_dir.resolve()
            return current_dir == install_dir
        except Exception:
            return False

    def _is_running_from_temp_location(self) -> bool:
        """
        Check if DevManager is running from a temporary location.

        Returns:
            True if running from a temporary location
        """
        try:
            current_path_str = str(self.current_exe.parent).lower()
            
            # Check against known temporary directories
            for temp_dir in INSTALLER_TEMP_DIRS:
                if temp_dir.lower() in current_path_str:
                    return True
            
            # Check if in system temp directory
            temp_dir = Path(tempfile.gettempdir()).resolve()
            current_dir = self.current_exe.parent.resolve()
            
            try:
                current_dir.relative_to(temp_dir)
                return True
            except ValueError:
                pass
            
            return False
            
        except Exception:
            return False

    def install(self) -> bool:
        """
        Install DevManager to the system directory.

        Returns:
            True if installation successful, False otherwise
        """
        try:
            logging.info(f"Starting DevManager installation to {self.install_dir}")

            # Check for admin privileges on Windows
            if CURRENT_PLATFORM == "windows" and not is_admin():
                logging.info("Requesting administrator privileges for installation")
                return self._install_with_admin_privileges()

            # Create installation directory
            ensure_directory(self.install_dir)

            # Copy executable
            if not self._copy_executable():
                return False

            # Create shortcuts and registry entries
            if CURRENT_PLATFORM == "windows":
                self._create_windows_shortcuts()
                self._create_registry_entries()

            logging.info("DevManager installation completed successfully")
            return True

        except Exception as e:
            logging.error(f"Installation failed: {e}", exc_info=True)
            return False

    def _install_with_admin_privileges(self) -> bool:
        """
        Install DevManager with administrator privileges.

        Returns:
            True if installation successful, False otherwise
        """
        try:
            # Create a temporary installation script
            script_content = self._create_install_script()
            script_path = Path(tempfile.gettempdir()) / "devmanager_install.py"
            
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(script_content)

            # Run the installation script with admin privileges
            if CURRENT_PLATFORM == "windows":
                import ctypes
                
                # Use ShellExecuteW to run with admin privileges
                result = ctypes.windll.shell32.ShellExecuteW(
                    None,
                    "runas",  # Request elevation
                    sys.executable,
                    f'"{script_path}"',
                    None,
                    1  # SW_SHOWNORMAL
                )
                
                if result > 32:  # Success
                    logging.info("Installation script launched with admin privileges")
                    # Exit current process as the elevated script will handle installation
                    return True
                else:
                    logging.error(f"Failed to launch installation script with admin privileges: {result}")
                    return False
            else:
                # For Unix-like systems, use sudo
                result = subprocess.run([
                    "sudo", sys.executable, str(script_path)
                ], capture_output=True, text=True)
                
                return result.returncode == 0

        except Exception as e:
            logging.error(f"Failed to install with admin privileges: {e}", exc_info=True)
            return False

    def _copy_executable(self) -> bool:
        """
        Copy the executable to the installation directory.
        Also copies DevAutomator if available.

        Returns:
            True if successful, False otherwise
        """
        try:
            logging.info(f"Copying executable from {self.current_exe} to {self.installed_exe}")

            # Ensure target directory exists
            self.installed_exe.parent.mkdir(parents=True, exist_ok=True)

            # Copy the DevManager executable
            shutil.copy2(self.current_exe, self.installed_exe)

            # Make executable on Unix-like systems
            if CURRENT_PLATFORM != "windows":
                os.chmod(self.installed_exe, 0o755)

            logging.info("DevManager executable copied successfully")

            # Also copy DevAutomator if it exists in the same directory
            self._copy_devautomator_if_available()

            return True

        except Exception as e:
            logging.error(f"Failed to copy executable: {e}", exc_info=True)
            return False

    def _copy_devautomator_if_available(self) -> None:
        """Copy DevAutomator executable if available in the same directory."""
        try:
            # Look for DevAutomator in the same directory as DevManager
            devautomator_source = self.current_exe.parent / "DevAutomator.exe"
            devautomator_target = self.install_dir / "DevAutomator.exe"

            if devautomator_source.exists():
                logging.info(f"Found DevAutomator, copying to {devautomator_target}")
                shutil.copy2(devautomator_source, devautomator_target)

                # Make executable on Unix-like systems
                if CURRENT_PLATFORM != "windows":
                    os.chmod(devautomator_target, 0o755)

                logging.info("DevAutomator executable copied successfully")
            else:
                logging.info("DevAutomator not found in source directory, will be downloaded later")

        except Exception as e:
            logging.warning(f"Failed to copy DevAutomator: {e}")
            # Don't fail the installation if DevAutomator copy fails

    def restart_from_install_location(self) -> bool:
        """
        Restart DevManager from the installation location.

        Returns:
            True if restart initiated successfully
        """
        try:
            if not self.installed_exe.exists():
                logging.error("Installed executable not found")
                return False

            logging.info(f"Restarting DevManager from {self.installed_exe}")
            
            if CURRENT_PLATFORM == "windows":
                # Use os.startfile for Windows
                os.startfile(str(self.installed_exe))
            else:
                # Use subprocess for Unix-like systems
                subprocess.Popen([str(self.installed_exe)], 
                               start_new_session=True)
            
            return True
            
        except Exception as e:
            logging.error(f"Failed to restart from install location: {e}", exc_info=True)
            return False

    def _create_windows_shortcuts(self) -> None:
        """Create Windows shortcuts for DevManager."""
        try:
            if CURRENT_PLATFORM != "windows":
                return

            # Create desktop shortcut
            self._create_desktop_shortcut()

            # Create start menu shortcut
            self._create_start_menu_shortcut()

        except Exception as e:
            logging.warning(f"Failed to create shortcuts: {e}")

    def _create_desktop_shortcut(self) -> None:
        """Create desktop shortcut."""
        try:
            import winshell
            from win32com.client import Dispatch

            desktop = winshell.desktop()
            shortcut_path = Path(desktop) / DESKTOP_SHORTCUT_NAME

            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(str(shortcut_path))
            shortcut.Targetpath = str(self.installed_exe)
            shortcut.WorkingDirectory = str(self.install_dir)
            shortcut.Description = f"{APP_NAME} - DevAutomator Installer and Updater"
            shortcut.save()

            logging.info(f"Desktop shortcut created: {shortcut_path}")

        except ImportError:
            logging.warning("winshell or pywin32 not available, skipping desktop shortcut")
        except Exception as e:
            logging.warning(f"Failed to create desktop shortcut: {e}")

    def _create_start_menu_shortcut(self) -> None:
        """Create start menu shortcut."""
        try:
            import winshell
            from win32com.client import Dispatch

            start_menu = winshell.start_menu()
            folder_path = Path(start_menu) / START_MENU_FOLDER
            folder_path.mkdir(exist_ok=True)

            shortcut_path = folder_path / START_MENU_SHORTCUT_NAME

            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(str(shortcut_path))
            shortcut.Targetpath = str(self.installed_exe)
            shortcut.WorkingDirectory = str(self.install_dir)
            shortcut.Description = f"{APP_NAME} - DevAutomator Installer and Updater"
            shortcut.save()

            logging.info(f"Start menu shortcut created: {shortcut_path}")

        except ImportError:
            logging.warning("winshell or pywin32 not available, skipping start menu shortcut")
        except Exception as e:
            logging.warning(f"Failed to create start menu shortcut: {e}")

    def _create_registry_entries(self) -> None:
        """Create Windows registry entries."""
        try:
            if CURRENT_PLATFORM != "windows":
                return

            import winreg

            # Create application registry key
            with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, REGISTRY_KEY) as key:
                winreg.SetValueEx(key, "InstallPath", 0, winreg.REG_SZ, str(self.install_dir))
                winreg.SetValueEx(key, "Version", 0, winreg.REG_SZ, VERSION)
                winreg.SetValueEx(key, "ExecutablePath", 0, winreg.REG_SZ, str(self.installed_exe))

            # Create uninstall registry entry
            with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, UNINSTALL_KEY) as key:
                winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, APP_NAME)
                winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, VERSION)
                winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, "CSS Development")
                winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, str(self.install_dir))
                winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ,
                                f'"{self.installed_exe}" --uninstall')
                winreg.SetValueEx(key, "NoModify", 0, winreg.REG_DWORD, 1)
                winreg.SetValueEx(key, "NoRepair", 0, winreg.REG_DWORD, 1)

            logging.info("Registry entries created successfully")

        except ImportError:
            logging.warning("winreg not available, skipping registry entries")
        except Exception as e:
            logging.warning(f"Failed to create registry entries: {e}")

    def _create_install_script(self) -> str:
        """
        Create installation script for elevated execution.

        Returns:
            Installation script content
        """
        return f'''#!/usr/bin/env python3
"""
DevManager installation script with elevated privileges.
This script is automatically generated and executed with admin rights.
"""

import logging
import os
import shutil
import sys
import time
from pathlib import Path

# Configuration
CURRENT_EXE = Path(r"{self.current_exe}")
INSTALL_DIR = Path(r"{self.install_dir}")
INSTALLED_EXE = INSTALL_DIR / "DevManager.exe"

def setup_logging():
    """Set up logging for the installation script."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    """Main installation function."""
    setup_logging()

    try:
        logging.info("Starting DevManager installation with elevated privileges")

        # Create installation directory
        INSTALL_DIR.mkdir(parents=True, exist_ok=True)
        logging.info(f"Created installation directory: {{INSTALL_DIR}}")

        # Copy executable
        if CURRENT_EXE.exists():
            shutil.copy2(CURRENT_EXE, INSTALLED_EXE)
            logging.info(f"Copied executable to: {{INSTALLED_EXE}}")
        else:
            logging.error(f"Source executable not found: {{CURRENT_EXE}}")
            return 1

        # Start the installed version
        if INSTALLED_EXE.exists():
            logging.info("Starting DevManager from installed location")
            os.startfile(str(INSTALLED_EXE))
        else:
            logging.error("Failed to find installed executable")
            return 1

        logging.info("Installation completed successfully")
        time.sleep(2)  # Give user time to see the message
        return 0

    except Exception as e:
        logging.error(f"Installation failed: {{e}}")
        input("Press Enter to exit...")
        return 1

if __name__ == "__main__":
    sys.exit(main())
'''
