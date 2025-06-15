#!/usr/bin/env python3
"""
Compatible token generation utility for DevManager.

This script generates compatible tokens for DevAutomator communication.
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.token_handler_compatible import CompatibleTokenHandler


def main():
    """Main function for compatible token generation utility."""
    try:
        handler = CompatibleTokenHandler()
        
        # Generate new compatible token
        token = handler.generate_token()
        print("New compatible token generated:")
        print(f"  Token: {token}")
        print(f"  Expires in: 24 hours")
        print()
        print("Usage for DevAutomator:")
        print(f"  ../css_dev_automator/dist/dev_automator.exe --token {token}")
        print()
        print("⚠️  Keep this token secure and do not share it!")
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
