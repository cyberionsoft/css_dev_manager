"""
Version manifest management for DevManager.
"""

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..common.constants import GITHUB_REPO_NAME, GITHUB_REPO_OWNER
from ..common.utils import calculate_checksum, load_json_file, save_json_file
from ..common.version import Version


class ManifestManager:
    """
    Manages the version manifest file that contains information about
    available versions of DevAutomator and DevManager.
    """

    def __init__(self, manifest_path: Path | None = None):
        """
        Initialize the manifest manager.

        Args:
            manifest_path: Path to the manifest file (default: versions.json)
        """
        self.manifest_path = manifest_path or Path("versions.json")
        self.manifest_data = self._load_manifest()

        logging.info(f"ManifestManager initialized with: {self.manifest_path}")

    def _load_manifest(self) -> dict[str, Any]:
        """
        Load the manifest file or create a default one.

        Returns:
            Manifest data dictionary
        """
        if self.manifest_path.exists():
            data = load_json_file(self.manifest_path)
            if data:
                logging.info("Loaded existing manifest file")
                return data

        # Create default manifest
        logging.info("Creating default manifest")
        return self._create_default_manifest()

    def _create_default_manifest(self) -> dict[str, Any]:
        """
        Create a default manifest structure.

        Returns:
            Default manifest dictionary
        """
        return {
            "schema_version": "1.0",
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "repository": {
                "owner": GITHUB_REPO_OWNER,
                "name": GITHUB_REPO_NAME,
                "url": f"https://github.com/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}",
            },
            "devautomator": {"latest_version": None, "release_notes": "", "builds": {}},
            "devmanager": {
                "latest_version": "0.1.4",
                "release_notes": "Fixed fastexcel dependency and console window issues",
                "builds": {},
            },
        }

    def update_devautomator_version(
        self,
        version: str,
        build_results: dict[str, Path],
        download_urls: dict[str, str] | None = None,
        release_notes: str = "",
    ) -> bool:
        """
        Update DevAutomator version information in the manifest.

        Args:
            version: New version string
            build_results: Dictionary mapping platform to build archive path
            download_urls: Dictionary mapping platform to download URL
            release_notes: Release notes for this version

        Returns:
            True if successful, False otherwise
        """
        try:
            logging.info(f"Updating DevAutomator version to {version}")

            # Validate version
            Version(version)

            # Update basic version info
            self.manifest_data["devautomator"]["latest_version"] = version
            self.manifest_data["devautomator"]["release_notes"] = release_notes
            self.manifest_data["last_updated"] = datetime.now(timezone.utc).isoformat()

            # Update build information
            builds = {}
            for platform, archive_path in build_results.items():
                build_info = self._create_build_info(
                    archive_path, platform, version, download_urls
                )
                if build_info:
                    builds[platform] = build_info

            self.manifest_data["devautomator"]["builds"] = builds

            # Save the manifest
            return self._save_manifest()

        except Exception as e:
            logging.error(f"Failed to update DevAutomator version: {e}", exc_info=True)
            return False

    def update_devmanager_version(
        self,
        version: str,
        build_results: dict[str, Path],
        download_urls: dict[str, str] | None = None,
        release_notes: str = "",
    ) -> bool:
        """
        Update DevManager version information in the manifest.

        Args:
            version: New version string
            build_results: Dictionary mapping platform to build archive path
            download_urls: Dictionary mapping platform to download URL
            release_notes: Release notes for this version

        Returns:
            True if successful, False otherwise
        """
        try:
            logging.info(f"Updating DevManager version to {version}")

            # Validate version
            Version(version)

            # Update basic version info
            self.manifest_data["devmanager"]["latest_version"] = version
            self.manifest_data["devmanager"]["release_notes"] = release_notes
            self.manifest_data["last_updated"] = datetime.now(timezone.utc).isoformat()

            # Update build information
            builds = {}
            for platform, archive_path in build_results.items():
                build_info = self._create_build_info(
                    archive_path, platform, version, download_urls
                )
                if build_info:
                    builds[platform] = build_info

            self.manifest_data["devmanager"]["builds"] = builds

            # Save the manifest
            return self._save_manifest()

        except Exception as e:
            logging.error(f"Failed to update DevManager version: {e}", exc_info=True)
            return False

    def _create_build_info(
        self,
        archive_path: Path,
        platform: str,
        version: str,
        download_urls: dict[str, str] | None = None,
    ) -> dict[str, Any] | None:
        """
        Create build information for a platform.

        Args:
            archive_path: Path to the build archive
            platform: Platform identifier
            version: Version string
            download_urls: Optional download URLs

        Returns:
            Build information dictionary or None if failed
        """
        try:
            if not archive_path.exists():
                logging.error(f"Archive not found: {archive_path}")
                return None

            # Calculate file information
            file_size = archive_path.stat().st_size
            checksum = calculate_checksum(archive_path)

            # Determine download URL
            download_url = ""
            if download_urls and platform in download_urls:
                download_url = download_urls[platform]
            else:
                # Construct GitHub release URL
                filename = archive_path.name
                download_url = (
                    f"https://github.com/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/"
                    f"releases/download/v{version}/{filename}"
                )

            return {
                "version": version,
                "filename": archive_path.name,
                "size": file_size,
                "checksum": checksum,
                "download_url": download_url,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logging.error(f"Failed to create build info for {platform}: {e}")
            return None

    def get_latest_version(self, app: str) -> str | None:
        """
        Get the latest version for an application.

        Args:
            app: Application name ('devautomator' or 'devmanager')

        Returns:
            Latest version string or None if not found
        """
        if app in self.manifest_data:
            return self.manifest_data[app].get("latest_version")
        return None

    def get_build_info(self, app: str, platform: str) -> dict[str, Any] | None:
        """
        Get build information for a specific app and platform.

        Args:
            app: Application name
            platform: Platform identifier

        Returns:
            Build information dictionary or None if not found
        """
        if app in self.manifest_data:
            builds = self.manifest_data[app].get("builds", {})
            return builds.get(platform)
        return None

    def get_all_builds(self, app: str) -> dict[str, Any]:
        """
        Get all build information for an application.

        Args:
            app: Application name

        Returns:
            Dictionary of all builds
        """
        if app in self.manifest_data:
            return self.manifest_data[app].get("builds", {})
        return {}

    def add_version_history(
        self, app: str, version: str, release_notes: str = ""
    ) -> bool:
        """
        Add a version to the history (for tracking previous versions).

        Args:
            app: Application name
            version: Version string
            release_notes: Release notes

        Returns:
            True if successful, False otherwise
        """
        try:
            if app not in self.manifest_data:
                return False

            # Initialize history if it doesn't exist
            if "version_history" not in self.manifest_data[app]:
                self.manifest_data[app]["version_history"] = []

            # Add version to history
            version_entry = {
                "version": version,
                "release_notes": release_notes,
                "released_at": datetime.now(timezone.utc).isoformat(),
            }

            # Check if version already exists in history
            history = self.manifest_data[app]["version_history"]
            for entry in history:
                if entry["version"] == version:
                    # Update existing entry
                    entry.update(version_entry)
                    return self._save_manifest()

            # Add new entry
            history.append(version_entry)

            # Sort by version (newest first)
            history.sort(key=lambda x: Version(x["version"]), reverse=True)

            return self._save_manifest()

        except Exception as e:
            logging.error(f"Failed to add version history: {e}", exc_info=True)
            return False

    def validate_manifest(self) -> bool:
        """
        Validate the manifest structure and data.

        Returns:
            True if valid, False otherwise
        """
        try:
            required_fields = ["schema_version", "last_updated", "repository"]
            for field in required_fields:
                if field not in self.manifest_data:
                    logging.error(f"Missing required field: {field}")
                    return False

            # Validate applications
            for app in ["devautomator", "devmanager"]:
                if app in self.manifest_data:
                    app_data = self.manifest_data[app]

                    # Check version format if present
                    if "latest_version" in app_data and app_data["latest_version"]:
                        try:
                            Version(app_data["latest_version"])
                        except Exception:
                            logging.error(f"Invalid version format for {app}")
                            return False

                    # Validate builds
                    builds = app_data.get("builds", {})
                    for platform, build_info in builds.items():
                        required_build_fields = [
                            "version",
                            "size",
                            "checksum",
                            "download_url",
                        ]
                        for field in required_build_fields:
                            if field not in build_info:
                                logging.error(
                                    f"Missing build field {field} for {app}/{platform}"
                                )
                                return False

            logging.info("Manifest validation passed")
            return True

        except Exception as e:
            logging.error(f"Manifest validation failed: {e}", exc_info=True)
            return False

    def _save_manifest(self) -> bool:
        """
        Save the manifest to file.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Update last_updated timestamp
            self.manifest_data["last_updated"] = datetime.now(timezone.utc).isoformat()

            # Save to file
            success = save_json_file(self.manifest_path, self.manifest_data, indent=2)

            if success:
                logging.info(f"Manifest saved to: {self.manifest_path}")
            else:
                logging.error("Failed to save manifest")

            return success

        except Exception as e:
            logging.error(f"Failed to save manifest: {e}", exc_info=True)
            return False

    def get_manifest_data(self) -> dict[str, Any]:
        """
        Get the complete manifest data.

        Returns:
            Manifest data dictionary
        """
        return self.manifest_data.copy()

    def reload_manifest(self) -> bool:
        """
        Reload the manifest from file.

        Returns:
            True if successful, False otherwise
        """
        try:
            self.manifest_data = self._load_manifest()
            logging.info("Manifest reloaded successfully")
            return True
        except Exception as e:
            logging.error(f"Failed to reload manifest: {e}", exc_info=True)
            return False
