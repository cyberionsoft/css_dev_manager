"""
DevManager - Sophisticated installer and auto-updater for DevAutomator.

This is the main entry point that can be used to launch either the client
application or the build tools.
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def main():
    """Main entry point for DevManager."""
    # Use the new simplified main module
    from src.main import main as new_main
    sys.exit(new_main())


if __name__ == "__main__":
    main()
