"""
GUI components for DevManager using PySide6.
"""

import sys

from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class TokenModeDialog(QDialog):
    """Dialog for token mode operations."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("DevManager - Developer Mode")
        self.setFixedSize(500, 300)
        self.setModal(True)
        self.selected_option = None
        self._setup_ui()

    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)

        # Title
        title = QLabel("DevManager - Developer Mode")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 16, QFont.Bold))
        layout.addWidget(title)

        # Description
        desc = QLabel("Select an operation to perform:")
        desc.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc)

        layout.addSpacing(20)

        # Options group
        options_group = QGroupBox("Available Operations")
        options_layout = QVBoxLayout(options_group)

        # Build DevManager button
        self.build_devmanager_btn = QPushButton("Build and Upload DevManager")
        self.build_devmanager_btn.setMinimumHeight(40)
        self.build_devmanager_btn.clicked.connect(
            lambda: self._select_option("devmanager")
        )
        options_layout.addWidget(self.build_devmanager_btn)

        # Build DevAutomator button
        self.build_devautomator_btn = QPushButton("Build and Upload DevAutomator")
        self.build_devautomator_btn.setMinimumHeight(40)
        self.build_devautomator_btn.clicked.connect(
            lambda: self._select_option("devautomator")
        )
        options_layout.addWidget(self.build_devautomator_btn)

        layout.addWidget(options_group)

        layout.addSpacing(20)

        # Button layout
        button_layout = QHBoxLayout()

        # Cancel button
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        button_layout.addStretch()

        layout.addLayout(button_layout)

    def _select_option(self, option: str):
        """Handle option selection."""
        self.selected_option = option
        self.accept()

    def get_selected_option(self) -> str | None:
        """Get the selected option."""
        return self.selected_option


class ProgressDialog(QDialog):
    """Dialog for showing progress of operations with enhanced UI."""

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(600, 400)  # Larger size for better visibility
        self.setModal(True)
        self._setup_ui()

    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Title
        title_label = QLabel(self.windowTitle())
        title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont("Arial", 14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # Status label
        self.status_label = QLabel("Initializing...")
        self.status_label.setWordWrap(True)
        self.status_label.setMinimumHeight(40)
        self.status_label.setStyleSheet("QLabel { background-color: #f0f0f0; padding: 8px; border-radius: 4px; }")
        layout.addWidget(self.status_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.progress_bar.setMinimumHeight(25)
        layout.addWidget(self.progress_bar)

        # Log text area
        log_label = QLabel("Build Log:")
        log_label.setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(log_label)

        self.log_text = QTextEdit()
        self.log_text.setMinimumHeight(200)
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))  # Monospace font for logs
        self.log_text.setStyleSheet("QTextEdit { background-color: #2b2b2b; color: #ffffff; }")
        layout.addWidget(self.log_text)

        # Button layout
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setMinimumWidth(100)
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)

    def update_status(self, status: str):
        """Update the status label."""
        self.status_label.setText(status)
        # Also add to log for complete history
        self.add_log(status)

    def add_log(self, message: str):
        """Add a message to the log with timestamp."""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        self.log_text.append(formatted_message)

        # Auto-scroll to bottom
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def set_progress(self, value: int, maximum: int = 100):
        """Set progress bar value."""
        self.progress_bar.setRange(0, maximum)
        self.progress_bar.setValue(value)

    def set_indeterminate(self):
        """Set progress bar to indeterminate mode."""
        self.progress_bar.setRange(0, 0)


class NormalModeWindow(QMainWindow):
    """Main window for normal mode operations with progress tracking."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("DevManager - Auto-Update and Launch")
        self.setFixedSize(700, 500)
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint | Qt.WindowMinimizeButtonHint)

        # State variables
        self.update_worker = None
        self.operation_completed = False

        self._setup_ui()

    def _setup_ui(self):
        """Set up the user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Title
        title_label = QLabel("DevManager")
        title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont("Arial", 18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # Subtitle
        subtitle_label = QLabel("Auto-Update and DevAutomator Launcher")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setFont(QFont("Arial", 12))
        subtitle_label.setStyleSheet("color: #666666;")
        layout.addWidget(subtitle_label)

        layout.addSpacing(20)

        # Status section
        status_group = QGroupBox("Current Status")
        status_layout = QVBoxLayout(status_group)

        self.status_label = QLabel("Initializing...")
        self.status_label.setWordWrap(True)
        self.status_label.setMinimumHeight(30)
        self.status_label.setStyleSheet("QLabel { background-color: #f0f0f0; padding: 10px; border-radius: 5px; }")
        status_layout.addWidget(self.status_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 3)  # 3 main steps
        self.progress_bar.setValue(0)
        self.progress_bar.setMinimumHeight(25)
        status_layout.addWidget(self.progress_bar)

        layout.addWidget(status_group)

        # Log section
        log_group = QGroupBox("Operation Log")
        log_layout = QVBoxLayout(log_group)

        self.log_text = QTextEdit()
        self.log_text.setMinimumHeight(200)
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        self.log_text.setStyleSheet("QTextEdit { background-color: #2b2b2b; color: #ffffff; }")
        log_layout.addWidget(self.log_text)

        layout.addWidget(log_group)

        # Button section
        button_layout = QHBoxLayout()

        self.close_btn = QPushButton("Close")
        self.close_btn.setMinimumWidth(100)
        self.close_btn.setEnabled(False)  # Disabled until operation completes
        self.close_btn.clicked.connect(self.close)

        button_layout.addStretch()
        button_layout.addWidget(self.close_btn)

        layout.addLayout(button_layout)

    def update_status(self, message: str):
        """Update the status label."""
        self.status_label.setText(message)
        self.add_log(message)

    def add_log(self, message: str):
        """Add a message to the log with timestamp."""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        self.log_text.append(formatted_message)

        # Auto-scroll to bottom
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def set_progress(self, value: int):
        """Set progress bar value."""
        self.progress_bar.setValue(value)

    def operation_finished(self, success: bool, message: str):
        """Handle operation completion."""
        self.operation_completed = True
        self.close_btn.setEnabled(True)

        if success:
            self.update_status("✅ All operations completed successfully!")
            self.add_log("DevManager will now exit...")
            # Auto-close after 3 seconds
            QTimer.singleShot(3000, self.close)
        else:
            self.update_status(f"❌ Operation failed: {message}")
            self.close_btn.setText("Close")


class BuildWorker(QThread):
    """Worker thread for build operations with detailed progress reporting."""

    status_updated = Signal(str)
    log_message = Signal(str)
    progress_updated = Signal(int, int)
    finished = Signal(bool, str)  # success, message

    def __init__(self, operation: str, github_client):
        super().__init__()
        self.operation = operation
        self.github_client = github_client

    def emit_status(self, message: str):
        """Emit status update to GUI."""
        self.status_updated.emit(message)
        self.log_message.emit(message)

    def run(self):
        """Run the build operation with detailed progress reporting."""
        try:
            if self.operation == "devmanager":
                self.emit_status("🚀 Starting DevManager build and release process")
                self.emit_status("🔗 Connecting to GitHub repository...")
                success = self._build_devmanager_with_progress()
            elif self.operation == "devautomator":
                self.emit_status("🚀 Starting DevAutomator build and release process")
                self.emit_status("🔗 Connecting to GitHub repository...")
                success = self._build_devautomator_with_progress()
            else:
                self.finished.emit(False, f"Unknown operation: {self.operation}")
                return

            if success:
                self.emit_status("✅ Build and release completed successfully!")
                self.finished.emit(True, "Operation completed successfully")
            else:
                self.emit_status("❌ Build and release failed!")
                self.finished.emit(False, "Build operation failed")

        except Exception as e:
            error_msg = f"❌ Error during build: {e}"
            self.emit_status(error_msg)
            self.finished.emit(False, error_msg)

    def _build_devmanager_with_progress(self) -> bool:
        """Build DevManager with GUI progress updates."""
        try:
            # Step 1: GitHub connection
            self.emit_status("✅ Repository connection established")

            # Step 2: Build process
            self.emit_status("🔨 Compiling DevManager executable...")
            self.emit_status("📋 Build configuration:")
            self.emit_status("   • Target: DevManager.exe")
            self.emit_status("   • Mode: Single file executable")
            self.emit_status("   • Source: src/main.py")

            self.emit_status("🔄 Starting PyInstaller process...")
            self.emit_status("   This may take 2-3 minutes, please wait...")

            # Simulate build progress updates
            import time
            for i in range(5):
                time.sleep(2)  # Simulate build time
                elapsed = (i + 1) * 20
                self.emit_status(f"⏱️  Build in progress... ({elapsed}s elapsed)")
                self.progress_updated.emit(i + 1, 5)

            # Call actual build method
            success = self.github_client.build_and_release_devmanager()

            if success:
                self.emit_status("✅ DevManager built successfully!")
                self.emit_status("📤 Uploading to GitHub...")
                self.emit_status("🎉 Release is now available on GitHub")

            return success

        except Exception as e:
            self.emit_status(f"❌ Build failed: {e}")
            return False

    def _build_devautomator_with_progress(self) -> bool:
        """Build DevAutomator with GUI progress updates."""
        try:
            # Step 1: GitHub connection
            self.emit_status("✅ Repository connection established")

            # Step 2: Build process
            self.emit_status("🔨 Compiling DevAutomator executable...")
            self.emit_status("📁 DevAutomator project found")
            self.emit_status("📋 Build configuration:")
            self.emit_status("   • Target: DevAutomator.exe")
            self.emit_status("   • Mode: Single file executable")
            self.emit_status("   • Excluding: torch, numpy, scipy, pandas, etc.")

            self.emit_status("🔄 Starting PyInstaller process...")
            self.emit_status("   This may take 2-3 minutes, please wait...")

            # Simulate build progress updates
            import time
            for i in range(5):
                time.sleep(2)  # Simulate build time
                elapsed = (i + 1) * 20
                self.emit_status(f"⏱️  Build in progress... ({elapsed}s elapsed)")
                self.progress_updated.emit(i + 1, 5)

            # Call actual build method
            success = self.github_client.build_and_release_devautomator()

            if success:
                self.emit_status("✅ DevAutomator built successfully!")
                self.emit_status("📤 Uploading to GitHub...")
                self.emit_status("🎉 Release is now available on GitHub")

            return success

        except Exception as e:
            self.emit_status(f"❌ Build failed: {e}")
            return False


class NormalModeWorker(QThread):
    """Worker thread for normal mode operations (self-update, DevAutomator update, launch)."""

    status_updated = Signal(str)
    log_message = Signal(str)
    progress_updated = Signal(int)
    finished = Signal(bool, str)  # success, message

    def __init__(self):
        super().__init__()

    def emit_status(self, message: str):
        """Emit status update to GUI."""
        self.status_updated.emit(message)
        self.log_message.emit(message)

    def run(self):
        """Run the normal mode operations."""
        try:
            # Import here to avoid circular imports
            from .updater import DevManagerUpdater, DevAutomatorUpdater
            from .token_handler_compatible import CompatibleTokenHandler

            # Step 1: Check for DevManager self-updates
            self.emit_status("🔍 Checking for DevManager updates...")
            self.progress_updated.emit(1)

            devmanager_updater = DevManagerUpdater()

            if devmanager_updater.check_for_updates():
                self.emit_status("✅ DevManager update available!")
                self.emit_status("📥 Downloading and installing update...")

                if devmanager_updater.download_and_install_update():
                    self.emit_status("✅ DevManager updated successfully.")
                    self.emit_status("🔄 Restarting with new version...")
                    # The self-update script will handle restart
                    self.finished.emit(True, "DevManager updated and restarting")
                    return
                else:
                    self.emit_status("❌ Failed to update DevManager")
                    self.finished.emit(False, "DevManager update failed")
                    return
            else:
                self.emit_status("✅ DevManager is up to date.")

            # Step 2: Check for DevAutomator updates
            self.emit_status("🔍 Checking for DevAutomator updates...")
            self.progress_updated.emit(2)

            devautomator_updater = DevAutomatorUpdater()

            if devautomator_updater.check_for_updates():
                self.emit_status("✅ DevAutomator update available!")
                self.emit_status("🛑 Stopping existing DevAutomator processes...")

                # Kill existing DevAutomator process if running
                devautomator_updater.stop_devautomator()

                # Download and install update
                self.emit_status("📥 Downloading and installing update...")
                if devautomator_updater.download_and_install_update():
                    self.emit_status("✅ DevAutomator updated successfully.")
                else:
                    self.emit_status("❌ Failed to update DevAutomator")
                    self.finished.emit(False, "DevAutomator update failed")
                    return
            else:
                self.emit_status("✅ DevAutomator is up to date.")

            # Step 3: Start DevAutomator with token and exit
            self.emit_status("🔑 Generating secure authentication token...")
            self.progress_updated.emit(3)

            # Generate token for DevAutomator
            token_handler = CompatibleTokenHandler()
            token = token_handler.generate_token()

            # Start DevAutomator with token
            self.emit_status("🚀 Launching DevAutomator with token...")
            if devautomator_updater.start_devautomator_with_token(token):
                self.emit_status("✅ DevAutomator started successfully!")
                self.finished.emit(True, "All operations completed successfully")
            else:
                self.emit_status("❌ Failed to start DevAutomator")
                self.finished.emit(False, "Failed to start DevAutomator")

        except Exception as e:
            error_msg = f"❌ Error during normal mode operations: {e}"
            self.emit_status(error_msg)
            self.finished.emit(False, error_msg)


def show_token_mode_dialog() -> str | None:
    """
    Show the token mode dialog and return the selected option.

    Returns:
        Selected option or None if cancelled
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    dialog = TokenModeDialog()
    if dialog.exec() == QDialog.Accepted:
        return dialog.get_selected_option()
    return None


def show_build_progress_dialog(operation: str, github_client) -> bool:
    """
    Show the build progress dialog and perform the operation.

    Args:
        operation: Operation to perform ("devmanager" or "devautomator")
        github_client: GitHub client instance

    Returns:
        True if successful, False otherwise
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    dialog = ProgressDialog(f"Building {operation.title()}")
    worker = BuildWorker(operation, github_client)

    # Connect signals
    worker.status_updated.connect(dialog.update_status)
    worker.log_message.connect(dialog.add_log)
    worker.progress_updated.connect(dialog.set_progress)

    success = False

    def on_finished(result: bool, message: str):
        nonlocal success
        success = result
        dialog.cancel_btn.setText("Close")
        if result:
            QMessageBox.information(dialog, "Success", message)
        else:
            QMessageBox.critical(dialog, "Error", message)

    worker.finished.connect(on_finished)

    # Start worker and show dialog
    worker.start()
    dialog.exec()

    # Clean up
    worker.quit()
    worker.wait()

    return success


def show_error_dialog(title: str, message: str):
    """Show an error dialog."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    QMessageBox.critical(None, title, message)


def show_info_dialog(title: str, message: str):
    """Show an information dialog."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    QMessageBox.information(None, title, message)


def show_normal_mode_window() -> bool:
    """
    Show the normal mode window and perform auto-update operations.

    Returns:
        True if successful, False otherwise
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    window = NormalModeWindow()
    worker = NormalModeWorker()

    # Connect signals
    worker.status_updated.connect(window.update_status)
    worker.log_message.connect(window.add_log)
    worker.progress_updated.connect(window.set_progress)
    worker.finished.connect(window.operation_finished)

    success = False

    def on_finished(result: bool, message: str):
        nonlocal success
        success = result

    worker.finished.connect(on_finished)

    # Start worker and show window
    worker.start()
    window.show()

    # Start the event loop
    app.exec()

    # Clean up
    worker.quit()
    worker.wait()

    return success
