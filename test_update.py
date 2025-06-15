#!/usr/bin/env python3
"""
Test script to verify the DevManager update mechanism is working.
"""

import sys
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from updater import DevManagerUpdater

def test_update_mechanism():
    """Test the DevManager update mechanism."""
    print("🧪 Testing DevManager update mechanism...")
    
    # Create updater
    updater = DevManagerUpdater()
    
    # Test getting latest version
    print("📋 Getting latest version...")
    latest_version = updater._get_latest_version()
    if latest_version:
        print(f"✅ Latest version: {latest_version}")
    else:
        print("❌ Failed to get latest version")
        return False
    
    # Test downloading release
    print("📥 Testing download...")
    with tempfile.TemporaryDirectory() as temp_dir:
        downloaded_file = updater._download_release(latest_version, Path(temp_dir))
        if downloaded_file and downloaded_file.exists():
            print(f"✅ Download successful: {downloaded_file}")
            print(f"📊 File size: {downloaded_file.stat().st_size} bytes")
            return True
        else:
            print("❌ Download failed")
            return False

if __name__ == "__main__":
    success = test_update_mechanism()
    if success:
        print("\n🎉 Update mechanism test PASSED!")
        sys.exit(0)
    else:
        print("\n💥 Update mechanism test FAILED!")
        sys.exit(1)
