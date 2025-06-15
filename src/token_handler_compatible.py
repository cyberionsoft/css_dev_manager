"""
Compatible Token Handler for DevManager that works with DevAutomator.
This creates tokens that both systems can understand.
"""

import hashlib
import json
import logging
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

try:
    from .common.constants import CONFIG_DIR, TOKEN_EXPIRY_HOURS, TOKEN_FILE
    from .common.utils import ensure_directory
except ImportError:
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from common.constants import CONFIG_DIR, TOKEN_EXPIRY_HOURS, TOKEN_FILE
    from common.utils import ensure_directory


class CompatibleTokenHandler:
    """
    Token handler that creates tokens compatible with both DevManager and DevAutomator.
    Uses simple token + hash system that DevAutomator expects.
    """

    def __init__(self):
        """Initialize the compatible token handler."""
        self.token_file_path = CONFIG_DIR / TOKEN_FILE
        ensure_directory(CONFIG_DIR)

    def generate_token(self) -> str:
        """
        Generate a new secure token compatible with DevAutomator.

        Returns:
            Generated token string
        """
        # Generate a secure random token
        token = secrets.token_urlsafe(32)
        
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=TOKEN_EXPIRY_HOURS)
        
        # Create token data in format DevAutomator expects
        token_data = {
            "token_hash": self._hash_token(token),
            "created_at": now.isoformat(),
            "expires_at": expires_at.isoformat(),
            "used": False,
        }

        self._save_token_data(token_data)
        logging.info(f"Generated new compatible token (expires in {TOKEN_EXPIRY_HOURS} hours)")

        return token

    def validate_token(self, token: str) -> bool:
        """
        Validate a token.

        Args:
            token: Token to validate

        Returns:
            True if token is valid, False otherwise
        """
        try:
            token_data = self._load_token_data()
            if not token_data:
                logging.warning("No token data found")
                return False

            # Check if token hash matches
            token_hash = self._hash_token(token)
            if token_data.get("token_hash") != token_hash:
                logging.warning("Token hash mismatch")
                return False

            # Check if token has expired
            expires_at = datetime.fromisoformat(token_data["expires_at"])
            if datetime.now(timezone.utc) > expires_at:
                logging.warning("Token has expired")
                return False

            # Check if token has already been used (for one-time use tokens)
            if token_data.get("used", False):
                logging.warning("Token has already been used")
                return False

            # Mark token as used for one-time use
            token_data["used"] = True
            token_data["used_at"] = datetime.now(timezone.utc).isoformat()
            self._save_token_data(token_data)

            logging.info("Token validation successful")
            return True

        except Exception as e:
            logging.error(f"Token validation error: {e}")
            return False

    def mark_token_used(self, token: str) -> bool:
        """
        Mark a token as used.

        Args:
            token: Token to mark as used

        Returns:
            True if successful, False otherwise
        """
        try:
            token_data = self._load_token_data()
            if not token_data:
                return False

            token_hash = self._hash_token(token)
            if token_data.get("token_hash") == token_hash:
                token_data["used"] = True
                token_data["used_at"] = datetime.now(timezone.utc).isoformat()
                self._save_token_data(token_data)
                logging.info("Token marked as used")
                return True

            return False

        except Exception as e:
            logging.error(f"Error marking token as used: {e}")
            return False

    def revoke_token(self) -> bool:
        """
        Revoke the current token.

        Returns:
            True if successful, False otherwise
        """
        try:
            if self.token_file_path.exists():
                self.token_file_path.unlink()
                logging.info("Token revoked successfully")
                return True
            return False

        except Exception as e:
            logging.error(f"Error revoking token: {e}")
            return False

    def get_token_info(self) -> dict[str, Any] | None:
        """
        Get information about the current token.

        Returns:
            Token information dictionary or None if no token exists
        """
        try:
            token_data = self._load_token_data()
            if not token_data:
                return None

            # Remove sensitive information
            info = {
                "created_at": token_data.get("created_at"),
                "expires_at": token_data.get("expires_at"),
                "used": token_data.get("used", False),
                "used_at": token_data.get("used_at"),
            }

            return info

        except Exception as e:
            logging.error(f"Error getting token info: {e}")
            return None

    def _hash_token(self, token: str) -> str:
        """
        Hash a token for secure comparison (compatible with DevAutomator).

        Args:
            token: Token to hash

        Returns:
            Hashed token
        """
        return hashlib.sha256(token.encode()).hexdigest()

    def _load_token_data(self) -> dict[str, Any] | None:
        """
        Load token data from file.

        Returns:
            Token data dictionary or None if file doesn't exist
        """
        try:
            if not self.token_file_path.exists():
                return None

            with open(self.token_file_path, encoding="utf-8") as f:
                return json.load(f)

        except Exception as e:
            logging.error(f"Error loading token data: {e}")
            return None

    def _save_token_data(self, token_data: dict[str, Any]) -> bool:
        """
        Save token data to file.

        Args:
            token_data: Token data to save

        Returns:
            True if successful, False otherwise
        """
        try:
            with open(self.token_file_path, "w", encoding="utf-8") as f:
                json.dump(token_data, f, indent=2)
            return True

        except Exception as e:
            logging.error(f"Error saving token data: {e}")
            return False


# Compatibility functions
def generate_dev_token() -> str:
    """
    Convenience function to generate a development token.

    Returns:
        Generated token
    """
    handler = CompatibleTokenHandler()
    return handler.generate_token()


def validate_dev_token(token: str) -> bool:
    """
    Convenience function to validate a development token.

    Args:
        token: Token to validate

    Returns:
        True if valid, False otherwise
    """
    handler = CompatibleTokenHandler()
    return handler.validate_token(token)
