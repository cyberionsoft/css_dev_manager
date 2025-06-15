"""
Utility functions for DevManager.
"""

import hashlib
import json
import logging
import os
import platform
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Any

from .constants import CURRENT_PLATFORM, SUPPORTED_PLATFORMS


def get_platform_info() -> dict[str, str]:
    """
    Get current platform information.

    Returns:
        Dictionary containing platform information
    """
    system = platform.system().lower()
    machine = platform.machine().lower()

    # Normalize architecture names
    if machine in ("x86_64", "amd64"):
        arch = "x64"
    elif machine in ("i386", "i686", "x86"):
        arch = "x86"
    elif machine in ("aarch64", "arm64"):
        arch = "arm64"
    else:
        arch = machine

    platform_info = SUPPORTED_PLATFORMS.get(system, {})

    return {
        "system": system,
        "architecture": arch,
        "platform_key": platform_info.get("platform_key", system),
        "executable_ext": platform_info.get("executable_ext", ""),
        "archive_ext": platform_info.get("archive_ext", ".zip"),
        "name": platform_info.get("name", system.title()),
    }


def calculate_checksum(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Calculate checksum of a file.

    Args:
        file_path: Path to the file
        algorithm: Hash algorithm to use (default: sha256)

    Returns:
        Hexadecimal checksum string

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If algorithm is not supported
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        hasher = hashlib.new(algorithm)
    except ValueError:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}")

    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)

    return hasher.hexdigest()


def verify_checksum(
    file_path: Path, expected_checksum: str, algorithm: str = "sha256"
) -> bool:
    """
    Verify file checksum against expected value.

    Args:
        file_path: Path to the file
        expected_checksum: Expected checksum value
        algorithm: Hash algorithm to use

    Returns:
        True if checksum matches, False otherwise
    """
    try:
        actual_checksum = calculate_checksum(file_path, algorithm)
        return actual_checksum.lower() == expected_checksum.lower()
    except (FileNotFoundError, ValueError):
        return False


def ensure_directory(directory: Path) -> None:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        directory: Path to the directory
    """
    directory.mkdir(parents=True, exist_ok=True)


def safe_extract_zip(zip_path: Path, extract_to: Path, overwrite: bool = True) -> None:
    """
    Safely extract a ZIP file to a directory.

    Args:
        zip_path: Path to the ZIP file
        extract_to: Directory to extract to
        overwrite: Whether to overwrite existing files

    Raises:
        zipfile.BadZipFile: If the ZIP file is corrupted
        PermissionError: If unable to write to destination
    """
    if not zip_path.exists():
        raise FileNotFoundError(f"ZIP file not found: {zip_path}")

    # Create extraction directory
    ensure_directory(extract_to)

    # If overwrite is False and directory is not empty, raise error
    if not overwrite and any(extract_to.iterdir()):
        raise FileExistsError(f"Directory not empty and overwrite=False: {extract_to}")

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        # Security check: ensure no path traversal
        for member in zip_ref.namelist():
            if os.path.isabs(member) or ".." in member:
                raise ValueError(f"Unsafe path in ZIP file: {member}")

        zip_ref.extractall(extract_to)


def safe_remove_directory(directory: Path, max_retries: int = 3) -> bool:
    """
    Safely remove a directory with retries.

    Args:
        directory: Directory to remove
        max_retries: Maximum number of retry attempts

    Returns:
        True if successfully removed, False otherwise
    """
    if not directory.exists():
        return True

    for attempt in range(max_retries):
        try:
            shutil.rmtree(directory)
            return True
        except (OSError, PermissionError) as e:
            logging.warning(f"Attempt {attempt + 1} to remove {directory} failed: {e}")
            if attempt < max_retries - 1:
                import time

                time.sleep(1)  # Wait before retry

    return False


def load_json_file(file_path: Path) -> dict[str, Any] | None:
    """
    Load JSON data from a file.

    Args:
        file_path: Path to the JSON file

    Returns:
        Parsed JSON data or None if file doesn't exist or is invalid
    """
    if not file_path.exists():
        return None

    try:
        with open(file_path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        logging.error(f"Failed to load JSON file {file_path}: {e}")
        return None


def save_json_file(file_path: Path, data: dict[str, Any], indent: int = 2) -> bool:
    """
    Save data to a JSON file.

    Args:
        file_path: Path to save the JSON file
        data: Data to save
        indent: JSON indentation level

    Returns:
        True if successful, False otherwise
    """
    try:
        ensure_directory(file_path.parent)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
        return True
    except (OSError, TypeError) as e:
        logging.error(f"Failed to save JSON file {file_path}: {e}")
        return False


def get_executable_path() -> Path:
    """
    Get the path to the current executable.

    Returns:
        Path to the current executable
    """
    import sys

    if getattr(sys, "frozen", False):
        # Running as PyInstaller bundle
        return Path(sys.executable)
    else:
        # Running as Python script
        return Path(sys.argv[0]).resolve()


def is_admin() -> bool:
    """
    Check if the current process has administrator privileges.

    Returns:
        True if running with admin privileges, False otherwise
    """
    try:
        if CURRENT_PLATFORM == "windows":
            import ctypes

            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        else:
            return os.geteuid() == 0
    except Exception:
        return False


def create_temp_directory() -> Path:
    """
    Create a temporary directory.

    Returns:
        Path to the temporary directory
    """
    return Path(tempfile.mkdtemp())


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted size string
    """
    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024.0 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1

    return f"{size_bytes:.1f} {size_names[i]}"
