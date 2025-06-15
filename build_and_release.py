#!/usr/bin/env python3
"""
Build and release script for DevManager v0.1.3
"""

import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    """Build and release DevManager v0.1.3"""
    try:
        # Import after adding to path
        from github_client import GitHubClient
        from common.constants import VERSION
        
        print(f"🚀 Building and releasing DevManager v{VERSION}")
        print("=" * 60)
        
        # Initialize GitHub client
        print("📡 Initializing GitHub client...")
        github_client = GitHubClient()
        
        # Build and upload DevManager
        print("🏗️  Building and uploading DevManager...")
        success = github_client.build_and_upload_devmanager()
        
        if success:
            print(f"✅ DevManager v{VERSION} built and released successfully!")
            print(f"🔗 Release URL: https://github.com/cyberionsoft/css_dev_manager/releases/tag/v{VERSION}")
            return 0
        else:
            print("❌ Failed to build and release DevManager")
            return 1
            
    except Exception as e:
        print(f"💥 Error: {e}")
        logging.error(f"Build and release failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
