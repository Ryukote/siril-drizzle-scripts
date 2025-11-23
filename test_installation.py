#!/usr/bin/env python3
"""
Test Installation Script
Verify that all required components are properly installed
"""

import sys


def check_python_version():
    """Check Python version"""
    print("Checking Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 7:
        print(f"  ✓ Python {version.major}.{version.minor}.{version.micro} (OK)")
        return True
    else:
        print(f"  ✗ Python {version.major}.{version.minor}.{version.micro} (Need 3.7+)")
        return False


def check_pysiril():
    """Check pySiril installation"""
    print("\nChecking pySiril installation...")
    try:
        from pysiril.siril import Siril
        from pysiril.wrapper import Wrapper
        from pysiril.addons import Addons
        print("  ✓ pySiril installed (OK)")
        return True
    except ImportError as e:
        print(f"  ✗ pySiril not found: {e}")
        print("     Install with: python -m pip install pysiril")
        print("     Download from: https://gitlab.com/free-astro/pysiril/-/releases")
        return False


def check_tkinter():
    """Check tkinter for GUI"""
    print("\nChecking tkinter (for GUI)...")
    try:
        import tkinter
        print("  ✓ tkinter installed (OK)")
        return True
    except ImportError:
        print("  ✗ tkinter not found")
        print("     Install with: sudo apt-get install python3-tk (Linux)")
        print("     or: brew install python-tk (macOS)")
        print("     Note: tkinter only needed for GUI, scripts work without it")
        return False


def check_modules():
    """Check local modules"""
    print("\nChecking local modules...")
    try:
        from drizzle_config import DrizzleConfig, DrizzleMethod, CalibrationMode
        print("  ✓ drizzle_config.py (OK)")

        from siril_drizzle import SirilDrizzleProcessor
        print("  ✓ siril_drizzle.py (OK)")

        return True
    except ImportError as e:
        print(f"  ✗ Error loading modules: {e}")
        return False


def test_config():
    """Test configuration creation"""
    print("\nTesting configuration...")
    try:
        from drizzle_config import DrizzleConfig, PRESETS

        config = DrizzleConfig()
        config.validate()
        print("  ✓ Default configuration valid")

        preset = PRESETS['high_resolution']
        preset.validate()
        print("  ✓ Presets loaded successfully")

        return True
    except Exception as e:
        print(f"  ✗ Configuration test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("Siril Drizzle Scripts - Installation Test")
    print("=" * 60)

    results = []
    results.append(("Python Version", check_python_version()))
    results.append(("pySiril", check_pysiril()))
    results.append(("tkinter (GUI)", check_tkinter()))
    results.append(("Local Modules", check_modules()))
    results.append(("Configuration", test_config()))

    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    all_pass = True
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{name:20s}: {status}")
        if not passed and name != "tkinter (GUI)":  # tkinter is optional
            all_pass = False

    print("=" * 60)

    if all_pass:
        print("\n✓ All tests passed! You're ready to use the drizzle scripts.")
        print("\nQuick start:")
        print("  GUI:         python drizzle_gui.py")
        print("  Command:     python quick_standard_drizzle.py ./lights")
        print("  Examples:    See examples/ directory")
        print("\nFor full documentation, see README.md")
    else:
        print("\n✗ Some tests failed. Please install missing components.")
        print("See messages above for installation instructions.")
        sys.exit(1)


if __name__ == "__main__":
    main()
