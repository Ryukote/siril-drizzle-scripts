#!/usr/bin/env python3
"""
Quick launcher for VeraLux Drizzle Studio
Tests dependencies and launches the application
"""

import sys
import subprocess

def check_dependencies():
    """Check if all required dependencies are installed"""
    print("Checking dependencies...")

    missing = []

    # Check PyQt6
    try:
        import PyQt6
        print("✓ PyQt6 installed")
    except ImportError:
        print("✗ PyQt6 not found")
        missing.append("PyQt6")

    # Check if we can import our modules
    try:
        from drizzle_config import DrizzleConfig
        print("✓ drizzle_config available")
    except ImportError as e:
        print(f"✗ drizzle_config not found: {e}")
        missing.append("drizzle_config")

    try:
        from siril_drizzle import SirilDrizzleProcessor
        print("✓ siril_drizzle available")
    except ImportError as e:
        print(f"✗ siril_drizzle not found: {e}")
        missing.append("siril_drizzle")

    if missing:
        print("\nMissing dependencies:")
        for dep in missing:
            print(f"  - {dep}")

        if "PyQt6" in missing:
            print("\nInstalling PyQt6...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "PyQt6"])
                print("✓ PyQt6 installed successfully!")
            except Exception as e:
                print(f"✗ Failed to install PyQt6: {e}")
                return False

        return len(missing) == 1 and missing[0] == "PyQt6"

    return True

def main():
    """Main entry point"""
    print("="*60)
    print("VeraLux Drizzle Studio Launcher")
    print("="*60)
    print()

    if not check_dependencies():
        print("\n⚠️  Some dependencies are missing.")
        print("Please ensure all required files are present.")
        sys.exit(1)

    print("\n✓ All dependencies OK!")
    print("\nLaunching VeraLux Drizzle Studio...")
    print("="*60)
    print()

    # Import and run
    try:
        from veralux_drizzle_studio import main as studio_main
        studio_main()
    except Exception as e:
        print(f"\n✗ Error launching studio: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
