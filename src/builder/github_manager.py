"""
GitHub API integration for managing releases and assets.
"""

import logging
from pathlib import Path

from github import Github, GithubException
from github.GitRelease import GitRelease

from ..common.constants import GITHUB_REPO_NAME, GITHUB_REPO_OWNER


class GitHubManager:
    """
    Manages GitHub releases and asset uploads for DevAutomator.
    """

    def __init__(
        self,
        token: str,
        repo_owner: str = GITHUB_REPO_OWNER,
        repo_name: str = GITHUB_REPO_NAME,
    ):
        """
        Initialize the GitHub manager.

        Args:
            token: GitHub personal access token
            repo_owner: Repository owner/organization
            repo_name: Repository name
        """
        self.token = token
        self.repo_owner = repo_owner
        self.repo_name = repo_name

        try:
            self.github = Github(token)
            self.repo = self.github.get_repo(f"{repo_owner}/{repo_name}")
            logging.info(f"GitHub manager initialized for {repo_owner}/{repo_name}")
        except GithubException as e:
            logging.error(f"Failed to initialize GitHub manager: {e}")
            raise

    def create_release(
        self,
        version: str,
        release_notes: str = "",
        prerelease: bool = False,
        draft: bool = False,
    ) -> GitRelease | None:
        """
        Create a new GitHub release.

        Args:
            version: Release version (will be used as tag)
            release_notes: Release notes/description
            prerelease: Whether this is a prerelease
            draft: Whether to create as draft

        Returns:
            GitRelease object or None if failed
        """
        try:
            tag_name = f"v{version}" if not version.startswith("v") else version
            release_name = f"DevAutomator {version}"

            logging.info(f"Creating GitHub release: {tag_name}")

            # Check if release already exists
            try:
                existing_release = self.repo.get_release(tag_name)
                logging.warning(f"Release {tag_name} already exists")
                return existing_release
            except GithubException:
                # Release doesn't exist, continue with creation
                pass

            # Create the release
            release = self.repo.create_git_release(
                tag=tag_name,
                name=release_name,
                message=release_notes or f"Release {version}",
                draft=draft,
                prerelease=prerelease,
            )

            logging.info(f"Release created successfully: {release.html_url}")
            return release

        except GithubException as e:
            logging.error(f"Failed to create release: {e}")
            return None

    def upload_release_asset(
        self,
        release: GitRelease,
        asset_path: Path,
        platform: str,
        asset_name: str | None = None,
    ) -> bool:
        """
        Upload an asset to a GitHub release.

        Args:
            release: GitRelease object
            asset_path: Path to the asset file
            platform: Platform identifier
            asset_name: Custom asset name (optional)

        Returns:
            True if successful, False otherwise
        """
        try:
            if not asset_path.exists():
                logging.error(f"Asset file not found: {asset_path}")
                return False

            # Determine asset name
            if asset_name is None:
                asset_name = asset_path.name

            logging.info(f"Uploading asset: {asset_name} ({platform})")

            # Check if asset already exists
            for asset in release.get_assets():
                if asset.name == asset_name:
                    logging.warning(f"Asset {asset_name} already exists, deleting...")
                    asset.delete_asset()
                    break

            # Upload the asset
            with open(asset_path, "rb") as f:
                asset = release.upload_asset(
                    path=str(asset_path),
                    name=asset_name,
                    content_type="application/zip",
                )

            logging.info(f"Asset uploaded successfully: {asset.browser_download_url}")
            return True

        except GithubException as e:
            logging.error(f"Failed to upload asset {asset_path}: {e}")
            return False
        except Exception as e:
            logging.error(
                f"Unexpected error uploading asset {asset_path}: {e}", exc_info=True
            )
            return False

    def get_release(self, version: str) -> GitRelease | None:
        """
        Get a specific release by version.

        Args:
            version: Release version

        Returns:
            GitRelease object or None if not found
        """
        try:
            tag_name = f"v{version}" if not version.startswith("v") else version
            return self.repo.get_release(tag_name)
        except GithubException:
            return None

    def get_latest_release(
        self, include_prereleases: bool = False
    ) -> GitRelease | None:
        """
        Get the latest release.

        Args:
            include_prereleases: Whether to include prereleases

        Returns:
            GitRelease object or None if not found
        """
        try:
            if include_prereleases:
                # Get all releases and find the latest
                releases = list(self.repo.get_releases())
                if releases:
                    return releases[0]
                return None
            else:
                return self.repo.get_latest_release()
        except GithubException:
            return None

    def get_release_download_urls(self, version: str) -> dict[str, str]:
        """
        Get download URLs for all assets in a release.

        Args:
            version: Release version

        Returns:
            Dictionary mapping platform to download URL
        """
        try:
            release = self.get_release(version)
            if not release:
                return {}

            download_urls = {}
            for asset in release.get_assets():
                # Extract platform from asset name
                asset_name = asset.name.lower()

                if "windows" in asset_name or "win" in asset_name:
                    platform = "windows"
                elif "macos" in asset_name or "darwin" in asset_name:
                    platform = "macos"
                elif "linux" in asset_name:
                    platform = "linux"
                else:
                    # Try to extract platform from filename pattern
                    parts = asset_name.split("_")
                    if len(parts) >= 3:
                        platform = parts[-1].replace(".zip", "")
                    else:
                        continue

                download_urls[platform] = asset.browser_download_url

            return download_urls

        except GithubException as e:
            logging.error(f"Failed to get download URLs for version {version}: {e}")
            return {}

    def delete_release(self, version: str) -> bool:
        """
        Delete a release.

        Args:
            version: Release version

        Returns:
            True if successful, False otherwise
        """
        try:
            release = self.get_release(version)
            if not release:
                logging.warning(f"Release {version} not found")
                return False

            release.delete_release()
            logging.info(f"Release {version} deleted successfully")
            return True

        except GithubException as e:
            logging.error(f"Failed to delete release {version}: {e}")
            return False

    def list_releases(self, limit: int = 10) -> list[dict[str, any]]:
        """
        List recent releases.

        Args:
            limit: Maximum number of releases to return

        Returns:
            List of release information dictionaries
        """
        try:
            releases = []
            for release in self.repo.get_releases()[:limit]:
                releases.append(
                    {
                        "tag_name": release.tag_name,
                        "name": release.title,
                        "published_at": release.published_at,
                        "prerelease": release.prerelease,
                        "draft": release.draft,
                        "html_url": release.html_url,
                        "assets_count": release.get_assets().totalCount,
                    }
                )

            return releases

        except GithubException as e:
            logging.error(f"Failed to list releases: {e}")
            return []

    def validate_token(self) -> bool:
        """
        Validate the GitHub token and repository access.

        Returns:
            True if valid, False otherwise
        """
        try:
            # Try to access repository information
            repo_info = self.repo.get_repo()
            logging.info(f"Token validation successful for {repo_info.full_name}")
            return True

        except GithubException as e:
            logging.error(f"Token validation failed: {e}")
            return False

    def get_repository_info(self) -> dict[str, any]:
        """
        Get repository information.

        Returns:
            Dictionary with repository information
        """
        try:
            repo = self.repo
            return {
                "name": repo.name,
                "full_name": repo.full_name,
                "description": repo.description,
                "html_url": repo.html_url,
                "clone_url": repo.clone_url,
                "default_branch": repo.default_branch,
                "private": repo.private,
                "stars": repo.stargazers_count,
                "forks": repo.forks_count,
                "issues": repo.open_issues_count,
                "created_at": repo.created_at,
                "updated_at": repo.updated_at,
            }

        except GithubException as e:
            logging.error(f"Failed to get repository info: {e}")
            return {}

    def create_release_with_assets(
        self,
        version: str,
        assets: dict[str, Path],
        release_notes: str = "",
        prerelease: bool = False,
    ) -> bool:
        """
        Create a release and upload all assets in one operation.

        Args:
            version: Release version
            assets: Dictionary mapping platform to asset path
            release_notes: Release notes
            prerelease: Whether this is a prerelease

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create the release
            release = self.create_release(version, release_notes, prerelease)
            if not release:
                return False

            # Upload all assets
            success = True
            for platform, asset_path in assets.items():
                if not self.upload_release_asset(release, asset_path, platform):
                    success = False

            return success

        except Exception as e:
            logging.error(f"Failed to create release with assets: {e}", exc_info=True)
            return False
