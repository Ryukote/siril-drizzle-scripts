#!/usr/bin/env python3
"""
Calibrated Drizzle Script
Process images with master calibration frames
"""

import sys
from drizzle_config import DrizzleConfig, DrizzleMethod, CalibrationMode
from siril_drizzle import SirilDrizzleProcessor


def main():
    """Drizzle processing with calibration"""
    if len(sys.argv) < 5:
        print("Usage: python calibrated_drizzle.py <lights_dir> <bias_dir> <dark_dir> <flat_dir> [output_dir]")
        print("\nExample:")
        print("  python calibrated_drizzle.py ./lights ./biases ./darks ./flats ./drizzled_output")
        sys.exit(1)

    lights_dir = sys.argv[1]
    bias_dir = sys.argv[2]
    dark_dir = sys.argv[3]
    flat_dir = sys.argv[4]
    output_dir = sys.argv[5] if len(sys.argv) > 5 else "./drizzled_output"

    # Configure for calibrated drizzle
    config = DrizzleConfig(
        method=DrizzleMethod.STANDARD,
        calibration_mode=CalibrationMode.CALIBRATED,
        pixfrac=0.7,
        scale=0.5,
        input_dir=lights_dir,
        output_dir=output_dir,
        bias_file=bias_dir,
        dark_file=dark_dir,
        flat_file=flat_dir,
        debayer=True,  # Set to False for monochrome
        equalize_cfa=True,
    )

    print("Calibrated Drizzle Processing")
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
