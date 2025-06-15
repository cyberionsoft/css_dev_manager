"""
Version handling utilities for DevManager.
"""

from typing import Union

from packaging.version import InvalidVersion
from packaging.version import Version as PackagingVersion


class Version:
    """
    Semantic version handling with comparison support.

    Supports standard semantic versioning (MAJOR.MINOR.PATCH) with optional
    pre-release and build metadata.
    """

    def __init__(self, version_string: str):
        """
        Initialize a Version object.

        Args:
            version_string: Version string in semantic version format

        Raises:
            InvalidVersion: If the version string is not valid
        """
        self.version_string = version_string.strip()
        try:
            self._version = PackagingVersion(self.version_string)
        except InvalidVersion as e:
            raise InvalidVersion(f"Invalid version string '{version_string}': {e}")

    @property
    def major(self) -> int:
        """Get the major version number."""
        return self._version.major

    @property
    def minor(self) -> int:
        """Get the minor version number."""
        return self._version.minor

    @property
    def micro(self) -> int:
        """Get the patch/micro version number."""
        return self._version.micro

    @property
    def patch(self) -> int:
        """Alias for micro (patch version number)."""
        return self.micro

    @property
    def is_prerelease(self) -> bool:
        """Check if this is a pre-release version."""
        return self._version.is_prerelease

    @property
    def is_devrelease(self) -> bool:
        """Check if this is a development release."""
        return self._version.is_devrelease

    def __str__(self) -> str:
        """Return the version string."""
        return self.version_string

    def __repr__(self) -> str:
        """Return a detailed representation."""
        return f"Version('{self.version_string}')"

    def __eq__(self, other: Union["Version", str]) -> bool:
        """Check if versions are equal."""
        if isinstance(other, str):
            other = Version(other)
        return self._version == other._version

    def __lt__(self, other: Union["Version", str]) -> bool:
        """Check if this version is less than another."""
        if isinstance(other, str):
            other = Version(other)
        return self._version < other._version

    def __le__(self, other: Union["Version", str]) -> bool:
        """Check if this version is less than or equal to another."""
        if isinstance(other, str):
            other = Version(other)
        return self._version <= other._version

    def __gt__(self, other: Union["Version", str]) -> bool:
        """Check if this version is greater than another."""
        if isinstance(other, str):
            other = Version(other)
        return self._version > other._version

    def __ge__(self, other: Union["Version", str]) -> bool:
        """Check if this version is greater than or equal to another."""
        if isinstance(other, str):
            other = Version(other)
        return self._version >= other._version

    def __ne__(self, other: Union["Version", str]) -> bool:
        """Check if versions are not equal."""
        return not self.__eq__(other)

    def __hash__(self) -> int:
        """Return hash of the version."""
        return hash(self._version)

    @classmethod
    def parse(cls, version_string: str) -> "Version":
        """
        Parse a version string and return a Version object.

        Args:
            version_string: Version string to parse

        Returns:
            Version object

        Raises:
            InvalidVersion: If the version string is invalid
        """
        return cls(version_string)

    def bump_major(self) -> "Version":
        """Return a new Version with the major version incremented."""
        return Version(f"{self.major + 1}.0.0")

    def bump_minor(self) -> "Version":
        """Return a new Version with the minor version incremented."""
        return Version(f"{self.major}.{self.minor + 1}.0")

    def bump_patch(self) -> "Version":
        """Return a new Version with the patch version incremented."""
        return Version(f"{self.major}.{self.minor}.{self.patch + 1}")

    def to_tuple(self) -> tuple[int, int, int]:
        """Return version as a tuple of (major, minor, patch)."""
        return (self.major, self.minor, self.patch)


def is_newer_version(current: str | Version, latest: str | Version) -> bool:
    """
    Check if the latest version is newer than the current version.

    Args:
        current: Current version
        latest: Latest version to compare against

    Returns:
        True if latest is newer than current, False otherwise
    """
    if isinstance(current, str):
        current = Version(current)
    if isinstance(latest, str):
        latest = Version(latest)

    return latest > current


def get_latest_version(*versions: str | Version) -> Version:
    """
    Get the latest version from a list of versions.

    Args:
        *versions: Variable number of version strings or Version objects

    Returns:
        The latest Version object

    Raises:
        ValueError: If no versions are provided
    """
    if not versions:
        raise ValueError("At least one version must be provided")

    version_objects = []
    for v in versions:
        if isinstance(v, str):
            version_objects.append(Version(v))
        else:
            version_objects.append(v)

    return max(version_objects)
