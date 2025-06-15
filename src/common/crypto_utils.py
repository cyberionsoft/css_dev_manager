"""
Cryptographic utilities for DevManager.
Provides deterministic encryption/decryption for bundled sensitive data.
"""

import base64
import hashlib
import logging
from typing import Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class DeterministicCrypto:
    """
    Provides deterministic encryption/decryption using application-specific keys.
    This allows sensitive data to be encrypted and bundled with the application
    while still being secure.
    """
    
    def __init__(self, app_identifier: str = "DevManager-v0.1.0"):
        """
        Initialize the crypto utility.
        
        Args:
            app_identifier: Unique identifier for this application version
        """
        self.app_identifier = app_identifier
        self._key = self._derive_key()
        self._fernet = Fernet(self._key)
        
    def _derive_key(self) -> bytes:
        """
        Derive a deterministic encryption key from application identifier.
        
        Returns:
            32-byte encryption key
        """
        # Use a combination of app identifier and a salt
        # This creates a deterministic key that's the same across installations
        # but unique to this application
        salt = b"DevManager-Salt-2024"  # Fixed salt for deterministic key
        
        # Create key derivation function
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,  # Standard number of iterations
        )
        
        # Derive key from app identifier
        key = base64.urlsafe_b64encode(kdf.derive(self.app_identifier.encode()))
        return key
    
    def encrypt_string(self, plaintext: str) -> str:
        """
        Encrypt a string and return base64-encoded result.
        
        Args:
            plaintext: String to encrypt
            
        Returns:
            Base64-encoded encrypted string
        """
        try:
            encrypted_bytes = self._fernet.encrypt(plaintext.encode())
            return base64.urlsafe_b64encode(encrypted_bytes).decode()
        except Exception as e:
            logging.error(f"Encryption failed: {e}")
            raise
    
    def decrypt_string(self, encrypted_b64: str) -> Optional[str]:
        """
        Decrypt a base64-encoded encrypted string.
        
        Args:
            encrypted_b64: Base64-encoded encrypted string
            
        Returns:
            Decrypted string or None if decryption fails
        """
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_b64.encode())
            decrypted_bytes = self._fernet.decrypt(encrypted_bytes)
            return decrypted_bytes.decode()
        except Exception as e:
            logging.error(f"Decryption failed: {e}")
            return None
    
    def encrypt_dict(self, data: dict) -> str:
        """
        Encrypt a dictionary as JSON and return base64-encoded result.
        
        Args:
            data: Dictionary to encrypt
            
        Returns:
            Base64-encoded encrypted JSON string
        """
        import json
        json_str = json.dumps(data, separators=(',', ':'))  # Compact JSON
        return self.encrypt_string(json_str)
    
    def decrypt_dict(self, encrypted_b64: str) -> Optional[dict]:
        """
        Decrypt a base64-encoded encrypted JSON string to dictionary.
        
        Args:
            encrypted_b64: Base64-encoded encrypted JSON string
            
        Returns:
            Decrypted dictionary or None if decryption fails
        """
        import json
        json_str = self.decrypt_string(encrypted_b64)
        if json_str is None:
            return None
        
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logging.error(f"JSON decode failed: {e}")
            return None


# Global instance for consistent encryption across the application
_crypto_instance = None

def get_crypto() -> DeterministicCrypto:
    """Get global crypto instance."""
    global _crypto_instance
    if _crypto_instance is None:
        _crypto_instance = DeterministicCrypto()
    return _crypto_instance


def encrypt_for_constants(plaintext: str) -> str:
    """
    Convenience function to encrypt data for storage in constants.
    
    Args:
        plaintext: String to encrypt
        
    Returns:
        Base64-encoded encrypted string suitable for constants
    """
    return get_crypto().encrypt_string(plaintext)


def decrypt_from_constants(encrypted_b64: str) -> Optional[str]:
    """
    Convenience function to decrypt data from constants.
    
    Args:
        encrypted_b64: Base64-encoded encrypted string from constants
        
    Returns:
        Decrypted string or None if decryption fails
    """
    return get_crypto().decrypt_string(encrypted_b64)
