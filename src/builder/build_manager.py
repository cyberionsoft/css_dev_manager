"""
Main build manager for orchestrating DevAutomator builds and releases.
"""

import logging
import sys
from pathlib import Path

import click

from ..common.constants import BUILD_DIR, DIST_DIR, SUPPORTED_PLATFORMS
from ..common.utils import ensure_directory, safe_remove_directory
from ..common.version import Version
from .github_manager import GitHubManager
from .manifest_manager import ManifestManager
from .packager import Packager


class BuildManager:
    """
    Orchestrates the complete build, package, and release process for DevAutomator.
    """

    def __init__(self, devautomator_path: Path, github_token: str | None = None):
        """
        Initialize the build manager.

        Args:
            devautomator_path: Path to the DevAutomator project
            github_token: GitHub personal access token
        """
        self.devautomator_path = Path(devautomator_path)
        self.build_dir = BUILD_DIR
        self.dist_dir = DIST_DIR

        # Initialize components
        self.packager = Packager(self.devautomator_path)
        self.github_manager = GitHubManager(github_token) if github_token else None
        self.manifest_manager = ManifestManager()

        # Ensure directories exist
        ensure_directory(self.build_dir)
        ensure_directory(self.dist_dir)

        logging.info(f"BuildManager initialized for: {self.devautomator_path}")

    def build_all_platforms(
        self, version: str, clean: bool = True, platforms: list[str] | None = None
    ) -> dict[str, Path]:
        """
        Build DevAutomator for all specified platforms.

        Args:
            version: Version string for the build
            clean: Whether to clean build directories first
            platforms: List of platforms to build for (default: all supported)

        Returns:
            Dictionary mapping platform names to build archive paths
        """
        if platforms is None:
            platforms = list(SUPPORTED_PLATFORMS.keys())

        logging.info(f"Starting build for version {version}, platforms: {platforms}")

        if clean:
            self._clean_build_directories()

        build_results = {}

        for platform in platforms:
            if platform not in SUPPORTED_PLATFORMS:
                logging.warning(f"Unsupported platform: {platform}")
                continue

            try:
                logging.info(f"Building for platform: {platform}")
                archive_path = self.packager.build_for_platform(platform, version)

                if archive_path and archive_path.exists():
                    build_results[platform] = archive_path
                    logging.info(f"Build successful for {platform}: {archive_path}")
                else:
                    logging.error(f"Build failed for platform: {platform}")

            except Exception as e:
                logging.error(
                    f"Build error for platform {platform}: {e}", exc_info=True
                )

        logging.info(f"Build completed. Successful builds: {len(build_results)}")
        return build_results

    def create_release(
        self,
        version: str,
        build_results: dict[str, Path],
        release_notes: str = "",
        prerelease: bool = False,
    ) -> bool:
        """
        Create a GitHub release and upload build artifacts.

        Args:
            version: Release version
            build_results: Dictionary of platform -> archive path
            release_notes: Release notes text
            prerelease: Whether this is a prerelease

        Returns:
            True if successful, False otherwise
        """
        if not self.github_manager:
            logging.error("GitHub manager not initialized (missing token)")
            return False

        if not build_results:
            logging.error("No build results to release")
            return False

        try:
            logging.info(f"Creating GitHub release for version {version}")

            # Create the release
            release = self.github_manager.create_release(
                version, release_notes, prerelease
            )

            if not release:
                return False

            # Upload build artifacts
            upload_success = True
            for platform, archive_path in build_results.items():
                success = self.github_manager.upload_release_asset(
                    release, archive_path, platform
                )
                if not success:
                    upload_success = False

            if upload_success:
                logging.info("All artifacts uploaded successfully")
            else:
                logging.warning("Some artifacts failed to upload")

            return upload_success

        except Exception as e:
            logging.error(f"Failed to create release: {e}", exc_info=True)
            return False

    def update_manifest(
        self, version: str, build_results: dict[str, Path], release_notes: str = ""
    ) -> bool:
        """
        Update the version manifest with new release information.

        Args:
            version: Release version
            build_results: Dictionary of platform -> archive path
            release_notes: Release notes

        Returns:
            True if successful, False otherwise
        """
        try:
            logging.info("Updating version manifest")

            # Get download URLs from GitHub (if available)
            download_urls = {}
            if self.github_manager:
                download_urls = self.github_manager.get_release_download_urls(version)

            # Update manifest
            success = self.manifest_manager.update_devautomator_version(
                version, build_results, download_urls, release_notes
            )

            if success:
                logging.info("Manifest updated successfully")
            else:
                logging.error("Failed to update manifest")

            return success

        except Exception as e:
            logging.error(f"Failed to update manifest: {e}", exc_info=True)
            return False

    def full_release_process(
        self,
        version: str,
        release_notes: str = "",
        platforms: list[str] | None = None,
        prerelease: bool = False,
        clean: bool = True,
    ) -> bool:
        """
        Execute the complete release process: build, release, and manifest update.

        Args:
            version: Release version
            release_notes: Release notes
            platforms: Platforms to build for
            prerelease: Whether this is a prerelease
            clean: Whether to clean build directories

        Returns:
            True if successful, False otherwise
        """
        try:
            logging.info(f"Starting full release process for version {version}")

            # Validate version
            try:
                Version(version)
            except Exception as e:
                logging.error(f"Invalid version string '{version}': {e}")
                return False

            # Step 1: Build for all platforms
            build_results = self.build_all_platforms(version, clean, platforms)
            if not build_results:
                logging.error("No successful builds, aborting release")
                return False

            # Step 2: Create GitHub release
            if self.github_manager:
                release_success = self.create_release(
                    version, build_results, release_notes, prerelease
                )
                if not release_success:
                    logging.error("GitHub release failed, aborting")
                    return False
            else:
                logging.warning("Skipping GitHub release (no token provided)")

            # Step 3: Update manifest
            manifest_success = self.update_manifest(
                version, build_results, release_notes
            )
            if not manifest_success:
                logging.error("Manifest update failed")
                return False

            logging.info(
                f"Full release process completed successfully for version {version}"
            )
            return True

        except Exception as e:
            logging.error(f"Full release process failed: {e}", exc_info=True)
            return False

    def _clean_build_directories(self) -> None:
        """Clean build and dist directories."""
        logging.info("Cleaning build directories")

        if self.build_dir.exists():
            safe_remove_directory(self.build_dir)

        if self.dist_dir.exists():
            safe_remove_directory(self.dist_dir)

        ensure_directory(self.build_dir)
        ensure_directory(self.dist_dir)


@click.command()
@click.option(
    "--devautomator-path",
    "-p",
    required=True,
    type=click.Path(exists=True),
    help="Path to DevAutomator project directory",
)
@click.option("--version", "-v", required=True, help="Version to build and release")
@click.option(
    "--github-token",
    "-t",
    envvar="GITHUB_TOKEN",
    help="GitHub personal access token (or set GITHUB_TOKEN env var)",
)
@click.option("--release-notes", "-n", default="", help="Release notes")
@click.option(
    "--platforms",
    "-pl",
    multiple=True,
    help="Platforms to build for (default: all supported)",
)
@click.option("--prerelease", is_flag=True, help="Mark as prerelease")
@click.option("--no-clean", is_flag=True, help="Skip cleaning build directories")
@click.option("--build-only", is_flag=True, help="Only build, do not create release")
@click.option("--debug", is_flag=True, help="Enable debug logging")
def main(
    devautomator_path: str,
    version: str,
    github_token: str | None,
    release_notes: str,
    platforms: tuple,
    prerelease: bool,
    no_clean: bool,
    build_only: bool,
    debug: bool,
) -> None:
    """
    DevManager build tool for creating DevAutomator releases.
    """
    # Set up logging
    log_level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler("build.log")],
    )

    try:
        # Initialize build manager
        build_manager = BuildManager(Path(devautomator_path), github_token)

        # Convert platforms tuple to list
        platform_list = list(platforms) if platforms else None

        if build_only:
            # Only build, don't create release
            build_results = build_manager.build_all_platforms(
                version, not no_clean, platform_list
            )

            if build_results:
                click.echo(
                    f"Build completed successfully for {len(build_results)} platforms"
                )
                for platform, path in build_results.items():
                    click.echo(f"  {platform}: {path}")
            else:
                click.echo("Build failed", err=True)
                sys.exit(1)
        else:
            # Full release process
            success = build_manager.full_release_process(
                version, release_notes, platform_list, prerelease, not no_clean
            )

            if success:
                click.echo(f"Release {version} completed successfully!")
            else:
                click.echo("Release process failed", err=True)
                sys.exit(1)

    except Exception as e:
        logging.error(f"Build process failed: {e}", exc_info=True)
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
