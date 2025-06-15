"""
Token handler for DevManager authentication and authorization.
Uses JWT tokens with cryptographic signing for enhanced security.
"""

import json
import logging
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

try:
    from .common.constants import CONFIG_DIR, TOKEN_EXPIRY_HOURS, TOKEN_FILE
    from .common.utils import ensure_directory
except ImportError:
    import sys

    sys.path.insert(0, str(Path(__file__).parent))
    from common.constants import CONFIG_DIR, TOKEN_EXPIRY_HOURS, TOKEN_FILE
    from common.utils import ensure_directory


class TokenHandler:
    """
    Handles token generation, validation, and management for DevManager.
    Uses JWT tokens with RSA signing for enhanced security.
    """

    def __init__(self):
        """Initialize the token handler."""
        self.token_file_path = CONFIG_DIR / TOKEN_FILE
        self.key_file_path = CONFIG_DIR / "private_key.pem"
        self.public_key_file_path = CONFIG_DIR / "public_key.pem"
        ensure_directory(CONFIG_DIR)
        self._ensure_keys()

    def _ensure_keys(self) -> None:
        """Ensure RSA key pair exists for JWT signing."""
        if not self.key_file_path.exists() or not self.public_key_file_path.exists():
            # Generate new RSA key pair
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
            )

            # Save private key
            private_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )
            with open(self.key_file_path, "wb") as f:
                f.write(private_pem)

            # Save public key
            public_key = private_key.public_key()
            public_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
            with open(self.public_key_file_path, "wb") as f:
                f.write(public_pem)

            logging.info("Generated new RSA key pair for JWT signing")

    def _get_private_key(self):
        """Load the private key for signing."""
        with open(self.key_file_path, "rb") as f:
            return serialization.load_pem_private_key(f.read(), password=None)

    def _get_public_key(self):
        """Load the public key for verification."""
        with open(self.public_key_file_path, "rb") as f:
            return serialization.load_pem_public_key(f.read())

    def generate_token(self) -> str:
        """
        Generate a new secure JWT token.

        Returns:
            Generated JWT token string
        """
        now = datetime.now(timezone.utc)
        payload = {
            "iss": "DevManager",  # Issuer
            "sub": "dev_operations",  # Subject
            "iat": now,  # Issued at
            "exp": now + timedelta(hours=TOKEN_EXPIRY_HOURS),  # Expiration
            "jti": secrets.token_urlsafe(16),  # JWT ID (unique identifier)
            "purpose": "dev_manager_operations",
        }

        private_key = self._get_private_key()
        token = jwt.encode(payload, private_key, algorithm="RS256")

        # Store token metadata for tracking
        token_data = {
            "jti": payload["jti"],
            "created_at": now.isoformat(),
            "expires_at": payload["exp"].isoformat(),
            "used": False,
        }

        self._save_token_data(token_data)
        logging.info(f"Generated new JWT token (expires in {TOKEN_EXPIRY_HOURS} hours)")

        return token

    def validate_token(self, token: str) -> bool:
        """
        Validate a JWT token.

        Args:
            token: JWT token to validate

        Returns:
            True if token is valid, False otherwise
        """
        try:
            # Decode and verify JWT token
            public_key = self._get_public_key()
            payload = jwt.decode(token, public_key, algorithms=["RS256"])

            # Verify token purpose
            if payload.get("purpose") != "dev_manager_operations":
                logging.warning("Invalid token purpose")
                return False

            # Check if token has been used (one-time use)
            jti = payload.get("jti")
            if jti:
                token_data = self._load_token_data()
                if token_data and token_data.get("jti") == jti:
                    if token_data.get("used", False):
                        logging.warning("Token has already been used")
                        return False

            logging.info("JWT token validation successful")
            return True

        except jwt.ExpiredSignatureError:
            logging.warning("Token has expired")
            return False
        except jwt.InvalidTokenError as e:
            logging.warning(f"Invalid token: {e}")
            return False

        except Exception as e:
            logging.error(f"Token validation error: {e}")
            return False

    def mark_token_used(self, token: str) -> bool:
        """
        Mark a JWT token as used.

        Args:
            token: JWT token to mark as used

        Returns:
            True if successful, False otherwise
        """
        try:
            # Decode token to get JTI
            public_key = self._get_public_key()
            payload = jwt.decode(token, public_key, algorithms=["RS256"])
            jti = payload.get("jti")

            if jti:
                token_data = self._load_token_data()
                if token_data and token_data.get("jti") == jti:
                    token_data["used"] = True
                    token_data["used_at"] = datetime.now(timezone.utc).isoformat()
                    self._save_token_data(token_data)
                    logging.info("JWT token marked as used")
                    return True

            return False

        except Exception as e:
            logging.error(f"Error marking token as used: {e}")
            return False

    def _decode_token(self, token: str) -> dict:
        """
        Decode JWT token and return payload.

        Args:
            token: JWT token to decode

        Returns:
            Token payload dictionary
        """
        try:
            public_key = self._get_public_key()
            payload = jwt.decode(token, public_key, algorithms=["RS256"])
            return payload
        except Exception as e:
            logging.error(f"Token decoding failed: {e}")
            return {}

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
                "jti": token_data.get("jti"),
                "created_at": token_data.get("created_at"),
                "expires_at": token_data.get("expires_at"),
                "used": token_data.get("used", False),
                "used_at": token_data.get("used_at"),
            }

            return info

        except Exception as e:
            logging.error(f"Error getting token info: {e}")
            return None

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


def generate_dev_token() -> str:
    """
    Convenience function to generate a development token.

    Returns:
        Generated token
    """
    handler = TokenHandler()
    return handler.generate_token()


def validate_dev_token(token: str) -> bool:
    """
    Convenience function to validate a development token.

    Args:
        token: Token to validate

    Returns:
        True if valid, False otherwise
    """
    handler = TokenHandler()
    return handler.validate_token(token)
