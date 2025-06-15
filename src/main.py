"""
Main entry point for DevManager.

This application can be started in two ways:
1. Simple start (double-click) - GUI mode with auto-update checks
2. Token start (terminal with token) - Developer mode for building and releasing
"""

import argparse
import logging
import sys
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available, continue without it
    pass

# Handle both relative and absolute imports for PyInstaller compatibility
try:
    # Try relative imports first (for normal Python execution)
    from .common.constants import APP_NAME, CONFIG_DIR, LOG_FILE, LOG_FORMAT, LOG_LEVEL, VERSION
    from .common.utils import ensure_directory
    from .github_client import GitHubClient
    from .gui import (
        show_build_progress_dialog,
        show_error_dialog,
        show_token_mode_dialog,
    )
    from .github_settings_dialog import show_github_settings_dialog
    from .token_handler_compatible import CompatibleTokenHandler as TokenHandler
    from .updater import DevAutomatorUpdater, DevManagerUpdater
    from .installer import FirstRunInstaller, show_install_dialog
except ImportError:
    try:
        # Try absolute imports with src prefix (for PyInstaller)
        from src.common.constants import APP_NAME, CONFIG_DIR, LOG_FILE, LOG_FORMAT, LOG_LEVEL, VERSION
        from src.common.utils import ensure_directory
        from src.github_client import GitHubClient
        from src.gui import (
            show_build_progress_dialog,
            show_error_dialog,
            show_token_mode_dialog,
        )
        from src.github_settings_dialog import show_github_settings_dialog
        from src.token_handler_compatible import CompatibleTokenHandler as TokenHandler
        from src.updater import DevAutomatorUpdater, DevManagerUpdater
        from src.installer import FirstRunInstaller, show_install_dialog
    except ImportError:
        # Final fallback - add src directory to path and import without prefix
        src_path = Path(__file__).parent
        if str(src_path) not in sys.path:
            sys.path.insert(0, str(src_path))

        from common.constants import APP_NAME, CONFIG_DIR, LOG_FILE, LOG_FORMAT, LOG_LEVEL, VERSION
        from common.utils import ensure_directory
        from github_client import GitHubClient
        from gui import (
            show_build_progress_dialog,
            show_error_dialog,
            show_token_mode_dialog,
        )
        from github_settings_dialog import show_github_settings_dialog
        from token_handler_compatible import CompatibleTokenHandler as TokenHandler
        from updater import DevAutomatorUpdater, DevManagerUpdater
        from installer import FirstRunInstaller, show_install_dialog


def setup_logging(debug: bool = False) -> None:
    """
    Set up logging configuration.

    Args:
        debug: Enable debug logging
    """
    ensure_directory(CONFIG_DIR)
    log_file_path = CONFIG_DIR / LOG_FILE

    level = logging.DEBUG if debug else getattr(logging, LOG_LEVEL.upper())

    logging.basicConfig(
        level=level,
        format=LOG_FORMAT,
        handlers=[
            logging.FileHandler(log_file_path, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments.

    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description=f"{APP_NAME} - Development Environment Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--token", type=str, help="Authentication token for developer mode"
    )

    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    parser.add_argument("--test-encryption", action="store_true", help="Test encryption system and exit")

    parser.add_argument("--version", action="version", version=f"{APP_NAME} {VERSION}")

    return parser.parse_args()


def token_mode_menu() -> str:
    """
    Display token mode menu and get user choice.
    Uses GUI if available, falls back to console.

    Returns:
        User's choice ('devmanager', 'devautomator', or 'exit')
    """
    try:
        # Try to use GUI first
        selected = show_token_mode_dialog()
        if selected:
            return selected
        else:
            return "exit"
    except Exception as e:
        logging.warning(f"GUI not available, falling back to console: {e}")

        # Fallback to console interface with enhanced UI
        print(f"\n{APP_NAME} v{VERSION} - Developer Mode")
        print("=" * 60)
        print("🔧 Development Operations Available:")
        print()
        print("  1. 🏗️  Build and Upload DevManager")
        print("     └─ Compile, package, and release DevManager to GitHub")
        print()
        print("  2. 🏗️  Build and Upload DevAutomator")
        print("     └─ Compile, package, and release DevAutomator to GitHub")
        print()
        print("  3. ⚙️  GitHub Settings")
        print("     └─ Configure GitHub token and settings")
        print()
        print("  4. 🚪 Exit")
        print("     └─ Return to normal operation")
        print()
        print("=" * 60)

        while True:
            choice = input("Select option (1-4): ").strip()
            if choice == "1":
                return "devmanager"
            elif choice == "2":
                return "devautomator"
            elif choice == "3":
                return "github_settings"
            elif choice == "4":
                return "exit"
            print("❌ Invalid choice. Please select 1, 2, 3, or 4.")


def handle_token_mode(token: str) -> int:
    """
    Handle token-based developer mode.

    Args:
        token: Authentication token

    Returns:
        Exit code
    """
    # Validate token
    token_handler = TokenHandler()
    if not token_handler.validate_token(token):
        error_msg = "Invalid or expired token"
        try:
            show_error_dialog("Authentication Error", error_msg)
        except Exception:
            print(f"ERROR: {error_msg}")
        return 1

    # Mark token as used
    token_handler.mark_token_used(token)

    try:
        while True:
            choice = token_mode_menu()

            if choice == "devmanager":
                # Build and upload DevManager
                try:
                    github_client = GitHubClient()
                    success = show_build_progress_dialog("devmanager", github_client)
                    if not success:
                        return 1
                except Exception as e:
                    # Fallback to console with enhanced progress reporting
                    print(f"\n🏗️  Building and Uploading DevManager")
                    print("=" * 50)
                    print("⏳ Initializing GitHub client...")

                    try:
                        github_client = GitHubClient()
                        print("✅ GitHub connection established")
                        print("🔨 Starting build process...")

                        success = github_client.build_and_release_devmanager()
                        if success:
                            print("✅ DevManager build and upload completed successfully!")
                            print("🎉 Release is now available on GitHub")
                        else:
                            print("❌ DevManager build and upload failed!")
                            return 1
                    except Exception as build_error:
                        print(f"❌ Build failed: {build_error}")
                        return 1

            elif choice == "devautomator":
                # Build and upload DevAutomator
                try:
                    github_client = GitHubClient()
                    success = show_build_progress_dialog("devautomator", github_client)
                    if not success:
                        return 1
                except Exception as e:
                    # Fallback to console with enhanced progress reporting
                    print(f"\n🏗️  Building and Uploading DevAutomator")
                    print("=" * 50)
                    print("⏳ Initializing GitHub client...")

                    try:
                        github_client = GitHubClient()
                        print("✅ GitHub connection established")
                        print("🔨 Starting build process...")

                        success = github_client.build_and_release_devautomator()
                        if success:
                            print("✅ DevAutomator build and upload completed successfully!")
                            print("🎉 Release is now available on GitHub")
                        else:
                            print("❌ DevAutomator build and upload failed!")
                            return 1
                    except Exception as build_error:
                        print(f"❌ Build failed: {build_error}")
                        return 1

            elif choice == "github_settings":
                # GitHub Settings
                try:
                    # Import with fallback handling
                    try:
                        from .github_settings_dialog import show_github_settings_dialog
                    except ImportError:
                        try:
                            from src.github_settings_dialog import show_github_settings_dialog
                        except ImportError:
                            from github_settings_dialog import show_github_settings_dialog

                    show_github_settings_dialog()
                except Exception as e:
                    # Fallback to console GitHub settings
                    print(f"\n⚙️  GitHub Settings")
                    print("=" * 50)
                    print("⚠️  GUI not available, using console mode")
                    print(f"Error: {e}")
                    print("\nTo configure GitHub token manually:")
                    print("1. Set GITHUB_TOKEN environment variable")
                    print("2. Or use the GUI mode when available")

            elif choice == "exit":
                print("Exiting...")
                return 0

            # Ask if user wants to continue (console mode only)
            try:
                # If GUI is available, it will handle continuation
                continue_choice = (
                    input("\nDo you want to perform another operation? (y/n): ")
                    .strip()
                    .lower()
                )
                if continue_choice not in ["y", "yes"]:
                    break
            except EOFError:
                # GUI mode - continue the loop
                continue

        return 0

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 130
    except Exception as e:
        logging.error(f"Error in token mode: {e}", exc_info=True)
        error_msg = f"Unexpected error: {e}"
        try:
            show_error_dialog("Error", error_msg)
        except Exception:
            print(f"ERROR: {error_msg}")
        return 1


def handle_simple_mode() -> int:
    """
    Handle simple mode with auto-update functionality using GUI.

    Flow:
    1. Check for DevManager updates -> if found, download, install, restart and exit
    2. Check for DevAutomator updates -> if found, stop DevAutomator, update, start with token and exit
    3. If no updates, start DevAutomator with token and exit

    Returns:
        Exit code
    """
    try:
        # Import GUI function with fallback handling
        try:
            from .gui import show_normal_mode_window
        except ImportError:
            try:
                from src.gui import show_normal_mode_window
            except ImportError:
                from gui import show_normal_mode_window

        # Show GUI and perform operations
        success = show_normal_mode_window()

        return 0 if success else 1

    except Exception as e:
        logging.error(f"Error in simple mode: {e}", exc_info=True)

        # Fallback to terminal mode if GUI fails
        print(f"\n❌ GUI Error: {e}")
        print("Falling back to terminal mode...")

        return handle_simple_mode_terminal()


def handle_simple_mode_terminal() -> int:
    """
    Handle simple mode with terminal interface (fallback).

    Returns:
        Exit code
    """
    try:
        # Import with fallback handling
        try:
            from .updater import DevAutomatorUpdater, DevManagerUpdater
            from .token_handler_compatible import CompatibleTokenHandler
        except ImportError:
            try:
                from src.updater import DevAutomatorUpdater, DevManagerUpdater
                from src.token_handler_compatible import CompatibleTokenHandler
            except ImportError:
                from updater import DevAutomatorUpdater, DevManagerUpdater
                from token_handler_compatible import CompatibleTokenHandler

        # Enhanced terminal UI with progress reporting
        print(f"\n{APP_NAME} v{VERSION} - Auto-Update Mode")
        print("=" * 60)

        # Step 1: Check for DevManager updates first
        print("\n[1/3] Checking for DevManager updates...")
        print("    ⏳ Connecting to GitHub...")
        devmanager_updater = DevManagerUpdater()

        if devmanager_updater.check_for_updates():
            print("    ✅ DevManager update available!")
            print("    📥 Downloading and installing update...")

            # Show progress for update
            print("    ⏳ Downloading update package...")
            if devmanager_updater.download_and_install_update():
                print("    ✅ DevManager updated successfully!")
                print("    🔄 The update script will restart the application.")
                print("\n" + "=" * 60)
                print("DevManager update completed. Restarting...")
                # The self-update script will handle restarting
                return 0
            else:
                print("    ❌ Failed to update DevManager.")
                print("    ⚠️  Continuing with current version...")
        else:
            print("    ✅ DevManager is up to date.")

        # Step 2: Check for DevAutomator updates or initial installation
        print("\n[2/3] Checking for DevAutomator...")
        print("    ⏳ Connecting to GitHub...")
        devautomator_updater = DevAutomatorUpdater()

        # Check if DevAutomator is installed
        if not devautomator_updater.is_devautomator_installed():
            print("    📥 DevAutomator not found - downloading initial installation...")
            print("    🛑 Stopping any existing DevAutomator processes...")
            devautomator_updater.stop_devautomator()

            # Download and install for the first time
            if devautomator_updater.download_and_install_update():
                print("    ✅ DevAutomator installed successfully.")
            else:
                print("    ❌ Failed to install DevAutomator")
                return 1
        elif devautomator_updater.check_for_updates():
            print("    ✅ DevAutomator update available!")
            print("    🛑 Stopping existing DevAutomator processes...")

            # Kill existing DevAutomator process if running
            devautomator_updater.stop_devautomator()

            # Download and install update
            print("    📥 Downloading and installing update...")
            if devautomator_updater.download_and_install_update():
                print("    ✅ DevAutomator updated successfully.")
            else:
                print("    ❌ Failed to update DevAutomator")
                return 1
        else:
            print("    ✅ DevAutomator is up to date.")

        # Step 3: Start DevAutomator with token and exit
        print("\n[3/3] Starting DevAutomator...")
        print("    🔑 Generating secure authentication token...")

        # Generate token for DevAutomator (use compatible token handler)
        token_handler = CompatibleTokenHandler()
        token = token_handler.generate_token()

        # Start DevAutomator with token
        print("    🚀 Launching DevAutomator with token...")
        if devautomator_updater.start_devautomator_with_token(token):
            print("    ✅ DevAutomator started successfully!")
            print("\n" + "=" * 60)
            print("All operations completed. Exiting DevManager...")
            return 0
        else:
            print("    ❌ Failed to start DevAutomator")
            return 1

    except Exception as e:
        logging.error(f"Error in terminal mode: {e}", exc_info=True)
        print(f"\n❌ ERROR: {e}")
        return 1


def test_encryption_system() -> int:
    """
    Test the encryption system and exit.

    Returns:
        Exit code (0 if successful, 1 if failed)
    """
    print("🔐 Testing DevManager Encryption System")
    print("=" * 50)

    try:
        # Test importing crypto modules
        print("📦 Importing crypto modules...")
        try:
            from .common.crypto_utils import get_crypto
            from .common.encrypted_constants import get_github_token_from_constants, get_config_from_constants
            from .common.constants import get_bundled_github_token, has_bundled_github_token
        except ImportError:
            try:
                from src.common.crypto_utils import get_crypto
                from src.common.encrypted_constants import get_github_token_from_constants, get_config_from_constants
                from src.common.constants import get_bundled_github_token, has_bundled_github_token
            except ImportError:
                from common.crypto_utils import get_crypto
                from common.encrypted_constants import get_github_token_from_constants, get_config_from_constants
                from common.constants import get_bundled_github_token, has_bundled_github_token

        print("✅ Successfully imported encryption modules")

        # Test crypto functionality
        print("🔧 Testing encryption/decryption...")
        crypto = get_crypto()
        test_data = "test_encryption_in_executable"
        encrypted = crypto.encrypt_string(test_data)
        decrypted = crypto.decrypt_string(encrypted)

        if test_data == decrypted:
            print("✅ Encryption/decryption working correctly")
        else:
            print("❌ Encryption/decryption failed")
            return 1

        # Test encrypted constants access
        print("🔑 Testing encrypted constants access...")
        has_token = has_bundled_github_token()
        print(f"Has bundled GitHub token: {'✅ Yes' if has_token else '❌ No'}")

        if has_token:
            token = get_bundled_github_token()
            if token:
                # Mask token for security
                masked_token = f"{token[:4]}...{token[-4:]}" if len(token) > 8 else "***"
                print(f"✅ Token retrieved: {masked_token} (length: {len(token)})")
            else:
                print("❌ Failed to retrieve token")
                return 1

        # Test config data access
        print("📊 Testing config data access...")
        config = get_config_from_constants()
        if config:
            print(f"✅ Config data retrieved: {len(config)} items")
            for key in config.keys():
                print(f"  - {key}")
        else:
            print("⚠️  No config data available")

        print("\n" + "=" * 50)
        print("🎉 All encryption tests passed!")
        return 0

    except Exception as e:
        print(f"❌ Encryption test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


def handle_first_run_installation() -> int:
    """
    Handle first-run installation if needed.

    Returns:
        Exit code (0 if should continue, 1 if error, 2 if restart needed)
    """
    try:
        installer = FirstRunInstaller()

        if not installer.needs_installation():
            # No installation needed, continue normally
            return 0

        logging.info("First-run installation required")

        # Try GUI installation first
        try:
            success = show_install_dialog(installer)
            if success:
                # Restart from installed location
                if installer.restart_from_install_location():
                    return 2  # Special exit code indicating restart
                else:
                    print("Failed to restart from installed location")
                    return 1
            else:
                print("Installation cancelled or failed")
                return 1

        except Exception as gui_error:
            logging.warning(f"GUI installation failed, falling back to console: {gui_error}")

            # Fallback to console installation
            print(f"\n{APP_NAME} - First Run Setup")
            print("=" * 50)
            print(f"Installing {APP_NAME} to system directory...")
            print(f"Installation directory: {installer.install_dir}")

            # Perform installation
            if installer.install():
                print("Installation completed successfully!")
                print("Restarting from installed location...")

                # Restart from installed location
                if installer.restart_from_install_location():
                    # Exit current process - the installed version will take over
                    return 2  # Special exit code indicating restart
                else:
                    print("Failed to restart from installed location")
                    return 1
            else:
                print("Installation failed!")
                return 1

    except Exception as e:
        logging.error(f"First-run installation error: {e}", exc_info=True)
        print(f"Installation error: {e}")
        return 1


def main() -> int:
    """
    Main entry point for DevManager.

    Returns:
        Exit code
    """
    args = parse_arguments()
    setup_logging(args.debug)

    logging.info(f"Starting {APP_NAME} v0.1.0")

    try:
        # Check for test mode first
        if args.test_encryption:
            return test_encryption_system()

        # Check for first-run installation (only in simple mode)
        if not args.token:
            install_result = handle_first_run_installation()
            if install_result == 1:
                return 1  # Installation failed
            elif install_result == 2:
                return 0  # Restart initiated, exit cleanly
            # install_result == 0: continue normally

        if args.token:
            # Token mode - Developer operations
            logging.info("Starting in token mode (developer)")
            return handle_token_mode(args.token)
        else:
            # Simple mode - Auto-update and launch
            logging.info("Starting in simple mode (auto-update)")
            return handle_simple_mode()

    except KeyboardInterrupt:
        logging.info("Application interrupted by user")
        return 130
    except Exception as e:
        logging.critical(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
