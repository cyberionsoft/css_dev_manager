#!/usr/bin/env python3
"""
Token generation utility for DevManager.

This script generates authentication tokens for developer mode operations.
"""

import sys
import argparse
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.token_handler import TokenHandler


def main():
    """Main function for token generation utility."""
    parser = argparse.ArgumentParser(
        description="Generate authentication tokens for DevManager developer mode",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/generate_token.py                    # Generate a new token
  python scripts/generate_token.py --info             # Show current token info
  python scripts/generate_token.py --revoke           # Revoke current token
  python scripts/generate_token.py --validate TOKEN   # Validate a token
        """
    )
    
    parser.add_argument(
        '--info',
        action='store_true',
        help='Show information about the current token'
    )
    
    parser.add_argument(
        '--revoke',
        action='store_true',
        help='Revoke the current token'
    )
    
    parser.add_argument(
        '--validate',
        type=str,
        metavar='TOKEN',
        help='Validate a specific token'
    )
    
    args = parser.parse_args()
    
    try:
        handler = TokenHandler()
        
        if args.info:
            # Show token information
            info = handler.get_token_info()
            if info:
                print("Current Token Information:")
                print(f"  Created: {info['created_at']}")
                print(f"  Expires: {info['expires_at']}")
                print(f"  Used: {info['used']}")
                if info.get('used_at'):
                    print(f"  Used At: {info['used_at']}")
            else:
                print("No token found.")
                return 1
                
        elif args.revoke:
            # Revoke current token
            if handler.revoke_token():
                print("Token revoked successfully.")
            else:
                print("No token to revoke or revocation failed.")
                return 1
                
        elif args.validate:
            # Validate specific token
            if handler.validate_token(args.validate):
                print("Token is valid.")
            else:
                print("Token is invalid or expired.")
                return 1
                
        else:
            # Generate new token
            token = handler.generate_token()
            print("New token generated:")
            print(f"  Token: {token}")
            print(f"  Expires in: 24 hours")
            print()
            print("Usage:")
            print(f"  python src/main.py --token {token}")
            print()
            print("⚠️  Keep this token secure and do not share it!")
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
