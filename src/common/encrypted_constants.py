"""
Encrypted constants for DevManager.
Contains sensitive data encrypted and bundled with the application.

IMPORTANT: This file contains encrypted sensitive data. The encryption is deterministic
based on the application identifier, allowing the data to be bundled with the app
while maintaining security.

To update encrypted values, use the scripts/encrypt_constants.py utility.
"""

import logging
from typing import Optional

try:
    from .crypto_utils import decrypt_from_constants
except ImportError:
    try:
        from src.common.crypto_utils import decrypt_from_constants
    except ImportError:
        from crypto_utils import decrypt_from_constants


# Encrypted sensitive data
# These values are encrypted using the DeterministicCrypto class
# To update these values, use the scripts/encrypt_constants.py script

# GitHub Token (encrypted)
# Original value should be set using the encryption script
ENCRYPTED_GITHUB_TOKEN = "Z0FBQUFBQm9Ucnk4R2xQUWhMYnJQRDZESi11R0RwXy10dkhDTGNqUV96QllnZ1pCZXBDbTIzYkJBYk1UMk9lWUNfd2lCMzFUM3A2UUc0dUxIQ0wtckY1VnQ5cEtqanhqbTZiZE9zUnd5SkNfMTYyQmdvSDdTUWtnQjIyNW15Wk95dU9QOE1BeHFULW8="

# Additional encrypted configuration data
ENCRYPTED_CONFIG_DATA = "Z0FBQUFBQm9UcnpkYUM4QUdwdGlUMzFSYnZJZTF1UHFoY3lzcUNRay1yLU5BdDV5REZSX2Z1RXB0ZkVWMG1LeDFrYXItVnYyeXFLcjRjMXNOWGhhdzdLYm5wSXBDNkg1N0JMcmdyb1lnSHBWY2dvd3BwRzNLSDJEbWt2ZnhkaWRSazFETGEwbFB0Zjh5c21oNVBBdm5Rd3hvdXhwMmFaZjd0MnlmVUhXV3lNYndwVHJSZy05aUdLQXNFSVUxRlpQamc2eV93U0kwM2xQSzdaWXZsUW5WWTJxd1I0U2RkWDFldTBpVWJTTTIwTHNJdGhxa29uWTc1UVZFUkxXSDBmU1hmV1VXUjNSWEszcWlfSE5MOXdqVE9iLUVOVi1pS09xQnc9PQ=="

# Backup encrypted tokens (if needed for different environments)
ENCRYPTED_BACKUP_TOKENS = {
    # "environment_name": "encrypted_token_value"
}


class EncryptedConstants:
    """
    Provides access to encrypted constants with caching and fallback mechanisms.
    """
    
    def __init__(self):
        """Initialize the encrypted constants manager."""
        self._cache = {}
        self._decryption_attempted = set()
    
    def get_github_token(self) -> Optional[str]:
        """
        Get the GitHub token from encrypted constants.
        
        Returns:
            Decrypted GitHub token or None if not available/decryption fails
        """
        cache_key = "github_token"
        
        # Return cached value if available
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Avoid repeated decryption attempts for failed keys
        if cache_key in self._decryption_attempted:
            return None
        
        # Attempt decryption
        if ENCRYPTED_GITHUB_TOKEN:
            try:
                token = decrypt_from_constants(ENCRYPTED_GITHUB_TOKEN)
                if token:
                    self._cache[cache_key] = token
                    logging.info("GitHub token successfully decrypted from constants")
                    return token
                else:
                    logging.warning("GitHub token decryption failed")
            except Exception as e:
                logging.error(f"Error decrypting GitHub token: {e}")
        else:
            logging.info("No encrypted GitHub token found in constants")
        
        # Mark as attempted to avoid repeated failures
        self._decryption_attempted.add(cache_key)
        return None
    
    def get_config_data(self) -> Optional[dict]:
        """
        Get additional configuration data from encrypted constants.
        
        Returns:
            Decrypted configuration dictionary or None if not available
        """
        cache_key = "config_data"
        
        # Return cached value if available
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Avoid repeated decryption attempts for failed keys
        if cache_key in self._decryption_attempted:
            return None
        
        # Attempt decryption
        if ENCRYPTED_CONFIG_DATA:
            try:
                try:
                    from .crypto_utils import get_crypto
                except ImportError:
                    try:
                        from src.common.crypto_utils import get_crypto
                    except ImportError:
                        from crypto_utils import get_crypto

                crypto = get_crypto()
                config_data = crypto.decrypt_dict(ENCRYPTED_CONFIG_DATA)
                if config_data:
                    self._cache[cache_key] = config_data
                    logging.info("Configuration data successfully decrypted from constants")
                    return config_data
                else:
                    logging.warning("Configuration data decryption failed")
            except Exception as e:
                logging.error(f"Error decrypting configuration data: {e}")
        else:
            logging.debug("No encrypted configuration data found in constants")
        
        # Mark as attempted to avoid repeated failures
        self._decryption_attempted.add(cache_key)
        return None
    
    def get_backup_token(self, environment: str) -> Optional[str]:
        """
        Get a backup token for a specific environment.
        
        Args:
            environment: Environment name
            
        Returns:
            Decrypted backup token or None if not available
        """
        cache_key = f"backup_token_{environment}"
        
        # Return cached value if available
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Avoid repeated decryption attempts for failed keys
        if cache_key in self._decryption_attempted:
            return None
        
        # Attempt decryption
        encrypted_token = ENCRYPTED_BACKUP_TOKENS.get(environment)
        if encrypted_token:
            try:
                token = decrypt_from_constants(encrypted_token)
                if token:
                    self._cache[cache_key] = token
                    logging.info(f"Backup token for {environment} successfully decrypted")
                    return token
                else:
                    logging.warning(f"Backup token decryption failed for {environment}")
            except Exception as e:
                logging.error(f"Error decrypting backup token for {environment}: {e}")
        else:
            logging.debug(f"No backup token found for environment: {environment}")
        
        # Mark as attempted to avoid repeated failures
        self._decryption_attempted.add(cache_key)
        return None
    
    def has_github_token(self) -> bool:
        """
        Check if a GitHub token is available in encrypted constants.
        
        Returns:
            True if token is available and can be decrypted
        """
        return self.get_github_token() is not None
    
    def clear_cache(self):
        """Clear the decryption cache."""
        self._cache.clear()
        self._decryption_attempted.clear()
        logging.debug("Encrypted constants cache cleared")


# Global instance
_encrypted_constants = None

def get_encrypted_constants() -> EncryptedConstants:
    """Get global encrypted constants instance."""
    global _encrypted_constants
    if _encrypted_constants is None:
        _encrypted_constants = EncryptedConstants()
    return _encrypted_constants


# Convenience functions
def get_github_token_from_constants() -> Optional[str]:
    """Get GitHub token from encrypted constants."""
    return get_encrypted_constants().get_github_token()


def get_config_from_constants() -> Optional[dict]:
    """Get configuration data from encrypted constants."""
    return get_encrypted_constants().get_config_data()


def has_encrypted_github_token() -> bool:
    """Check if encrypted GitHub token is available."""
    return get_encrypted_constants().has_github_token()
