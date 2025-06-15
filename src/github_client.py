"""
GitHub client for building and releasing DevManager and DevAutomator.
"""

import logging
import subprocess
import tempfile
from pathlib import Path

from github import Github, GithubException

try:
    from .common.constants import VERSION
except ImportError:
    # Fallback for direct execution
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from common.constants import VERSION

# GitHub Configuration
GITHUB_CONFIG = {
    "owner": "cyberionsoft",
    "repos": {
        "devmanager": "css_dev_manager",
        "devautomator": "css_dev_automator"
    },
    "urls": {
        "devmanager": "https://github.com/cyberionsoft/css_dev_manager",
        "devautomator": "https://github.com/cyberionsoft/css_dev_automator"
    },
    "release_format": "v{version}",
    "asset_naming": {
        "devmanager": "DevManager_v{version}_{platform}.zip",
        "devautomator": "DevAutomator_v{version}_{platform}.zip"
    }
}

try:
    from .common.constants import VERSION
    from .common.utils import get_platform_info
    from .secure_config import get_secure_config
except ImportError:
    import sys

    sys.path.insert(0, str(Path(__file__).parent))
    from common.constants import VERSION
    from common.utils import get_platform_info
    from secure_config import get_secure_config


class GitHubClient:
    """
    Client for interacting with GitHub for build and release operations.
    """

    def __init__(self):
        """Initialize the GitHub client."""
        # Get token with multiple fallback sources:
        # 1. Bundled encrypted constants (highest priority)
        # 2. Secure config storage
        # 3. Environment variable (lowest priority)
        self.github_token = self._get_github_token_with_fallbacks()

        if not self.github_token:
            raise ValueError("GitHub token not configured. Please configure it in GitHub Settings or use the encryption utility.")

        self.github = Github(self.github_token)
        self.platform_info = get_platform_info()
        self.config = GITHUB_CONFIG

        # Test connection on initialization
        self._test_connection()

    def _get_github_token_with_fallbacks(self) -> str:
        """
        Get GitHub token with multiple fallback sources.

        Returns:
            GitHub token from the first available source
        """
        import logging

        # 1. Try bundled encrypted constants first (highest priority)
        try:
            from .common.constants import get_bundled_github_token
            token = get_bundled_github_token()
            if token:
                logging.info("Using GitHub token from bundled encrypted constants")
                return token
        except Exception as e:
            logging.debug(f"Could not get token from bundled constants: {e}")

        # 2. Try secure config storage
        try:
            secure_config = get_secure_config()
            token = secure_config.get_github_token()
            if token:
                logging.info("Using GitHub token from secure config storage")
                return token
        except Exception as e:
            logging.debug(f"Could not get token from secure config: {e}")

        # 3. Try environment variable (lowest priority)
        try:
            import os
            token = os.environ.get("GITHUB_TOKEN")
            if token:
                logging.info("Using GitHub token from environment variable")
                return token
        except Exception as e:
            logging.debug(f"Could not get token from environment: {e}")

        # No token found
        logging.warning("No GitHub token found in any source")
        return None

    def build_and_release_devmanager(self) -> bool:
        """
        Build and release DevManager using existing executable or quick build.

        Returns:
            True if successful, False otherwise
        """
        try:
            print("    🚀 Starting DevManager release process")
            logging.info("Starting DevManager release process")

            print("    🔗 Connecting to GitHub repository...")
            # Get repository
            repo = self.github.get_repo(f"{self.config['owner']}/{self.config['repos']['devmanager']}")
            print("    ✅ Repository connection established")

            # Check for existing executable first
            existing_exe = Path("dist/devmanager.exe")
            if existing_exe.exists():
                print(f"    ✅ Found existing executable: {existing_exe}")
                exe_size = existing_exe.stat().st_size / (1024 * 1024)
                print(f"    📊 Executable size: {exe_size:.1f} MB")

                # Use existing executable
                success = self.create_single_executable_release(
                    app_name="devmanager",
                    exe_path=str(existing_exe),
                    version=VERSION
                )

                if success:
                    print("    ✅ DevManager released successfully using existing executable!")
                    return True
                else:
                    print("    ⚠️  Release with existing executable failed, trying fresh build...")

            # If no existing executable or release failed, do a quick build
            print("    🔨 Building DevManager executable...")
            build_path = self._quick_build_devmanager()
            if not build_path:
                print("    ❌ Build failed")
                return False

            # Create release with built executable
            success = self.create_single_executable_release(
                app_name="devmanager",
                exe_path=str(build_path),
                version=VERSION
            )

            if success:
                print("    ✅ DevManager built and released successfully!")
                return True
            else:
                print("    ❌ Release failed")
                return False

        except Exception as e:
            print(f"    ❌ Release failed: {e}")
            logging.error(f"Error in DevManager build and release: {e}", exc_info=True)
            return False

    def build_and_release_devautomator(self) -> bool:
        """
        Build and release DevAutomator using existing executable or quick build.

        Returns:
            True if successful, False otherwise
        """
        try:
            print("    🚀 Starting DevAutomator release process")
            logging.info("Starting DevAutomator release process")

            print("    🔗 Connecting to GitHub repository...")
            # Get repository
            repo = self.github.get_repo(f"{self.config['owner']}/{self.config['repos']['devautomator']}")
            print("    ✅ Repository connection established")

            # Check for existing DevAutomator executable
            devautomator_path = Path("../css_dev_automator")
            existing_exe = devautomator_path / "dist" / "DevAutomator.exe"

            if existing_exe.exists():
                print(f"    ✅ Found existing DevAutomator executable: {existing_exe}")
                exe_size = existing_exe.stat().st_size / (1024 * 1024)
                print(f"    📊 Executable size: {exe_size:.1f} MB")

                # Use existing executable
                success = self.create_single_executable_release(
                    app_name="devautomator",
                    exe_path=str(existing_exe),
                    version=VERSION
                )

                if success:
                    print("    ✅ DevAutomator released successfully using existing executable!")
                    return True
                else:
                    print("    ⚠️  Release with existing executable failed, trying fresh build...")

            # If no existing executable or release failed, do a quick build
            print("    🔨 Building DevAutomator executable...")
            build_path = self._quick_build_devautomator()
            if not build_path:
                print("    ❌ Build failed")
                return False

            # Create release with built executable
            success = self.create_single_executable_release(
                app_name="devautomator",
                exe_path=str(build_path),
                version=VERSION
            )

            if success:
                print("    ✅ DevAutomator built and released successfully!")
                return True
            else:
                print("    ❌ Release failed")
                return False

        except Exception as e:
            print(f"    ❌ Release failed: {e}")
            logging.error(f"Error in DevAutomator build and release: {e}", exc_info=True)
            return False

    def _quick_build_devmanager(self) -> Path | None:
        """
        Quick build of DevManager using the existing spec file.

        Returns:
            Path to built executable or None if failed
        """
        try:
            print("    🔨 Quick building DevManager...")
            logging.info("Quick building DevManager...")

            # Use existing spec file for faster build
            spec_file = Path("src/specs/devmanager.spec")
            if not spec_file.exists():
                print(f"    ❌ Spec file not found: {spec_file}")
                return None

            print("    ⚙️  Running PyInstaller with existing spec...")
            print(f"    📋 Using spec file: {spec_file}")

            # Run PyInstaller with the spec file (much faster)
            cmd = [
                "pyinstaller",
                "--clean",
                "--noconfirm",
                str(spec_file),
            ]

            print("    🔄 Starting PyInstaller process...")

            import time
            start_time = time.time()

            # Run PyInstaller
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutes timeout
            )

            elapsed_total = int(time.time() - start_time)

            if result.returncode != 0:
                print(f"    ❌ PyInstaller failed after {elapsed_total}s")
                print("    📄 Error details:")
                error_lines = result.stderr.split('\n')[-5:]
                for line in error_lines:
                    if line.strip():
                        print(f"       {line}")
                logging.error(f"PyInstaller failed: {result.stderr}")
                return None
            else:
                print(f"    ✅ PyInstaller completed successfully in {elapsed_total}s")

            # Check for built executable
            exe_path = Path("dist/devmanager.exe")
            if not exe_path.exists():
                print(f"    ❌ Built executable not found: {exe_path}")
                return None

            exe_size = exe_path.stat().st_size / (1024 * 1024)
            print(f"    ✅ Executable built: {exe_size:.1f} MB")

            return exe_path

        except Exception as e:
            print(f"    ❌ Quick build error: {e}")
            logging.error(f"Error in quick build: {e}", exc_info=True)
            return None

    def _build_devmanager(self) -> Path | None:
        """
        Build DevManager using PyInstaller.

        Returns:
            Path to built package or None if failed
        """
        try:
            print("    🔨 Compiling DevManager executable...")
            logging.info("Building DevManager...")

            # Create temporary build directory
            with tempfile.TemporaryDirectory() as temp_dir:
                build_dir = Path(temp_dir) / "build"
                dist_dir = Path(temp_dir) / "dist"

                print("    ⚙️  Running PyInstaller...")
                print("    📋 Build configuration:")
                print(f"       • Target: DevManager.exe")
                print(f"       • Mode: Single file executable")
                print(f"       • Source: src/main.py")
                print(f"       • Output: {dist_dir}")

                # Run PyInstaller
                cmd = [
                    "pyinstaller",
                    "--onefile",
                    "--name",
                    "DevManager",
                    "--distpath",
                    str(dist_dir),
                    "--workpath",
                    str(build_dir),
                    "--clean",
                    "src/main.py",
                ]

                print("    🔄 Starting PyInstaller process...")
                print("       This may take 2-3 minutes, please wait...")

                # Run with real-time output
                import time
                start_time = time.time()

                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )

                # Show progress indicators
                last_update = time.time()
                while process.poll() is None:
                    current_time = time.time()
                    if current_time - last_update > 10:  # Update every 10 seconds
                        elapsed = int(current_time - start_time)
                        print(f"    ⏱️  Build in progress... ({elapsed}s elapsed)")
                        last_update = current_time
                    time.sleep(1)

                # Get final output
                stdout, _ = process.communicate()
                elapsed_total = int(time.time() - start_time)

                if process.returncode != 0:
                    print(f"    ❌ PyInstaller failed after {elapsed_total}s")
                    print("    📄 Error details:")
                    # Show last few lines of output for debugging
                    error_lines = stdout.split('\n')[-10:]
                    for line in error_lines:
                        if line.strip():
                            print(f"       {line}")
                    logging.error(f"PyInstaller failed: {stdout}")
                    return None
                else:
                    print(f"    ✅ PyInstaller completed successfully in {elapsed_total}s")

                print("    📦 Creating distribution package...")
                # Create zip package
                exe_name = f"DevManager{self.platform_info['executable_ext']}"
                exe_path = dist_dir / exe_name

                if not exe_path.exists():
                    print(f"    ❌ Built executable not found: {exe_path}")
                    logging.error(f"Built executable not found: {exe_path}")
                    return None

                print(f"    ✅ Executable found: {exe_name}")
                exe_size = exe_path.stat().st_size / (1024 * 1024)
                print(f"    📊 Executable size: {exe_size:.1f} MB")

                # Create zip file
                import zipfile

                # Ensure consistent platform naming (lowercase for compatibility)
                platform_name = self.platform_info['platform_key'].lower()
                zip_path = (
                    Path(temp_dir)
                    / f"DevManager_v{VERSION}_{platform_name}.zip"
                )

                print(f"    🗜️  Creating ZIP archive: {zip_path.name}")
                with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                    zipf.write(exe_path, exe_name)

                zip_size = zip_path.stat().st_size / (1024 * 1024)
                compression_ratio = (1 - zip_size / exe_size) * 100
                print(f"    ✅ ZIP created: {zip_size:.1f} MB (compressed {compression_ratio:.1f}%)")

                # Copy to permanent location
                final_path = Path.cwd() / "dist" / zip_path.name
                final_path.parent.mkdir(exist_ok=True)
                import shutil

                print(f"    📁 Copying to: {final_path}")
                shutil.copy2(zip_path, final_path)

                print(f"    ✅ DevManager built successfully: {final_path.name}")
                logging.info(f"DevManager built successfully: {final_path}")
                return final_path

        except Exception as e:
            print(f"    ❌ Build error: {e}")
            logging.error(f"Error building DevManager: {e}", exc_info=True)
            return None

    def _quick_build_devautomator(self) -> Path | None:
        """
        Quick build of DevAutomator using PyInstaller.

        Returns:
            Path to built executable or None if failed
        """
        try:
            print("    🔨 Quick building DevAutomator...")
            logging.info("Quick building DevAutomator...")

            # Path to DevAutomator project
            devautomator_path = Path("../css_dev_automator")
            if not devautomator_path.exists():
                print(f"    ❌ DevAutomator project not found at: {devautomator_path}")
                return None

            print("    📁 DevAutomator project found")

            # Quick PyInstaller command
            cmd = [
                "pyinstaller",
                "--onefile",
                "--name", "DevAutomator",
                "--distpath", "dist",
                "--clean",
                "--noconfirm",
                "main.py",
            ]

            print("    🔄 Starting PyInstaller process...")

            import time
            start_time = time.time()

            # Run PyInstaller from DevAutomator directory
            result = subprocess.run(
                cmd,
                cwd=str(devautomator_path),
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutes timeout
            )

            elapsed_total = int(time.time() - start_time)

            if result.returncode != 0:
                print(f"    ❌ PyInstaller failed after {elapsed_total}s")
                print("    📄 Error details:")
                error_lines = result.stderr.split('\n')[-5:]
                for line in error_lines:
                    if line.strip():
                        print(f"       {line}")
                logging.error(f"PyInstaller failed: {result.stderr}")
                return None
            else:
                print(f"    ✅ PyInstaller completed successfully in {elapsed_total}s")

            # Check for built executable
            exe_path = devautomator_path / "dist" / "DevAutomator.exe"
            if not exe_path.exists():
                print(f"    ❌ Built executable not found: {exe_path}")
                return None

            exe_size = exe_path.stat().st_size / (1024 * 1024)
            print(f"    ✅ DevAutomator executable built: {exe_size:.1f} MB")

            return exe_path

        except Exception as e:
            print(f"    ❌ Quick build error: {e}")
            logging.error(f"Error in DevAutomator quick build: {e}", exc_info=True)
            return None

    def _build_devautomator(self) -> Path | None:
        """
        Build DevAutomator using PyInstaller.

        Returns:
            Path to built package or None if failed
        """
        try:
            print("    🔨 Compiling DevAutomator executable...")
            logging.info("Building DevAutomator...")

            # Path to DevAutomator project
            devautomator_path = Path("../css_dev_automator")

            if not devautomator_path.exists():
                print(f"    ❌ DevAutomator project not found at: {devautomator_path}")
                logging.error(f"DevAutomator project not found at: {devautomator_path}")
                return None

            print("    📁 DevAutomator project found")

            # Create temporary build directory
            with tempfile.TemporaryDirectory() as temp_dir:
                build_dir = Path(temp_dir) / "build"
                dist_dir = Path(temp_dir) / "dist"

                print("    ⚙️  Running PyInstaller...")
                print("    📋 Build configuration:")
                print(f"       • Target: DevAutomator.exe")
                print(f"       • Mode: Single file executable")
                print(f"       • Source: {devautomator_path / 'main.py'}")
                print(f"       • Output: {dist_dir}")
                print("       • Excluding: torch, numpy, scipy, pandas, matplotlib, etc.")

                # Run PyInstaller from DevAutomator directory with exclusions
                cmd = [
                    "pyinstaller",
                    "--onefile",
                    "--name",
                    "DevAutomator",
                    "--distpath",
                    str(dist_dir),
                    "--workpath",
                    str(build_dir),
                    "--clean",
                    # Exclude problematic packages
                    "--exclude-module", "torch",
                    "--exclude-module", "numpy",
                    "--exclude-module", "scipy",
                    "--exclude-module", "pandas",
                    "--exclude-module", "matplotlib",
                    "--exclude-module", "tensorflow",
                    "--exclude-module", "sklearn",
                    "--exclude-module", "tkinter",
                    "--exclude-module", "jupyter",
                    "--exclude-module", "IPython",
                    "--exclude-module", "notebook",
                    str(devautomator_path / "main.py"),
                ]

                print("    🔄 Starting PyInstaller process...")
                print("       This may take 2-3 minutes, please wait...")

                # Run with real-time output
                import time
                start_time = time.time()

                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    cwd=str(devautomator_path),
                    bufsize=1,
                    universal_newlines=True
                )

                # Show progress indicators
                last_update = time.time()
                while process.poll() is None:
                    current_time = time.time()
                    if current_time - last_update > 10:  # Update every 10 seconds
                        elapsed = int(current_time - start_time)
                        print(f"    ⏱️  Build in progress... ({elapsed}s elapsed)")
                        last_update = current_time
                    time.sleep(1)

                # Get final output
                stdout, _ = process.communicate()
                elapsed_total = int(time.time() - start_time)

                if process.returncode != 0:
                    print(f"    ❌ PyInstaller failed after {elapsed_total}s")
                    print("    📄 Error details:")
                    # Show last few lines of output for debugging
                    error_lines = stdout.split('\n')[-10:]
                    for line in error_lines:
                        if line.strip():
                            print(f"       {line}")
                    logging.error(f"PyInstaller failed: {stdout}")
                    return None
                else:
                    print(f"    ✅ PyInstaller completed successfully in {elapsed_total}s")

                print("    📦 Creating distribution package...")
                # Create zip package
                exe_name = f"DevAutomator{self.platform_info['executable_ext']}"
                exe_path = dist_dir / exe_name

                if not exe_path.exists():
                    print(f"    ❌ Built executable not found: {exe_path}")
                    logging.error(f"Built executable not found: {exe_path}")
                    return None

                print(f"    ✅ Executable found: {exe_name}")
                exe_size = exe_path.stat().st_size / (1024 * 1024)
                print(f"    📊 Executable size: {exe_size:.1f} MB")

                # Create zip file
                import zipfile

                # Ensure consistent platform naming (lowercase for compatibility)
                platform_name = self.platform_info['platform_key'].lower()
                zip_path = (
                    Path(temp_dir)
                    / f"DevAutomator_v{VERSION}_{platform_name}.zip"
                )

                print(f"    🗜️  Creating ZIP archive: {zip_path.name}")
                with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                    zipf.write(exe_path, exe_name)

                zip_size = zip_path.stat().st_size / (1024 * 1024)
                compression_ratio = (1 - zip_size / exe_size) * 100
                print(f"    ✅ ZIP created: {zip_size:.1f} MB (compressed {compression_ratio:.1f}%)")

                # Copy to permanent location
                final_path = Path.cwd() / "dist" / zip_path.name
                final_path.parent.mkdir(exist_ok=True)
                import shutil

                print(f"    📁 Copying to: {final_path}")
                shutil.copy2(zip_path, final_path)

                print(f"    ✅ DevAutomator built successfully: {final_path.name}")
                logging.info(f"DevAutomator built successfully: {final_path}")
                return final_path

        except Exception as e:
            print(f"    ❌ Build error: {e}")
            logging.error(f"Error building DevAutomator: {e}", exc_info=True)
            return None

    def _test_connection(self) -> bool:
        """
        Test GitHub API connection and repository access.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            logging.info("Testing GitHub API connection...")

            # Test basic API access
            user = self.github.get_user()
            logging.info(f"Connected to GitHub as: {user.login}")

            # Test repository access
            for repo_key, repo_name in self.config['repos'].items():
                try:
                    repo = self.github.get_repo(f"{self.config['owner']}/{repo_name}")
                    logging.info(f"✅ Access confirmed for {repo_key}: {repo.full_name}")
                except GithubException as e:
                    logging.error(f"❌ Cannot access {repo_key} repository: {e}")
                    return False

            logging.info("✅ GitHub connection and repository access verified")
            return True

        except Exception as e:
            logging.error(f"❌ GitHub connection test failed: {e}")
            return False

    def check_repository_access(self, repo_key: str) -> bool:
        """
        Check access to a specific repository.

        Args:
            repo_key: Repository key ('devmanager' or 'devautomator')

        Returns:
            True if access is available
        """
        try:
            repo_name = self.config['repos'].get(repo_key)
            if not repo_name:
                logging.error(f"Unknown repository key: {repo_key}")
                return False

            repo = self.github.get_repo(f"{self.config['owner']}/{repo_name}")
            logging.info(f"Repository access confirmed: {repo.full_name}")
            return True

        except GithubException as e:
            logging.error(f"Repository access failed for {repo_key}: {e}")
            return False

    def get_latest_release_info(self, repo_key: str) -> dict:
        """
        Get latest release information for a repository.

        Args:
            repo_key: Repository key ('devmanager' or 'devautomator')

        Returns:
            Dictionary with release information
        """
        try:
            repo_name = self.config['repos'].get(repo_key)
            if not repo_name:
                return {"error": f"Unknown repository key: {repo_key}"}

            repo = self.github.get_repo(f"{self.config['owner']}/{repo_name}")

            try:
                latest_release = repo.get_latest_release()
                return {
                    "tag_name": latest_release.tag_name,
                    "name": latest_release.title,
                    "published_at": latest_release.published_at.isoformat(),
                    "assets": [
                        {
                            "name": asset.name,
                            "download_url": asset.browser_download_url,
                            "size": asset.size
                        }
                        for asset in latest_release.get_assets()
                    ]
                }
            except GithubException:
                return {"error": "No releases found"}

        except Exception as e:
            return {"error": str(e)}

    def create_single_executable_release(self, app_name: str, exe_path: str, version: str = None) -> bool:
        """
        Create a GitHub release for a single executable.

        Args:
            app_name: Application name ('devmanager' or 'devautomator')
            exe_path: Path to the executable file
            version: Version string (defaults to current VERSION)

        Returns:
            True if successful, False otherwise
        """
        try:
            if version is None:
                version = VERSION

            print(f"🚀 Creating single executable release for {app_name.title()}")

            # Validate inputs
            exe_file = Path(exe_path)
            if not exe_file.exists():
                print(f"❌ Executable not found: {exe_path}")
                return False

            repo_name = self.config['repos'].get(app_name)
            if not repo_name:
                print(f"❌ Unknown application: {app_name}")
                return False

            # Get repository
            repo = self.github.get_repo(f"{self.config['owner']}/{repo_name}")
            print(f"📋 Repository: {repo.full_name}")

            # Create ZIP package
            print("📦 Creating ZIP package...")
            with tempfile.TemporaryDirectory() as temp_dir:
                # Ensure consistent platform naming (lowercase for compatibility)
                platform_name = self.platform_info['platform_key'].lower()
                asset_name = self.config['asset_naming'][app_name].format(
                    version=version,
                    platform=platform_name
                )

                # Log the asset name being created for debugging
                logging.info(f"Creating asset with name: {asset_name}")
                zip_path = Path(temp_dir) / asset_name

                if not self._create_single_exe_package(exe_file, zip_path, app_name, version):
                    return False

                # Create release
                release_tag = f"v{version}"
                release_name = f"{app_name.title()} v{version}"
                release_notes = self._generate_single_exe_release_notes(app_name, version, exe_file)

                try:
                    # Check if release already exists
                    release = repo.get_release(release_tag)
                    print(f"🔄 Release {release_tag} already exists, updating...")
                except GithubException:
                    # Create new release
                    print(f"🆕 Creating new release: {release_tag}")
                    release = repo.create_git_release(
                        tag=release_tag,
                        name=release_name,
                        message=release_notes,
                        draft=False,
                        prerelease=False,
                    )
                    print(f"✅ Created release: {release.html_url}")

                # Remove existing asset if it exists
                print("🔍 Checking for existing assets...")
                for asset in release.get_assets():
                    if asset.name == asset_name:
                        print(f"🗑️ Removing existing asset: {asset.name}")
                        asset.delete_asset()
                        break

                # Upload new asset
                print(f"📤 Uploading asset: {asset_name}")
                file_size_mb = zip_path.stat().st_size / (1024 * 1024)
                print(f"📊 File size: {file_size_mb:.1f} MB")

                asset = release.upload_asset(
                    path=str(zip_path),
                    name=asset_name,
                    content_type="application/zip"
                )

                print(f"✅ Asset uploaded: {asset.browser_download_url}")
                print(f"🌐 Release URL: {release.html_url}")

            return True

        except Exception as e:
            print(f"❌ Failed to create single executable release: {e}")
            logging.error(f"Single executable release failed: {e}", exc_info=True)
            return False

    def _create_single_exe_package(self, exe_path: Path, zip_path: Path, app_name: str, version: str) -> bool:
        """Create a ZIP package containing the single executable and metadata."""
        try:
            import zipfile
            from datetime import datetime

            print(f"📦 Creating ZIP package: {zip_path.name}")

            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add the executable
                zipf.write(exe_path, exe_path.name)

                # Create and add README
                readme_content = f"""# {app_name.title()} v{version}

## Single Executable Release

This package contains a single executable file for {app_name.title()} v{version}.

### Installation
1. Extract the ZIP file
2. Run the executable directly - no installation required
3. For DevManager: Can be run in normal mode (double-click) or with token
4. For DevAutomator: Requires token parameter from DevManager

### File Information
- **Executable**: {exe_path.name}
- **Version**: {version}
- **Platform**: Windows 64-bit
- **Build Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Size**: {exe_path.stat().st_size / (1024*1024):.1f} MB

### Features
- Single executable - no dependencies required
- All resources embedded
- Cross-platform compatible
- Optimized for performance

### Support
For issues and documentation, visit:
https://github.com/{self.config['owner']}/{self.config['repos'][app_name]}
"""

                # Add README to ZIP
                zipf.writestr("README.md", readme_content)

            print(f"✅ ZIP package created: {zip_path}")
            return True

        except Exception as e:
            print(f"❌ Failed to create ZIP package: {e}")
            return False

    def _generate_single_exe_release_notes(self, app_name: str, version: str, exe_path: Path) -> str:
        """Generate release notes for single executable release."""
        from datetime import datetime

        return f"""# {app_name.title()} v{version} - Single Executable Release

## 🎉 New Features
- **Single Executable**: No more multiple files and folders - just one .exe file!
- **Embedded Resources**: All templates, configs, and assets are embedded
- **Simplified Deployment**: Easy installation and distribution
- **Optimized Performance**: Faster startup and reduced disk footprint

## 📦 What's Included
- Single executable file ({exe_path.stat().st_size / (1024*1024):.1f} MB)
- All functionality preserved from previous versions
- Cross-environment compatibility (development and production)

## 🔧 Technical Improvements
- PyInstaller onefile mode implementation
- Resource path handling for embedded files
- Optimized dependency management
- Reduced package size

## 📥 Installation
1. Download the ZIP file from the assets below
2. Extract the executable
3. Run directly - no installation required!

## 🔗 Related Projects
- DevManager: https://github.com/{self.config['owner']}/css_dev_manager
- DevAutomator: https://github.com/{self.config['owner']}/css_dev_automator

---
**Build Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Platform**: Windows 64-bit
**Version**: {version}
"""

    def get_repository(self, repo_name: str):
        """
        Get a GitHub repository object.

        Args:
            repo_name: Full repository name (owner/repo)

        Returns:
            GitHub repository object
        """
        return self.github.get_repo(repo_name)

    def get_releases(self, repo_name: str) -> list:
        """
        Get all releases for a repository.

        Args:
            repo_name: Full repository name (owner/repo)

        Returns:
            List of release objects
        """
        try:
            repo = self.github.get_repo(repo_name)
            return list(repo.get_releases())
        except Exception as e:
            logging.error(f"Error getting releases for {repo_name}: {e}")
            return []

    def get_latest_version(self, repo_name: str) -> str | None:
        """
        Get the latest version tag for a repository.

        Args:
            repo_name: Full repository name (owner/repo)

        Returns:
            Latest version string or None if no releases
        """
        try:
            repo = self.github.get_repo(repo_name)
            latest_release = repo.get_latest_release()
            return latest_release.tag_name
        except Exception as e:
            logging.debug(f"No releases found for {repo_name}: {e}")
            return None

    def _generate_release_notes(self, app_name: str, version: str) -> str:
        """
        Generate release notes for the application.

        Args:
            app_name: Name of the application
            version: Version being released

        Returns:
            Release notes string
        """
        return f"""# {app_name} {version}

## What's New
- Bug fixes and improvements
- Updated dependencies
- Performance optimizations

## Installation
Download the appropriate package for your platform and extract it to your desired location.

## System Requirements
- Windows 10 or later
- macOS 10.15 or later
- Linux (Ubuntu 20.04+ or equivalent)

## Support
For issues and support, please visit our GitHub repository: {self.config['urls'][app_name.lower().replace('dev', 'dev')]}
"""
