"""
PyInstaller integration for packaging DevAutomator and DevManager.
"""

import logging
import os
import subprocess
import zipfile
from pathlib import Path

from ..common.constants import BUILD_DIR, DIST_DIR, SPEC_DIR, SUPPORTED_PLATFORMS
from ..common.utils import calculate_checksum, ensure_directory, safe_remove_directory


class Packager:
    """
    Handles PyInstaller packaging for DevAutomator and DevManager.
    """

    def __init__(self, project_path: Path):
        """
        Initialize the packager.

        Args:
            project_path: Path to the project to package
        """
        self.project_path = Path(project_path)
        self.build_dir = BUILD_DIR
        self.dist_dir = DIST_DIR
        self.spec_dir = SPEC_DIR

        logging.info(f"Packager initialized for: {self.project_path}")

    def build_for_platform(self, platform: str, version: str) -> Path | None:
        """
        Build the project for a specific platform.

        Args:
            platform: Target platform (windows, darwin, linux)
            version: Version string

        Returns:
            Path to the created archive or None if failed
        """
        if platform not in SUPPORTED_PLATFORMS:
            logging.error(f"Unsupported platform: {platform}")
            return None

        try:
            logging.info(f"Building for platform: {platform}")

            # Determine which spec file to use
            spec_file = self._get_spec_file()
            if not spec_file:
                return None

            # Set up environment variables for the build
            env = self._setup_build_environment(platform, version)

            # Run PyInstaller
            if not self._run_pyinstaller(spec_file, env):
                return None

            # Create distribution archive
            archive_path = self._create_archive(platform, version)

            return archive_path

        except Exception as e:
            logging.error(f"Build failed for platform {platform}: {e}", exc_info=True)
            return None

    def _get_spec_file(self) -> Path | None:
        """
        Determine which spec file to use based on the project.

        Returns:
            Path to the spec file or None if not found
        """
        # Check if this is DevAutomator or DevManager by looking at project structure
        if (self.project_path / "src" / "builder").exists():
            # This is the DevManager project (has builder module)
            spec_file = self.spec_dir / "devmanager.spec"
        elif (self.project_path / "src" / "gui_manager.py").exists():
            # This is DevAutomator (has gui_manager)
            spec_file = self.spec_dir / "devautomator.spec"
        else:
            # Default to devmanager if we can't determine
            spec_file = self.spec_dir / "devmanager.spec"

        if not spec_file.exists():
            logging.error(f"Spec file not found: {spec_file}")
            return None

        return spec_file

    def _setup_build_environment(self, platform: str, version: str) -> dict[str, str]:
        """
        Set up environment variables for the build.

        Args:
            platform: Target platform
            version: Version string

        Returns:
            Environment variables dictionary
        """
        env = os.environ.copy()

        # Set build-specific environment variables
        env["DEVAUTOMATOR_PATH"] = str(self.project_path)
        env["BUILD_VERSION"] = version
        env["TARGET_PLATFORM"] = platform
        env["PYTHONPATH"] = str(self.project_path)

        # Platform-specific settings
        platform_info = SUPPORTED_PLATFORMS[platform]
        env["PLATFORM_KEY"] = platform_info["platform_key"]
        env["EXECUTABLE_EXT"] = platform_info["executable_ext"]
        env["ARCHIVE_EXT"] = platform_info["archive_ext"]

        return env

    def _run_pyinstaller(self, spec_file: Path, env: dict[str, str]) -> bool:
        """
        Run PyInstaller with the specified spec file.

        Args:
            spec_file: Path to the spec file
            env: Environment variables

        Returns:
            True if successful, False otherwise
        """
        try:
            # Prepare PyInstaller command
            cmd = [
                "pyinstaller",
                "--clean",
                "--noconfirm",
                "--distpath",
                str(self.dist_dir),
                "--workpath",
                str(self.build_dir),
                str(spec_file),
            ]

            logging.info(f"Running PyInstaller: {' '.join(cmd)}")

            # Run PyInstaller
            result = subprocess.run(
                cmd,
                env=env,
                cwd=str(self.project_path),
                capture_output=True,
                text=True,
                timeout=1800,  # 30 minutes timeout
            )

            if result.returncode == 0:
                logging.info("PyInstaller completed successfully")
                return True
            else:
                logging.error(
                    f"PyInstaller failed with return code {result.returncode}"
                )
                logging.error(f"STDOUT: {result.stdout}")
                logging.error(f"STDERR: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            logging.error("PyInstaller timed out")
            return False
        except Exception as e:
            logging.error(f"Failed to run PyInstaller: {e}", exc_info=True)
            return False

    def _create_archive(self, platform: str, version: str) -> Path | None:
        """
        Create a ZIP archive of the built application.

        Args:
            platform: Target platform
            version: Version string

        Returns:
            Path to the created archive or None if failed
        """
        try:
            # Determine the application name
            app_name = self._get_app_name()

            # Find the built application directory
            app_dir = self.dist_dir / app_name
            if not app_dir.exists():
                logging.error(f"Built application directory not found: {app_dir}")
                return None

            # Create archive filename
            platform_info = SUPPORTED_PLATFORMS[platform]
            archive_name = f"{app_name}_{version}_{platform_info['platform_key']}.zip"
            archive_path = self.dist_dir / archive_name

            logging.info(f"Creating archive: {archive_path}")

            # Create ZIP archive
            with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                for file_path in app_dir.rglob("*"):
                    if file_path.is_file():
                        # Calculate relative path within the archive
                        arcname = file_path.relative_to(app_dir)
                        zipf.write(file_path, arcname)

            # Verify archive was created
            if archive_path.exists():
                file_size = archive_path.stat().st_size
                checksum = calculate_checksum(archive_path)

                logging.info("Archive created successfully:")
                logging.info(f"  Path: {archive_path}")
                logging.info(f"  Size: {file_size} bytes")
                logging.info(f"  SHA256: {checksum}")

                return archive_path
            else:
                logging.error("Archive was not created")
                return None

        except Exception as e:
            logging.error(f"Failed to create archive: {e}", exc_info=True)
            return None

    def _get_app_name(self) -> str:
        """
        Get the application name based on the project.

        Returns:
            Application name
        """
        # Check if this is DevAutomator or DevManager by looking at project structure
        if (self.project_path / "src" / "builder").exists():
            # This is the DevManager project (has builder module)
            return "devmanager"
        elif (self.project_path / "src" / "gui_manager.py").exists():
            # This is DevAutomator (has gui_manager)
            return "devautomator"
        else:
            # Default to devmanager if we can't determine
            return "devmanager"

    def get_build_info(self, archive_path: Path) -> dict[str, any]:
        """
        Get build information for an archive.

        Args:
            archive_path: Path to the archive

        Returns:
            Dictionary with build information
        """
        try:
            if not archive_path.exists():
                return {}

            file_size = archive_path.stat().st_size
            checksum = calculate_checksum(archive_path)

            return {
                "path": str(archive_path),
                "size": file_size,
                "checksum": checksum,
                "filename": archive_path.name,
            }

        except Exception as e:
            logging.error(f"Failed to get build info for {archive_path}: {e}")
            return {}

    def clean_build_artifacts(self) -> None:
        """Clean up build artifacts."""
        logging.info("Cleaning build artifacts")

        # Remove build directory
        if self.build_dir.exists():
            safe_remove_directory(self.build_dir)

        # Remove dist directory contents (but keep the directory)
        if self.dist_dir.exists():
            for item in self.dist_dir.iterdir():
                if item.is_dir():
                    safe_remove_directory(item)
                else:
                    try:
                        item.unlink()
                    except Exception as e:
                        logging.warning(f"Failed to remove {item}: {e}")

        # Recreate directories
        ensure_directory(self.build_dir)
        ensure_directory(self.dist_dir)

    def validate_build_environment(self) -> bool:
        """
        Validate that the build environment is properly set up.

        Returns:
            True if environment is valid, False otherwise
        """
        try:
            # Check if PyInstaller is available
            result = subprocess.run(
                ["pyinstaller", "--version"], capture_output=True, text=True, timeout=10
            )

            if result.returncode != 0:
                logging.error("PyInstaller is not available")
                return False

            logging.info(f"PyInstaller version: {result.stdout.strip()}")

            # Check if project path exists
            if not self.project_path.exists():
                logging.error(f"Project path does not exist: {self.project_path}")
                return False

            # Check if spec files exist
            spec_file = self._get_spec_file()
            if not spec_file:
                return False

            logging.info("Build environment validation passed")
            return True

        except Exception as e:
            logging.error(f"Build environment validation failed: {e}", exc_info=True)
            return False
