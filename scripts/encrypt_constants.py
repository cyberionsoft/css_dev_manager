#!/usr/bin/env python3
"""
Utility script to encrypt sensitive constants for DevManager.

This script allows developers to encrypt sensitive data (like GitHub tokens)
and update the encrypted_constants.py file with the encrypted values.

Usage:
    python scripts/encrypt_constants.py --github-token "your_token_here"
    python scripts/encrypt_constants.py --config-file "path/to/config.json"
    python scripts/encrypt_constants.py --interactive
"""

import argparse
import json
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.common.crypto_utils import get_crypto


def encrypt_github_token(token: str) -> str:
    """
    Encrypt a GitHub token.
    
    Args:
        token: GitHub personal access token
        
    Returns:
        Encrypted token as base64 string
    """
    crypto = get_crypto()
    return crypto.encrypt_string(token)


def encrypt_config_data(config_data: dict) -> str:
    """
    Encrypt configuration data.
    
    Args:
        config_data: Dictionary of configuration data
        
    Returns:
        Encrypted config as base64 string
    """
    crypto = get_crypto()
    return crypto.encrypt_dict(config_data)


def update_constants_file(github_token: str = None, config_data: dict = None, backup_tokens: dict = None):
    """
    Update the encrypted_constants.py file with new encrypted values.
    
    Args:
        github_token: GitHub token to encrypt and store
        config_data: Configuration data to encrypt and store
        backup_tokens: Dictionary of backup tokens to encrypt and store
    """
    constants_file = project_root / "src" / "common" / "encrypted_constants.py"
    
    if not constants_file.exists():
        print(f"Error: Constants file not found at {constants_file}")
        return False
    
    # Read current file
    with open(constants_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Update GitHub token if provided
    if github_token:
        encrypted_token = encrypt_github_token(github_token)
        content = update_constant_value(content, "ENCRYPTED_GITHUB_TOKEN", encrypted_token)
        print("✅ GitHub token encrypted and updated")
    
    # Update config data if provided
    if config_data:
        encrypted_config = encrypt_config_data(config_data)
        content = update_constant_value(content, "ENCRYPTED_CONFIG_DATA", encrypted_config)
        print("✅ Configuration data encrypted and updated")
    
    # Update backup tokens if provided
    if backup_tokens:
        encrypted_backups = {}
        for env, token in backup_tokens.items():
            encrypted_backups[env] = encrypt_github_token(token)
        
        # Format the dictionary for the Python file
        backup_dict_str = "{\n"
        for env, encrypted_token in encrypted_backups.items():
            backup_dict_str += f'    "{env}": "{encrypted_token}",\n'
        backup_dict_str += "}"
        
        content = update_constant_dict(content, "ENCRYPTED_BACKUP_TOKENS", backup_dict_str)
        print("✅ Backup tokens encrypted and updated")
    
    # Write updated content
    with open(constants_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Constants file updated: {constants_file}")
    return True


def update_constant_value(content: str, constant_name: str, new_value: str) -> str:
    """
    Update a string constant value in the file content.
    
    Args:
        content: File content
        constant_name: Name of the constant to update
        new_value: New encrypted value
        
    Returns:
        Updated file content
    """
    import re
    
    # Pattern to match the constant assignment
    pattern = rf'^{constant_name}\s*=\s*"[^"]*"'
    replacement = f'{constant_name} = "{new_value}"'
    
    # Replace the constant value
    updated_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    
    return updated_content


def update_constant_dict(content: str, constant_name: str, new_dict_str: str) -> str:
    """
    Update a dictionary constant in the file content.
    
    Args:
        content: File content
        constant_name: Name of the constant to update
        new_dict_str: New dictionary string
        
    Returns:
        Updated file content
    """
    import re
    
    # Pattern to match the dictionary constant (multi-line)
    pattern = rf'^{constant_name}\s*=\s*\{{[^}}]*\}}'
    replacement = f'{constant_name} = {new_dict_str}'
    
    # Replace the constant value
    updated_content = re.sub(pattern, replacement, content, flags=re.MULTILINE | re.DOTALL)
    
    return updated_content


def interactive_mode():
    """Run in interactive mode to collect and encrypt sensitive data."""
    print("🔐 DevManager Constants Encryption Utility")
    print("=" * 50)
    
    # Collect GitHub token
    github_token = input("Enter GitHub token (or press Enter to skip): ").strip()
    if not github_token:
        github_token = None
    
    # Collect additional config data
    config_data = None
    add_config = input("Add additional configuration data? (y/N): ").strip().lower()
    if add_config == 'y':
        config_data = {}
        while True:
            key = input("Enter config key (or press Enter to finish): ").strip()
            if not key:
                break
            value = input(f"Enter value for '{key}': ").strip()
            config_data[key] = value
        
        if not config_data:
            config_data = None
    
    # Collect backup tokens
    backup_tokens = None
    add_backups = input("Add backup tokens for different environments? (y/N): ").strip().lower()
    if add_backups == 'y':
        backup_tokens = {}
        while True:
            env = input("Enter environment name (or press Enter to finish): ").strip()
            if not env:
                break
            token = input(f"Enter token for '{env}': ").strip()
            if token:
                backup_tokens[env] = token
        
        if not backup_tokens:
            backup_tokens = None
    
    # Update constants file
    if github_token or config_data or backup_tokens:
        print("\n🔄 Updating constants file...")
        success = update_constants_file(github_token, config_data, backup_tokens)
        if success:
            print("\n✅ All constants encrypted and updated successfully!")
        else:
            print("\n❌ Failed to update constants file")
    else:
        print("\n⚠️  No data provided, nothing to encrypt")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Encrypt constants for DevManager")
    parser.add_argument("--github-token", help="GitHub personal access token to encrypt")
    parser.add_argument("--config-file", help="JSON file containing configuration data to encrypt")
    parser.add_argument("--interactive", action="store_true", help="Run in interactive mode")
    parser.add_argument("--test", action="store_true", help="Test encryption/decryption without updating files")
    
    args = parser.parse_args()
    
    if args.test:
        # Test mode - encrypt and decrypt a test string
        test_string = "test_token_12345"
        crypto = get_crypto()
        encrypted = crypto.encrypt_string(test_string)
        decrypted = crypto.decrypt_string(encrypted)
        
        print(f"Original: {test_string}")
        print(f"Encrypted: {encrypted}")
        print(f"Decrypted: {decrypted}")
        print(f"Test {'PASSED' if test_string == decrypted else 'FAILED'}")
        return
    
    if args.interactive:
        interactive_mode()
        return
    
    # Command line mode
    github_token = args.github_token
    config_data = None
    
    if args.config_file:
        config_file = Path(args.config_file)
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                print(f"✅ Configuration loaded from {config_file}")
            except Exception as e:
                print(f"❌ Error loading config file: {e}")
                return
        else:
            print(f"❌ Config file not found: {config_file}")
            return
    
    if github_token or config_data:
        success = update_constants_file(github_token, config_data)
        if success:
            print("✅ Constants updated successfully!")
        else:
            print("❌ Failed to update constants")
    else:
        print("⚠️  No data provided. Use --interactive mode or provide --github-token")
        parser.print_help()


if __name__ == "__main__":
    main()
