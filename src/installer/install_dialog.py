"""
Installation dialog for DevManager first-run setup.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QThread, Signal, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QProgressBar,
    QTextEdit,
    QMessageBox,
    QCheckBox,
)
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtCore import Qt

from ..common.constants import APP_NAME, DEVMANAGER_INSTALL_DIR


class InstallationWorker(QThread):
    """Worker thread for performing the installation."""
    
    progress_updated = Signal(int, str)  # progress percentage, status message
    installation_completed = Signal(bool, str)  # success, message
    
    def __init__(self, installer, create_shortcuts: bool = True):
        """
        Initialize the installation worker.
        
        Args:
            installer: FirstRunInstaller instance
            create_shortcuts: Whether to create shortcuts
        """
        super().__init__()
        self.installer = installer
        self.create_shortcuts = create_shortcuts
    
    def run(self):
        """Run the installation process."""
        try:
            self.progress_updated.emit(10, "Preparing installation...")
            
            # Check admin privileges
            from ..common.utils import is_admin
            from ..common.constants import CURRENT_PLATFORM
            
            if CURRENT_PLATFORM == "windows" and not is_admin():
                self.progress_updated.emit(20, "Requesting administrator privileges...")
                success = self.installer._install_with_admin_privileges()
                if success:
                    self.installation_completed.emit(True, "Installation script launched with admin privileges")
                else:
                    self.installation_completed.emit(False, "Failed to obtain administrator privileges")
                return
            
            self.progress_updated.emit(30, "Creating installation directory...")
            
            # Create installation directory
            from ..common.utils import ensure_directory
            ensure_directory(self.installer.install_dir)
            
            self.progress_updated.emit(50, "Copying executable...")
            
            # Copy executable
            if not self.installer._copy_executable():
                self.installation_completed.emit(False, "Failed to copy executable")
                return
            
            self.progress_updated.emit(70, "Creating shortcuts...")
            
            # Create shortcuts if requested
            if self.create_shortcuts and CURRENT_PLATFORM == "windows":
                self.installer._create_windows_shortcuts()
                self.installer._create_registry_entries()
            
            self.progress_updated.emit(100, "Installation completed!")
            self.installation_completed.emit(True, "DevManager installed successfully")
            
        except Exception as e:
            logging.error(f"Installation worker error: {e}", exc_info=True)
            self.installation_completed.emit(False, f"Installation failed: {str(e)}")


class InstallDialog(QDialog):
    """Dialog for DevManager first-run installation."""
    
    def __init__(self, installer, parent=None):
        """
        Initialize the installation dialog.
        
        Args:
            installer: FirstRunInstaller instance
            parent: Parent widget
        """
        super().__init__(parent)
        self.installer = installer
        self.installation_successful = False
        self.worker = None
        
        self.setWindowTitle(f"{APP_NAME} - First Run Setup")
        self.setFixedSize(500, 400)
        self.setModal(True)
        
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel(f"Welcome to {APP_NAME}")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Description
        desc_text = (
            f"{APP_NAME} needs to be installed to your system directory "
            f"for proper operation.\n\n"
            f"Installation directory:\n{self.installer.install_dir}\n\n"
            f"This will:\n"
            f"• Copy {APP_NAME} to the system directory\n"
            f"• Create desktop and start menu shortcuts\n"
            f"• Register the application with Windows\n\n"
            f"Administrator privileges may be required."
        )
        
        desc_label = QLabel(desc_text)
        desc_label.setWordWrap(True)
        desc_label.setAlignment(Qt.AlignLeft)
        layout.addWidget(desc_label)
        
        # Options
        self.shortcuts_checkbox = QCheckBox("Create desktop and start menu shortcuts")
        self.shortcuts_checkbox.setChecked(True)
        layout.addWidget(self.shortcuts_checkbox)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setVisible(False)
        layout.addWidget(self.status_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.install_button = QPushButton("Install")
        self.install_button.clicked.connect(self.start_installation)
        button_layout.addWidget(self.install_button)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
    def start_installation(self):
        """Start the installation process."""
        self.install_button.setEnabled(False)
        self.cancel_button.setText("Close")
        
        self.progress_bar.setVisible(True)
        self.status_label.setVisible(True)
        
        # Create and start worker thread
        create_shortcuts = self.shortcuts_checkbox.isChecked()
        self.worker = InstallationWorker(self.installer, create_shortcuts)
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.installation_completed.connect(self.installation_finished)
        self.worker.start()
        
    def update_progress(self, percentage: int, message: str):
        """
        Update the installation progress.
        
        Args:
            percentage: Progress percentage (0-100)
            message: Status message
        """
        self.progress_bar.setValue(percentage)
        self.status_label.setText(message)
        
    def installation_finished(self, success: bool, message: str):
        """
        Handle installation completion.
        
        Args:
            success: Whether installation was successful
            message: Result message
        """
        if success:
            self.installation_successful = True
            self.status_label.setText("Installation completed successfully!")
            
            # Show success message
            QMessageBox.information(
                self,
                "Installation Complete",
                f"{APP_NAME} has been installed successfully.\n\n"
                f"The application will now restart from the installed location."
            )
            
            self.accept()
        else:
            self.status_label.setText(f"Installation failed: {message}")
            
            # Show error message
            QMessageBox.critical(
                self,
                "Installation Failed",
                f"Failed to install {APP_NAME}:\n\n{message}\n\n"
                f"You can try running as administrator or contact support."
            )
            
        self.install_button.setEnabled(True)
        
    def closeEvent(self, event):
        """Handle dialog close event."""
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(
                self,
                "Installation in Progress",
                "Installation is currently in progress. Are you sure you want to cancel?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.worker.terminate()
                self.worker.wait()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


def show_install_dialog(installer) -> bool:
    """
    Show the installation dialog.
    
    Args:
        installer: FirstRunInstaller instance
        
    Returns:
        True if installation was successful, False otherwise
    """
    try:
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        dialog = InstallDialog(installer)
        result = dialog.exec()
        
        return result == QDialog.Accepted and dialog.installation_successful
        
    except Exception as e:
        logging.error(f"Failed to show install dialog: {e}", exc_info=True)
        return False
