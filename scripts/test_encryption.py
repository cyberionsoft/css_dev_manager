#!/usr/bin/env python3
"""
Test script for the encryption system.
Verifies that encryption and decryption work correctly.
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_basic_encryption():
    """Test basic encryption and decryption."""
    print("🔐 Testing basic encryption...")
    
    from src.common.crypto_utils import get_crypto
    
    crypto = get_crypto()
    
    # Test string encryption
    test_string = "ghp_test_token_12345_abcdef"
    encrypted = crypto.encrypt_string(test_string)
    decrypted = crypto.decrypt_string(encrypted)
    
    print(f"Original: {test_string}")
    print(f"Encrypted: {encrypted[:50]}...")
    print(f"Decrypted: {decrypted}")
    print(f"String test: {'✅ PASSED' if test_string == decrypted else '❌ FAILED'}")
    
    # Test dictionary encryption
    test_dict = {
        "api_key": "test_api_key_123",
        "secret": "test_secret_456",
        "config": {"debug": True, "timeout": 30}
    }
    
    encrypted_dict = crypto.encrypt_dict(test_dict)
    decrypted_dict = crypto.decrypt_dict(encrypted_dict)
    
    print(f"\nOriginal dict: {test_dict}")
    print(f"Encrypted dict: {encrypted_dict[:50]}...")
    print(f"Decrypted dict: {decrypted_dict}")
    print(f"Dict test: {'✅ PASSED' if test_dict == decrypted_dict else '❌ FAILED'}")
    
    return test_string == decrypted and test_dict == decrypted_dict


def test_deterministic_encryption():
    """Test that encryption is deterministic across instances."""
    print("\n🔄 Testing deterministic encryption...")
    
    from src.common.crypto_utils import DeterministicCrypto
    
    # Create two separate instances
    crypto1 = DeterministicCrypto()
    crypto2 = DeterministicCrypto()
    
    test_string = "test_deterministic_token"
    
    # Encrypt with first instance
    encrypted1 = crypto1.encrypt_string(test_string)
    
    # Decrypt with second instance
    decrypted2 = crypto2.decrypt_string(encrypted1)
    
    print(f"Original: {test_string}")
    print(f"Encrypted by crypto1: {encrypted1[:50]}...")
    print(f"Decrypted by crypto2: {decrypted2}")
    print(f"Deterministic test: {'✅ PASSED' if test_string == decrypted2 else '❌ FAILED'}")
    
    return test_string == decrypted2


def test_encrypted_constants():
    """Test the encrypted constants system."""
    print("\n📁 Testing encrypted constants system...")
    
    try:
        from src.common.encrypted_constants import get_encrypted_constants
        
        constants = get_encrypted_constants()
        
        # Test GitHub token (will be None if not set)
        github_token = constants.get_github_token()
        print(f"GitHub token from constants: {'✅ Available' if github_token else '⚠️  Not set'}")
        
        # Test config data (will be None if not set)
        config_data = constants.get_config_data()
        print(f"Config data from constants: {'✅ Available' if config_data else '⚠️  Not set'}")
        
        # Test has_github_token method
        has_token = constants.has_github_token()
        print(f"Has GitHub token: {'✅ Yes' if has_token else '⚠️  No'}")
        
        print("✅ Encrypted constants system working")
        return True
        
    except Exception as e:
        print(f"❌ Encrypted constants test failed: {e}")
        return False


def test_constants_integration():
    """Test integration with constants.py."""
    print("\n🔗 Testing constants integration...")
    
    try:
        from src.common.constants import (
            get_bundled_github_token,
            get_bundled_config_data,
            has_bundled_github_token
        )
        
        # Test functions
        github_token = get_bundled_github_token()
        config_data = get_bundled_config_data()
        has_token = has_bundled_github_token()
        
        print(f"Bundled GitHub token: {'✅ Available' if github_token else '⚠️  Not set'}")
        print(f"Bundled config data: {'✅ Available' if config_data else '⚠️  Not set'}")
        print(f"Has bundled token: {'✅ Yes' if has_token else '⚠️  No'}")
        
        print("✅ Constants integration working")
        return True
        
    except Exception as e:
        print(f"❌ Constants integration test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🧪 DevManager Encryption System Tests")
    print("=" * 50)
    
    tests = [
        test_basic_encryption,
        test_deterministic_encryption,
        test_encrypted_constants,
        test_constants_integration,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
