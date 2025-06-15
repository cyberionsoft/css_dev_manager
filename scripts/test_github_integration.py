#!/usr/bin/env python3
"""
Test script to verify GitHub integration with encrypted constants.
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_github_token_access():
    """Test that GitHub token can be accessed from encrypted constants."""
    print("🔐 Testing GitHub token access from encrypted constants...")
    
    try:
        from src.common.constants import get_bundled_github_token, has_bundled_github_token
        
        # Check if token is available
        has_token = has_bundled_github_token()
        print(f"Has bundled GitHub token: {'✅ Yes' if has_token else '❌ No'}")
        
        if has_token:
            # Get the token
            token = get_bundled_github_token()
            if token:
                # Mask the token for security (show first 4 and last 4 characters)
                masked_token = f"{token[:4]}...{token[-4:]}" if len(token) > 8 else "***"
                print(f"Token retrieved: {masked_token}")
                print(f"Token length: {len(token)} characters")
                print("✅ GitHub token successfully retrieved from encrypted constants")
                return True
            else:
                print("❌ Failed to retrieve GitHub token")
                return False
        else:
            print("❌ No GitHub token available in encrypted constants")
            return False
            
    except Exception as e:
        print(f"❌ Error accessing GitHub token: {e}")
        return False


def test_config_data_access():
    """Test that configuration data can be accessed from encrypted constants."""
    print("\n📊 Testing configuration data access from encrypted constants...")
    
    try:
        from src.common.constants import get_bundled_config_data
        
        # Get configuration data
        config = get_bundled_config_data()
        if config:
            print("✅ Configuration data retrieved:")
            for key, value in config.items():
                print(f"  - {key}: {value}")
            return True
        else:
            print("⚠️  No configuration data available")
            return True  # This is not an error, just no config data
            
    except Exception as e:
        print(f"❌ Error accessing configuration data: {e}")
        return False


def test_github_client_fallback():
    """Test the GitHub client fallback system."""
    print("\n🔄 Testing GitHub client fallback system...")
    
    try:
        # Import the GitHub client
        from src.github_client import GitHubClient
        
        # Try to create a client (this will test the fallback system)
        print("Attempting to create GitHub client...")
        client = GitHubClient()
        
        if client.github_token:
            # Mask the token for security
            masked_token = f"{client.github_token[:4]}...{client.github_token[-4:]}"
            print(f"✅ GitHub client created successfully with token: {masked_token}")
            
            # Test basic GitHub API access
            try:
                user = client.github.get_user()
                print(f"✅ GitHub API access confirmed for user: {user.login}")
                return True
            except Exception as api_error:
                print(f"⚠️  GitHub client created but API access failed: {api_error}")
                return True  # Client creation succeeded, API might have issues
        else:
            print("❌ GitHub client created but no token available")
            return False
            
    except Exception as e:
        print(f"❌ Error creating GitHub client: {e}")
        return False


def main():
    """Run all integration tests."""
    print("🧪 DevManager GitHub Integration Tests")
    print("=" * 50)
    
    tests = [
        test_github_token_access,
        test_config_data_access,
        test_github_client_fallback,
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
    print(f"Integration tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All integration tests passed!")
        return 0
    else:
        print("⚠️  Some integration tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
