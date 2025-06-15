"""
Secure Configuration Manager for DevManager
Handles sensitive configuration data like GitHub tokens with encryption
"""

import os
import json
import base64
import logging
from pathlib import Path
from typing import Any, Dict, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

try:
    from .common.constants import CONFIG_DIR
except ImportError:
    from common.constants import CONFIG_DIR


class SecureConfigManager:
    """
    Manages secure configuration with encryption for sensitive data like GitHub tokens.
    """
    
    def __init__(self):
        """Initialize the secure config manager."""
        self.config_dir = Path(CONFIG_DIR)
        self.config_file = self.config_dir / "secure_config.enc"
        self.key_file = self.config_dir / "config.key"
        
        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize encryption key
        self._key = self._get_or_create_key()
        self._fernet = Fernet(self._key)
        
        logging.info("Secure config manager initialized")
    
    def _get_or_create_key(self) -> bytes:
        """Get existing encryption key or create a new one."""
        if self.key_file.exists():
            try:
                with open(self.key_file, 'rb') as f:
                    return f.read()
            except Exception as e:
                logging.warning(f"Failed to read existing key: {e}")
        
        # Generate new key
        key = Fernet.generate_key()
        try:
            with open(self.key_file, 'wb') as f:
                f.write(key)
            # Set restrictive permissions (Windows)
            if os.name == 'nt':
                import stat
                os.chmod(self.key_file, stat.S_IREAD | stat.S_IWRITE)
        except Exception as e:
            logging.error(f"Failed to save encryption key: {e}")
        
        return key
    
    def _encrypt_data(self, data: str) -> bytes:
        """Encrypt string data."""
        return self._fernet.encrypt(data.encode())
    
    def _decrypt_data(self, encrypted_data: bytes) -> str:
        """Decrypt data to string."""
        return self._fernet.decrypt(encrypted_data).decode()
    
    def save_config(self, config_data: Dict[str, Any]) -> bool:
        """
        Save configuration data with encryption.
        
        Args:
            config_data: Dictionary of configuration data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert to JSON and encrypt
            json_data = json.dumps(config_data, indent=2)
            encrypted_data = self._encrypt_data(json_data)
            
            # Save to file
            with open(self.config_file, 'wb') as f:
                f.write(encrypted_data)
            
            logging.info("Secure configuration saved")
            return True
            
        except Exception as e:
            logging.error(f"Failed to save secure config: {e}")
            return False
    
    def load_config(self) -> Dict[str, Any]:
        """
        Load and decrypt configuration data.
        
        Returns:
            Dictionary of configuration data
        """
        try:
            if not self.config_file.exists():
                return {}
            
            # Read and decrypt
            with open(self.config_file, 'rb') as f:
                encrypted_data = f.read()
            
            json_data = self._decrypt_data(encrypted_data)
            config_data = json.loads(json_data)
            
            logging.info("Secure configuration loaded")
            return config_data
            
        except Exception as e:
            logging.error(f"Failed to load secure config: {e}")
            return {}
    
    def set_github_token(self, token: str) -> bool:
        """
        Set GitHub token in secure storage.
        
        Args:
            token: GitHub personal access token
            
        Returns:
            True if successful, False otherwise
        """
        config = self.load_config()
        config['github_token'] = token
        return self.save_config(config)
    
    def get_github_token(self) -> Optional[str]:
        """
        Get GitHub token from secure storage.
        
        Returns:
            GitHub token or None if not found
        """
        config = self.load_config()
        return config.get('github_token')
    
    def has_github_token(self) -> bool:
        """
        Check if GitHub token is configured.
        
        Returns:
            True if token exists, False otherwise
        """
        return self.get_github_token() is not None
    
    def remove_github_token(self) -> bool:
        """
        Remove GitHub token from secure storage.
        
        Returns:
            True if successful, False otherwise
        """
        config = self.load_config()
        if 'github_token' in config:
            del config['github_token']
            return self.save_config(config)
        return True
    
    def set_config_value(self, key: str, value: Any) -> bool:
        """
        Set a configuration value.
        
        Args:
            key: Configuration key
            value: Configuration value
            
        Returns:
            True if successful, False otherwise
        """
        config = self.load_config()
        config[key] = value
        return self.save_config(config)
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        config = self.load_config()
        return config.get(key, default)
    
    def validate_github_token(self, token: str) -> bool:
        """
        Validate GitHub token by testing API access.
        
        Args:
            token: GitHub token to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            from github import Github, GithubException
            
            github = Github(token)
            user = github.get_user()
            
            # Test basic access
            _ = user.login
            
            logging.info(f"GitHub token validated for user: {user.login}")
            return True
            
        except GithubException as e:
            logging.error(f"GitHub token validation failed: {e}")
            return False
        except Exception as e:
            logging.error(f"Token validation error: {e}")
            return False
    
    def get_github_token_with_fallback(self) -> Optional[str]:
        """
        Get GitHub token with fallback to environment variable.
        
        Returns:
            GitHub token from secure storage or environment
        """
        # First try secure storage
        token = self.get_github_token()
        if token:
            return token
        
        # Fallback to environment variable
        env_token = os.environ.get("GITHUB_TOKEN")
        if env_token:
            logging.info("Using GitHub token from environment variable")
            return env_token
        
        return None


# Global instance
_secure_config = None

def get_secure_config() -> SecureConfigManager:
    """Get global secure config manager instance."""
    global _secure_config
    if _secure_config is None:
        _secure_config = SecureConfigManager()
    return _secure_config
