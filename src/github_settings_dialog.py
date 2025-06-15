"""
GitHub Settings Dialog for DevManager
Handles GitHub token configuration and validation
"""

import logging
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QTextEdit, QGroupBox, QMessageBox, QProgressBar
)

try:
    from .secure_config import get_secure_config
except ImportError:
    from secure_config import get_secure_config


class TokenValidationWorker(QThread):
    """Worker thread for validating GitHub tokens."""
    
    validation_complete = Signal(bool, str)  # success, message
    
    def __init__(self, token: str):
        super().__init__()
        self.token = token
    
    def run(self):
        """Validate the GitHub token."""
        try:
            secure_config = get_secure_config()
            is_valid = secure_config.validate_github_token(self.token)
            
            if is_valid:
                self.validation_complete.emit(True, "GitHub token is valid!")
            else:
                self.validation_complete.emit(False, "GitHub token validation failed. Please check the token.")
                
        except Exception as e:
            self.validation_complete.emit(False, f"Validation error: {str(e)}")


class GitHubSettingsDialog(QDialog):
    """Dialog for configuring GitHub settings."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("GitHub Settings - DevManager")
        self.setFixedSize(600, 500)
        self.setModal(True)
        
        self.secure_config = get_secure_config()
        self.validation_worker = None
        
        self._setup_ui()
        self._load_current_settings()
    
    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("GitHub Configuration")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 16, QFont.Bold))
        layout.addWidget(title)
        
        # Description
        desc = QLabel("Configure GitHub access for build and release operations")
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("color: #666; margin-bottom: 20px;")
        layout.addWidget(desc)
        
        # Token configuration group
        token_group = QGroupBox("GitHub Personal Access Token")
        token_layout = QVBoxLayout(token_group)
        
        # Token input
        token_label = QLabel("GitHub Token:")
        token_layout.addWidget(token_label)
        
        self.token_input = QLineEdit()
        self.token_input.setEchoMode(QLineEdit.Password)
        self.token_input.setPlaceholderText("Enter your GitHub personal access token...")
        self.token_input.textChanged.connect(self._on_token_changed)
        token_layout.addWidget(self.token_input)
        
        # Show/Hide token button
        token_buttons_layout = QHBoxLayout()
        
        self.show_token_btn = QPushButton("Show Token")
        self.show_token_btn.clicked.connect(self._toggle_token_visibility)
        token_buttons_layout.addWidget(self.show_token_btn)
        
        self.validate_btn = QPushButton("Validate Token")
        self.validate_btn.clicked.connect(self._validate_token)
        self.validate_btn.setEnabled(False)
        token_buttons_layout.addWidget(self.validate_btn)
        
        token_buttons_layout.addStretch()
        token_layout.addLayout(token_buttons_layout)
        
        # Validation progress
        self.validation_progress = QProgressBar()
        self.validation_progress.setVisible(False)
        token_layout.addWidget(self.validation_progress)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        token_layout.addWidget(self.status_label)
        
        layout.addWidget(token_group)
        
        # Instructions group
        instructions_group = QGroupBox("How to Get a GitHub Token")
        instructions_layout = QVBoxLayout(instructions_group)
        
        instructions_text = QTextEdit()
        instructions_text.setReadOnly(True)
        instructions_text.setMaximumHeight(150)
        instructions_text.setHtml("""
        <p><b>To create a GitHub Personal Access Token:</b></p>
        <ol>
        <li>Go to <a href="https://github.com/settings/tokens">GitHub Settings → Developer settings → Personal access tokens</a></li>
        <li>Click "Generate new token (classic)"</li>
        <li>Give it a descriptive name (e.g., "DevManager Build Token")</li>
        <li>Select the following scopes:
            <ul>
            <li><b>repo</b> - Full control of private repositories</li>
            <li><b>workflow</b> - Update GitHub Action workflows</li>
            </ul>
        </li>
        <li>Click "Generate token"</li>
        <li>Copy the token and paste it above</li>
        </ol>
        <p><b>⚠️ Important:</b> Keep your token secure and never share it!</p>
        """)
        instructions_layout.addWidget(instructions_text)
        
        layout.addWidget(instructions_group)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        self.clear_btn = QPushButton("Clear Token")
        self.clear_btn.clicked.connect(self._clear_token)
        buttons_layout.addWidget(self.clear_btn)
        
        buttons_layout.addStretch()
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_btn)
        
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self._save_settings)
        self.save_btn.setEnabled(False)
        buttons_layout.addWidget(self.save_btn)
        
        layout.addLayout(buttons_layout)
    
    def _load_current_settings(self):
        """Load current GitHub settings."""
        token = self.secure_config.get_github_token()
        if token:
            self.token_input.setText(token)
            self.status_label.setText("✅ GitHub token is configured")
            self.status_label.setStyleSheet("color: green;")
        else:
            self.status_label.setText("⚠️ No GitHub token configured")
            self.status_label.setStyleSheet("color: orange;")
    
    def _on_token_changed(self):
        """Handle token input changes."""
        has_token = bool(self.token_input.text().strip())
        self.validate_btn.setEnabled(has_token)
        self.save_btn.setEnabled(has_token)
        
        if has_token:
            self.status_label.setText("Token entered - click 'Validate Token' to verify")
            self.status_label.setStyleSheet("color: blue;")
        else:
            self.status_label.setText("⚠️ No GitHub token entered")
            self.status_label.setStyleSheet("color: orange;")
    
    def _toggle_token_visibility(self):
        """Toggle token visibility."""
        if self.token_input.echoMode() == QLineEdit.Password:
            self.token_input.setEchoMode(QLineEdit.Normal)
            self.show_token_btn.setText("Hide Token")
        else:
            self.token_input.setEchoMode(QLineEdit.Password)
            self.show_token_btn.setText("Show Token")
    
    def _validate_token(self):
        """Validate the GitHub token."""
        token = self.token_input.text().strip()
        if not token:
            return
        
        # Show progress
        self.validation_progress.setVisible(True)
        self.validation_progress.setRange(0, 0)  # Indeterminate
        self.validate_btn.setEnabled(False)
        self.status_label.setText("🔍 Validating GitHub token...")
        self.status_label.setStyleSheet("color: blue;")
        
        # Start validation in background thread
        self.validation_worker = TokenValidationWorker(token)
        self.validation_worker.validation_complete.connect(self._on_validation_complete)
        self.validation_worker.start()
    
    def _on_validation_complete(self, success: bool, message: str):
        """Handle validation completion."""
        self.validation_progress.setVisible(False)
        self.validate_btn.setEnabled(True)
        
        if success:
            self.status_label.setText(f"✅ {message}")
            self.status_label.setStyleSheet("color: green;")
        else:
            self.status_label.setText(f"❌ {message}")
            self.status_label.setStyleSheet("color: red;")
        
        # Clean up worker
        if self.validation_worker:
            self.validation_worker.quit()
            self.validation_worker.wait()
            self.validation_worker = None
    
    def _clear_token(self):
        """Clear the GitHub token."""
        reply = QMessageBox.question(
            self, 
            "Clear Token", 
            "Are you sure you want to clear the GitHub token?\n\nThis will disable build and release functionality.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.token_input.clear()
            self.secure_config.remove_github_token()
            self.status_label.setText("⚠️ GitHub token cleared")
            self.status_label.setStyleSheet("color: orange;")
    
    def _save_settings(self):
        """Save GitHub settings."""
        token = self.token_input.text().strip()
        if not token:
            QMessageBox.warning(self, "Invalid Token", "Please enter a GitHub token.")
            return
        
        # Save token
        if self.secure_config.set_github_token(token):
            QMessageBox.information(
                self, 
                "Settings Saved", 
                "GitHub token has been saved securely.\n\nYou can now use build and release functionality."
            )
            self.accept()
        else:
            QMessageBox.critical(
                self, 
                "Save Failed", 
                "Failed to save GitHub token. Please try again."
            )


def show_github_settings_dialog(parent=None) -> bool:
    """
    Show GitHub settings dialog.
    
    Args:
        parent: Parent widget
        
    Returns:
        True if settings were saved, False otherwise
    """
    dialog = GitHubSettingsDialog(parent)
    return dialog.exec() == QDialog.Accepted
