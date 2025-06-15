#!/usr/bin/env python3
"""
Build script for DevAutomator using DevManager's build system.
"""

import argparse
import logging
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.builder.build_manager import BuildManager


def main():
    """Main entry point for the build script."""
    parser = argparse.ArgumentParser(
        description="Build DevAutomator using DevManager's build system"
    )
    
    parser.add_argument(
        '--devautomator-path', '-p',
        required=True,
        type=Path,
        help='Path to DevAutomator project directory'
    )
    
    parser.add_argument(
        '--version', '-v',
        required=True,
        help='Version to build'
    )
    
    parser.add_argument(
        '--github-token', '-t',
        help='GitHub personal access token (or set GITHUB_TOKEN env var)'
    )
    
    parser.add_argument(
        '--platforms',
        nargs='+',
        choices=['windows', 'darwin', 'linux'],
        default=['windows'],
        help='Platforms to build for (default: windows only)'
    )
    
    parser.add_argument(
        '--release-notes', '-n',
        default='',
        help='Release notes for this version'
    )
    
    parser.add_argument(
        '--prerelease',
        action='store_true',
        help='Mark as prerelease'
    )
    
    parser.add_argument(
        '--build-only',
        action='store_true',
        help='Only build, do not create GitHub release'
    )
    
    parser.add_argument(
        '--clean',
        action='store_true',
        default=True,
        help='Clean build directories before building'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    
    args = parser.parse_args()
    
    # Set up logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('build_devautomator.log')
        ]
    )
    
    try:
        # Get GitHub token from environment if not provided
        github_token = args.github_token or os.environ.get('GITHUB_TOKEN')
        
        if not args.build_only and not github_token:
            logging.warning("No GitHub token provided, will only build (no release)")
            build_only = True
        else:
            build_only = args.build_only
        
        # Initialize build manager
        build_manager = BuildManager(args.devautomator_path, github_token)
        
        if build_only:
            # Only build
            logging.info("Building DevAutomator (build-only mode)")
            build_results = build_manager.build_all_platforms(
                args.version,
                args.clean,
                args.platforms
            )
            
            if build_results:
                print(f"✅ Build completed successfully for {len(build_results)} platforms:")
                for platform, path in build_results.items():
                    print(f"   {platform}: {path}")
            else:
                print("❌ Build failed")
                sys.exit(1)
        else:
            # Full release process
            logging.info("Starting full DevAutomator release process")
            success = build_manager.full_release_process(
                args.version,
                args.release_notes,
                args.platforms,
                args.prerelease,
                args.clean
            )
            
            if success:
                print(f"✅ DevAutomator {args.version} released successfully!")
            else:
                print("❌ Release process failed")
                sys.exit(1)
                
    except KeyboardInterrupt:
        print("\n❌ Build cancelled by user")
        sys.exit(130)
    except Exception as e:
        logging.error(f"Build script failed: {e}", exc_info=True)
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
