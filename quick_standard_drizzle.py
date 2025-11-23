#!/usr/bin/env python3
"""
Quick Standard Drizzle Script
Simple script for standard drizzle processing
"""

import sys
from drizzle_config import DrizzleConfig, DrizzleMethod, CalibrationMode
from siril_drizzle import SirilDrizzleProcessor


def main():
    """Quick standard drizzle processing"""
    if len(sys.argv) < 2:
        print("Usage: python quick_standard_drizzle.py <input_directory> [output_directory]")
        print("\nExample:")
        print("  python quick_standard_drizzle.py ./lights ./drizzled_output")
        sys.exit(1)

    input_dir = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "./drizzled_output"

    # Configure for standard drizzle
    config = DrizzleConfig(
        method=DrizzleMethod.STANDARD,
        calibration_mode=CalibrationMode.UNCALIBRATED,
        pixfrac=0.7,  # Good general-purpose value
        scale=0.5,  # 2x oversampling
        input_dir=input_dir,
        output_dir=output_dir,
        debayer=True,  # Set to False for monochrome cameras
    )

    print("Standard Drizzle - Uncalibrated Images")
    print("=" * 60)
    print(config.get_description())
    print("=" * 60)
    print()

    # Process
    try:
        with SirilDrizzleProcessor(config) as processor:
            processor.process()
        print("\nProcessing complete!")
        print(f"Output saved to: {output_dir}")
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
