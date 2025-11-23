#!/usr/bin/env python3
"""
Point Source Optimized Drizzle
Uses fiDrizzle-MU method optimized for point sources
Based on parameters from fiDrizzle-MU.pdf
"""

import sys
from drizzle_config import DrizzleConfig, DrizzleMethod, CalibrationMode, PRESETS
from siril_drizzle import SirilDrizzleProcessor


def main():
    """Drizzle processing optimized for point sources"""
    if len(sys.argv) < 2:
        print("Usage: python point_source_drizzle.py <input_directory> [output_directory] [calibrated]")
        print("\nExamples:")
        print("  Uncalibrated:")
        print("    python point_source_drizzle.py ./lights ./drizzled_output")
        print("\n  Calibrated (with master frames in subdirectories):")
        print("    python point_source_drizzle.py ./data ./drizzled_output calibrated")
        print("    (expects ./data/lights, ./data/biases, ./data/darks, ./data/flats)")
        sys.exit(1)

    input_dir = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "./drizzled_output"
    use_calibration = len(sys.argv) > 3 and sys.argv[3].lower() == 'calibrated'

    # Start with point source preset
    config = PRESETS['point_sources']
    config.input_dir = input_dir
    config.output_dir = output_dir

    if use_calibration:
        import os
        config.calibration_mode = CalibrationMode.CALIBRATED
        config.bias_file = os.path.join(input_dir, 'biases')
        config.dark_file = os.path.join(input_dir, 'darks')
        config.flat_file = os.path.join(input_dir, 'flats')
        # Update input to lights subdirectory
        config.input_dir = os.path.join(input_dir, 'lights')

    print("Point Source Optimized Drizzle (fiDrizzle-MU)")
    print("=" * 60)
    print("Optimized for:")
    print("  - Point sources (stars, quasars, etc.)")
    print("  - Maximum spatial resolution")
    print("  - Minimal flux spreading")
    print("=" * 60)
    print()
    print(config.get_description())
    print("=" * 60)
    print()

    # Process
    try:
        with SirilDrizzleProcessor(config) as processor:
            processor.process()
        print("\nProcessing complete!")
        print(f"Output saved to: {output_dir}")
        print("\nNote: For full fiDrizzle-MU implementation with ~65 iterations")
        print("      as described in fiDrizzle-MU.pdf, see the main siril_drizzle.py script")
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
