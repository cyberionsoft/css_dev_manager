"""
Self-update script for DevManager.

This script is executed by DevManager to update itself.
It waits for the main process to exit, then replaces the executable
and restarts the application.
"""

import os
import sys
import time
import shutil
import zipfile
import logging
import subprocess
from pathlib import Path
from typing import Optional


def setup_logging() -> None:
    """Set up logging for the update script."""
    log_file = Path.home() / "AppData" / "Local" / "DevManager" / "update.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )


def wait_for_process_exit(process_name: str, max_wait: int = 30) -> bool:
    """
    Wait for a process to exit.
    
    Args:
        process_name: Name of the process to wait for
        max_wait: Maximum time to wait in seconds
        
    Returns:
        True if process exited, False if timeout
    """
    import psutil
    
    for _ in range(max_wait):
        found = False
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] and process_name.lower() in proc.info['name'].lower():
                found = True
                break
        
        if not found:
            return True
        
        time.sleep(1)
    
    return False


def backup_installation(install_dir: Path) -> Optional[Path]:
    """
    Create a backup of the current installation.
    
    Args:
        install_dir: Installation directory to backup
        
    Returns:
        Path to backup directory or None if failed
    """
    try:
        backup_dir = install_dir.parent / f"{install_dir.name}_backup"
        
        # Remove old backup if exists
        if backup_dir.exists():
            shutil.rmtree(backup_dir)
        
        # Create new backup
        shutil.copytree(install_dir, backup_dir)
        logging.info(f"Created backup at: {backup_dir}")
        
        return backup_dir
        
    except Exception as e:
        logging.error(f"Failed to create backup: {e}")
        return None


def extract_update(update_file: Path, install_dir: Path) -> bool:
    """
    Extract the update to the installation directory.
    
    Args:
        update_file: Path to the update ZIP file
        install_dir: Installation directory
        
    Returns:
        True if successful, False otherwise
    """
    try:
        logging.info(f"Extracting update from: {update_file}")
        
        with zipfile.ZipFile(update_file, 'r') as zip_ref:
            # Security check
            for member in zip_ref.namelist():
                if os.path.isabs(member) or ".." in member:
                    raise ValueError(f"Unsafe path in ZIP: {member}")
            
            # Extract all files
            zip_ref.extractall(install_dir)
        
        logging.info("Update extracted successfully")
        return True
        
    except Exception as e:
        logging.error(f"Failed to extract update: {e}")
        return False


def restore_backup(backup_dir: Path, install_dir: Path) -> bool:
    """
    Restore from backup in case of failure.
    
    Args:
        backup_dir: Backup directory
        install_dir: Installation directory
        
    Returns:
        True if successful, False otherwise
    """
    try:
        logging.info("Restoring from backup...")
        
        # Remove failed installation
        if install_dir.exists():
            shutil.rmtree(install_dir)
        
        # Restore backup
        shutil.copytree(backup_dir, install_dir)
        
        logging.info("Backup restored successfully")
        return True
        
    except Exception as e:
        logging.error(f"Failed to restore backup: {e}")
        return False


def restart_application(exe_path: Path) -> bool:
    """
    Restart the application.
    
    Args:
        exe_path: Path to the executable
        
    Returns:
        True if successful, False otherwise
    """
    try:
        if not exe_path.exists():
            logging.error(f"Executable not found: {exe_path}")
            return False
        
        logging.info(f"Restarting application: {exe_path}")
        
        # Start the application
        if sys.platform == "win32":
            os.startfile(str(exe_path))
        else:
            subprocess.Popen([str(exe_path)])
        
        return True
        
    except Exception as e:
        logging.error(f"Failed to restart application: {e}")
        return False


def cleanup_files(*file_paths: Path) -> None:
    """
    Clean up temporary files.
    
    Args:
        file_paths: Paths to files to remove
    """
    for file_path in file_paths:
        try:
            if file_path.exists():
                if file_path.is_file():
                    file_path.unlink()
                else:
                    shutil.rmtree(file_path)
                logging.info(f"Cleaned up: {file_path}")
        except Exception as e:
            logging.warning(f"Failed to clean up {file_path}: {e}")


def main() -> int:
    """
    Main update function.
    
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    if len(sys.argv) != 3:
        print("Usage: self_update.py <update_file> <install_dir>")
        return 1
    
    update_file = Path(sys.argv[1])
    install_dir = Path(sys.argv[2])
    
    setup_logging()
    logging.info("Starting DevManager self-update process")
    
    try:
        # Validate inputs
        if not update_file.exists():
            logging.error(f"Update file not found: {update_file}")
            return 1
        
        if not install_dir.exists():
            logging.error(f"Installation directory not found: {install_dir}")
            return 1
        
        # Wait for DevManager to exit
        logging.info("Waiting for DevManager to exit...")
        if not wait_for_process_exit("DevManager"):
            logging.warning("DevManager process may still be running")
        
        time.sleep(2)  # Additional wait
        
        # Create backup
        backup_dir = backup_installation(install_dir)
        if not backup_dir:
            logging.error("Failed to create backup, aborting update")
            return 1
        
        # Extract update
        if not extract_update(update_file, install_dir):
            logging.error("Failed to extract update, restoring backup")
            restore_backup(backup_dir, install_dir)
            return 1
        
        # Restart application
        exe_path = install_dir / "DevManager.exe"
        if not restart_application(exe_path):
            logging.error("Failed to restart application")
            # Don't restore backup here as the update might be successful
            return 1
        
        # Clean up
        cleanup_files(update_file, backup_dir)
        
        logging.info("DevManager update completed successfully")
        return 0
        
    except Exception as e:
        logging.error(f"Unexpected error during update: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
