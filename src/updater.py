"""
Updater classes for DevManager and DevAutomator.
"""

import logging
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

import httpx
import psutil
from packaging import version

try:
    from .common.constants import (
        CURRENT_PLATFORM,
        DEVAUTOMATOR_INSTALL_DIR,
        DEVAUTOMATOR_REPO_NAME,
        DEVMANAGER_INSTALL_DIR,
        DEVMANAGER_REPO_NAME,
        GITHUB_REPO_OWNER,
        SUPPORTED_PLATFORMS,
        VERSION,
    )
    from .common.utils import ensure_directory
except ImportError:
    import sys

    sys.path.insert(0, str(Path(__file__).parent))
    from common.constants import (
        CURRENT_PLATFORM,
        DEVAUTOMATOR_INSTALL_DIR,
        DEVAUTOMATOR_REPO_NAME,
        DEVMANAGER_INSTALL_DIR,
        DEVMANAGER_REPO_NAME,
        GITHUB_REPO_OWNER,
        SUPPORTED_PLATFORMS,
        VERSION,
    )
    from common.utils import ensure_directory


class BaseUpdater:
    """Base class for updaters."""

    def __init__(self, app_name: str, repo_name: str):
        """
        Initialize the base updater.

        Args:
            app_name: Name of the application
            repo_name: GitHub repository name
        """
        self.app_name = app_name
        self.repo_name = repo_name
        self.current_version = VERSION
        self.platform_info = SUPPORTED_PLATFORMS.get(CURRENT_PLATFORM, {})

    def check_for_updates(self) -> bool:
        """
        Check if updates are available.

        Returns:
            True if updates are available, False otherwise
        """
        try:
            latest_version = self._get_latest_version()
            if not latest_version:
                return False

            current_ver = version.parse(self.current_version)
            latest_ver = version.parse(latest_version)

            return latest_ver > current_ver

        except Exception as e:
            logging.error(f"Error checking for updates: {e}")
            return False

    def _get_latest_version(self) -> str | None:
        """
        Get the latest version from GitHub releases.

        Returns:
            Latest version string or None if failed
        """
        try:
            url = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{self.repo_name}/releases/latest"

            with httpx.Client() as client:
                response = client.get(url, timeout=30)
                response.raise_for_status()

                release_data = response.json()
                return release_data.get("tag_name", "").lstrip("v")

        except Exception as e:
            logging.error(f"Error getting latest version: {e}")
            return None

    def _download_release(self, version_tag: str, install_dir: Path) -> Path | None:
        """
        Download the release for the current platform.

        Args:
            version_tag: Version tag to download
            install_dir: Installation directory

        Returns:
            Path to downloaded file or None if failed
        """
        try:
            # Get release information
            url = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{self.repo_name}/releases/tags/v{version_tag}"

            with httpx.Client() as client:
                response = client.get(url, timeout=30)
                response.raise_for_status()

                release_data = response.json()
                assets = release_data.get("assets", [])

                # Find the asset for current platform
                platform_key = self.platform_info.get("platform_key", CURRENT_PLATFORM)
                asset_name = f"{self.app_name.lower()}_{platform_key}.zip"

                download_url = None
                for asset in assets:
                    if asset["name"] == asset_name:
                        download_url = asset["browser_download_url"]
                        break

                if not download_url:
                    logging.error(f"No asset found for platform: {platform_key}")
                    return None

                # Download the file
                logging.info(f"Downloading {asset_name}...")

                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=".zip"
                ) as temp_file:
                    with client.stream("GET", download_url) as stream:
                        stream.raise_for_status()
                        for chunk in stream.iter_bytes():
                            temp_file.write(chunk)

                    return Path(temp_file.name)

        except Exception as e:
            logging.error(f"Error downloading release: {e}")
            return None


class DevManagerUpdater(BaseUpdater):
    """Updater for DevManager itself."""

    def __init__(self):
        """Initialize DevManager updater."""
        super().__init__("DevManager", DEVMANAGER_REPO_NAME)
        self.install_dir = DEVMANAGER_INSTALL_DIR

    def download_and_install_update(self) -> bool:
        """
        Download and install DevManager update.

        Returns:
            True if successful, False otherwise
        """
        try:
            latest_version = self._get_latest_version()
            if not latest_version:
                return False

            # Download the update
            downloaded_file = self._download_release(latest_version, self.install_dir)
            if not downloaded_file:
                return False

            # Create self-update script
            self._create_self_update_script(downloaded_file)

            return True

        except Exception as e:
            logging.error(f"Error downloading and installing update: {e}")
            return False

    def _create_self_update_script(self, update_file: Path) -> None:
        """
        Create a script to perform self-update with UAC elevation support.

        Args:
            update_file: Path to the downloaded update file
        """
        script_content = f'''
import os
import sys
import time
import shutil
import zipfile
import subprocess
from pathlib import Path

def is_admin():
    """Check if running with admin privileges."""
    try:
        if os.name == 'nt':  # Windows
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        else:
            return os.geteuid() == 0
    except Exception:
        return False

def run_as_admin():
    """Re-run the script with admin privileges."""
    if os.name == 'nt':  # Windows
        import ctypes
        try:
            # Re-run with UAC elevation
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv), None, 1
            )
            return True
        except Exception as e:
            print(f"Failed to elevate privileges: {{e}}")
            return False
    else:
        # Unix-like systems
        try:
            subprocess.run(['sudo'] + [sys.executable] + sys.argv)
            return True
        except Exception as e:
            print(f"Failed to elevate privileges: {{e}}")
            return False

def main():
    # Check if we need admin privileges for installation directory
    install_dir = Path(r"{self.install_dir}")

    # If installing to Program Files and not admin, try to elevate
    if (os.name == 'nt' and
        'program files' in str(install_dir).lower() and
        not is_admin()):
        print("Administrator privileges required for installation.")
        if run_as_admin():
            return  # Script will be re-run with admin privileges
        else:
            print("Failed to obtain administrator privileges. Update cancelled.")
            input("Press Enter to exit...")
            sys.exit(1)

    # Wait for DevManager to exit
    time.sleep(3)

    try:
        # Extract update
        update_file = Path(r"{update_file}")

        print("Starting DevManager self-update...")

        # Ensure install directory exists
        install_dir.mkdir(parents=True, exist_ok=True)

        # Backup current installation if it exists
        backup_dir = install_dir.parent / "DevManager_backup"
        if install_dir.exists() and any(install_dir.iterdir()):
            if backup_dir.exists():
                shutil.rmtree(backup_dir)
            shutil.copytree(install_dir, backup_dir)
            print("Created backup of current installation")

        # Extract new version
        with zipfile.ZipFile(update_file, 'r') as zip_ref:
            zip_ref.extractall(install_dir)
        print("Extracted new version")

        # Clean up
        update_file.unlink()

        # Restart DevManager
        exe_path = install_dir / "DevManager.exe"
        if exe_path.exists():
            print("Restarting DevManager...")
            if os.name == 'nt':  # Windows
                os.startfile(str(exe_path))
            else:  # Unix-like
                os.system(f'"{{exe_path}}" &')
        else:
            print(f"ERROR: DevManager executable not found at {{str(exe_path)}}")
            input("Press Enter to exit...")
            sys.exit(1)

        print("DevManager update completed successfully")
        if os.name == 'nt':
            time.sleep(2)  # Give user time to see the message

    except Exception as e:
        print(f"Update failed: {{e}}")
        # Try to restore backup if available
        backup_dir = Path(r"{self.install_dir}").parent / "DevManager_backup"
        if backup_dir.exists():
            try:
                install_dir = Path(r"{self.install_dir}")
                if install_dir.exists():
                    shutil.rmtree(install_dir)
                shutil.copytree(backup_dir, install_dir)
                print("Restored backup due to update failure")
            except Exception as restore_error:
                print(f"Failed to restore backup: {{restore_error}}")
        input("Press Enter to exit...")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''

        script_path = Path(tempfile.gettempdir()) / "devmanager_update.py"
        with open(script_path, "w") as f:
            f.write(script_content)

        # Execute the update script
        if CURRENT_PLATFORM == "windows":
            # On Windows, use CREATE_NEW_CONSOLE to show the update progress
            subprocess.Popen(
                [sys.executable, str(script_path)],
                creationflags=subprocess.CREATE_NEW_CONSOLE,
            )
        else:
            subprocess.Popen([sys.executable, str(script_path)])


class DevAutomatorUpdater(BaseUpdater):
    """Updater for DevAutomator."""

    def __init__(self):
        """Initialize DevAutomator updater."""
        super().__init__("DevAutomator", DEVAUTOMATOR_REPO_NAME)
        self.install_dir = DEVAUTOMATOR_INSTALL_DIR
        self.exe_name = f"DevAutomator{self.platform_info.get('executable_ext', '')}"

    def download_and_install_update(self) -> bool:
        """
        Download and install DevAutomator update.

        Returns:
            True if successful, False otherwise
        """
        try:
            latest_version = self._get_latest_version()
            if not latest_version:
                return False

            # Download the update
            downloaded_file = self._download_release(latest_version, self.install_dir)
            if not downloaded_file:
                return False

            # Stop DevAutomator if running
            self.stop_devautomator()

            # Extract and install
            ensure_directory(self.install_dir)

            with zipfile.ZipFile(downloaded_file, "r") as zip_ref:
                zip_ref.extractall(self.install_dir)

            # Clean up
            downloaded_file.unlink()

            logging.info("DevAutomator updated successfully")
            return True

        except Exception as e:
            logging.error(f"Error updating DevAutomator: {e}")
            return False

    def stop_devautomator(self) -> bool:
        """
        Stop DevAutomator if it's running using psutil for better process management.

        Returns:
            True if successful, False otherwise
        """
        try:
            processes_found = []

            # Find DevAutomator processes
            for proc in psutil.process_iter(["pid", "name", "exe", "cmdline"]):
                try:
                    proc_info = proc.info
                    proc_name = proc_info.get("name", "").lower()
                    proc_exe = proc_info.get("exe", "")
                    proc_cmdline = " ".join(proc_info.get("cmdline", [])).lower()

                    # Check if this is a DevAutomator process
                    if (
                        self.exe_name.lower() in proc_name
                        or "devautomator" in proc_name
                        or "devautomator" in proc_cmdline
                        or (proc_exe and "devautomator" in proc_exe.lower())
                    ):
                        processes_found.append(proc)

                except (
                    psutil.NoSuchProcess,
                    psutil.AccessDenied,
                    psutil.ZombieProcess,
                ):
                    continue

            if not processes_found:
                logging.info("No DevAutomator processes found")
                return True

            # Terminate processes gracefully first
            for proc in processes_found:
                try:
                    logging.info(f"Terminating DevAutomator process {proc.pid}")
                    proc.terminate()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            # Wait for processes to terminate
            gone, alive = psutil.wait_procs(processes_found, timeout=10)

            # Force kill any remaining processes
            for proc in alive:
                try:
                    logging.warning(f"Force killing DevAutomator process {proc.pid}")
                    proc.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            # Final check
            if alive:
                psutil.wait_procs(alive, timeout=5)

            logging.info(f"Stopped {len(processes_found)} DevAutomator process(es)")
            return True

        except Exception as e:
            logging.error(f"Error stopping DevAutomator: {e}")
            return False

    def start_devautomator_with_token(self, token: str) -> bool:
        """
        Start DevAutomator with a token.

        Args:
            token: Authentication token

        Returns:
            True if successful, False otherwise
        """
        try:
            exe_path = self.install_dir / self.exe_name

            if not exe_path.exists():
                logging.error(f"DevAutomator executable not found: {exe_path}")
                return False

            # Start DevAutomator with token
            subprocess.Popen(
                [str(exe_path), "--token", token], cwd=str(self.install_dir)
            )

            logging.info("DevAutomator started with token")
            return True

        except Exception as e:
            logging.error(f"Error starting DevAutomator: {e}")
            return False
