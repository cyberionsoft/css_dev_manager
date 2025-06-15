# DevManager Encryption System

This document describes the encryption system used in DevManager to securely bundle sensitive data (like GitHub tokens) with the application while maintaining security.

## Overview

The encryption system allows sensitive configuration data to be encrypted and bundled with the DevManager application, eliminating the need for external configuration files while maintaining security. The system uses deterministic encryption, which means the same data will always produce the same encrypted output, allowing it to be bundled with the application.

## Components

### 1. Crypto Utils (`src/common/crypto_utils.py`)

Provides the core encryption/decryption functionality:

- **DeterministicCrypto**: Main encryption class that uses application-specific keys
- **Key Derivation**: Uses PBKDF2 with a fixed salt to create deterministic encryption keys
- **Fernet Encryption**: Uses symmetric encryption for fast and secure data protection

### 2. Encrypted Constants (`src/common/encrypted_constants.py`)

Contains the encrypted sensitive data and provides access methods:

- **ENCRYPTED_GITHUB_TOKEN**: Encrypted GitHub personal access token
- **ENCRYPTED_CONFIG_DATA**: Additional encrypted configuration data
- **ENCRYPTED_BACKUP_TOKENS**: Environment-specific backup tokens
- **EncryptedConstants**: Class providing cached access to decrypted data

### 3. Constants Integration (`src/common/constants.py`)

Provides convenient access functions:

- `get_bundled_github_token()`: Get GitHub token from encrypted constants
- `get_bundled_config_data()`: Get configuration data from encrypted constants
- `has_bundled_github_token()`: Check if GitHub token is available

### 4. Encryption Utility (`scripts/encrypt_constants.py`)

Developer tool for encrypting and updating constants:

- Command-line interface for encrypting tokens and config data
- Interactive mode for easy data entry
- Automatic updating of the encrypted_constants.py file

## Usage

### For Developers

#### 1. Encrypt a GitHub Token

```bash
# Command line mode
python scripts/encrypt_constants.py --github-token "ghp_your_token_here"

# Interactive mode
python scripts/encrypt_constants.py --interactive
```

#### 2. Encrypt Configuration Data

```bash
# From JSON file
python scripts/encrypt_constants.py --config-file "config.json"

# Interactive mode
python scripts/encrypt_constants.py --interactive
```

#### 3. Test the Encryption System

```bash
python scripts/test_encryption.py
```

### For Applications

#### 1. Access GitHub Token

```python
from src.common.constants import get_bundled_github_token

# Get token with automatic decryption
token = get_bundled_github_token()
if token:
    # Use the token
    github = Github(token)
```

#### 2. Access Configuration Data

```python
from src.common.constants import get_bundled_config_data

# Get additional config data
config = get_bundled_config_data()
if config:
    api_key = config.get('api_key')
    timeout = config.get('timeout', 30)
```

#### 3. Check Token Availability

```python
from src.common.constants import has_bundled_github_token

if has_bundled_github_token():
    print("GitHub token is available")
else:
    print("No GitHub token configured")
```

## Security Features

### 1. Deterministic Encryption

- Uses application-specific identifiers to derive encryption keys
- Same data always produces the same encrypted output
- Allows bundling encrypted data with the application

### 2. Key Derivation

- Uses PBKDF2 with 100,000 iterations for key strengthening
- Fixed salt ensures deterministic key generation
- 32-byte keys provide strong encryption

### 3. Fernet Encryption

- Symmetric encryption using AES 128 in CBC mode
- Built-in authentication prevents tampering
- Time-based tokens for additional security

### 4. Caching and Error Handling

- Decrypted values are cached to avoid repeated decryption
- Failed decryption attempts are tracked to prevent repeated failures
- Graceful fallback to other token sources

## Fallback System

The GitHub client uses a multi-tier fallback system for token access:

1. **Bundled Encrypted Constants** (Highest Priority)
   - Encrypted tokens bundled with the application
   - Always available, no external dependencies

2. **Secure Config Storage** (Medium Priority)
   - User-specific encrypted storage
   - Requires user configuration

3. **Environment Variables** (Lowest Priority)
   - Traditional environment variable approach
   - For development and testing

## File Structure

```
src/
├── common/
│   ├── constants.py           # Main constants with encryption access
│   ├── crypto_utils.py        # Core encryption utilities
│   └── encrypted_constants.py # Encrypted data storage
scripts/
├── encrypt_constants.py       # Encryption utility
└── test_encryption.py         # Test suite
docs/
└── ENCRYPTION_SYSTEM.md       # This documentation
```

## Best Practices

### 1. Token Management

- Use the encryption utility to update tokens
- Never commit unencrypted tokens to version control
- Regularly rotate GitHub tokens

### 2. Development Workflow

1. Generate GitHub token with appropriate permissions
2. Use encryption utility to encrypt and store token
3. Test the application with encrypted token
4. Build and distribute application with encrypted constants

### 3. Security Considerations

- The encryption is deterministic, so identical tokens will have identical encrypted values
- The encryption key is derived from application identifiers, making it specific to DevManager
- While secure for bundling, this is not suitable for storing user-specific secrets

## Troubleshooting

### Common Issues

1. **Decryption Fails**
   - Check that the encrypted constants file hasn't been corrupted
   - Verify the application identifier hasn't changed
   - Run the test script to verify encryption system

2. **No Token Available**
   - Use the encryption utility to set up encrypted constants
   - Check fallback sources (secure config, environment variables)
   - Verify the encrypted_constants.py file contains data

3. **Import Errors**
   - Ensure all required dependencies are installed
   - Check Python path configuration
   - Verify file structure is correct

### Testing

Run the test suite to verify the encryption system:

```bash
python scripts/test_encryption.py
```

This will test:
- Basic encryption/decryption
- Deterministic encryption across instances
- Encrypted constants access
- Integration with constants module
