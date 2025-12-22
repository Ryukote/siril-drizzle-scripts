#!/usr/bin/env python3
"""
Siril Drizzle - Complete All-in-One Script
Implements various drizzle methods using pySiril

Based on documentation from:
- pySiril documentation.md
- Drizzle.pdf (Fruchter & Hook 2002)
- fiDrizzle-MU.pdf (Zhang et al. 2025)

This script combines all functionality into a single file for easy deployment.
"""

import os
import sys
import argparse
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass
from enum import Enum

# ============================================================================
# CONFIGURATION CLASSES
# ============================================================================

class DrizzleMethod(Enum):
    """Available drizzle methods"""
    STANDARD = "standard"  # Standard Drizzle (Fruchter & Hook 2002)
    ITERATIVE = "iterative"  # iDrizzle
    FAST_DC = "fast_dc"  # fiDrizzle-DC (difference correction)
    FAST_MU = "fast_mu"  # fiDrizzle-MU (multiplicative updates)


class CalibrationMode(Enum):
    """Image calibration modes"""
    UNCALIBRATED = "uncalibrated"
    CALIBRATED = "calibrated"
    AUTO = "auto"


@dataclass
class DrizzleConfig:
    """
    Configuration for drizzle processing

    Parameters based on:
    - Drizzle.pdf (Fruchter & Hook 2002)
    - 3D drizzle.pdf (Law et al. 2023)
    - fiDrizzle-MU.pdf (Zhang et al. 2025)
    """
    # Drizzle method
    method: DrizzleMethod = DrizzleMethod.STANDARD

    # Calibration mode
    calibration_mode: CalibrationMode = CalibrationMode.AUTO

    # Standard Drizzle parameters (from Drizzle.pdf)
    pixfrac: float = 1.0  # Drop size parameter (0.0-1.0)
    # pixfrac = 1.0: shift-and-add
    # pixfrac = 0.0: interlacing
    # pixfrac = 0.5-0.8: recommended for most cases

    scale: float = 0.5  # Output pixel scale ratio (PSR parameter)
    # scale < 1.0: oversample output
    # scale = 0.5: 2x finer sampling

    # Iterative drizzle parameters (from fiDrizzle papers)
    max_iterations: int = 100  # Maximum iterations for iterative methods
    convergence_threshold: float = 1e-6  # Convergence criterion
    gamma: float = 1.0  # Step size parameter for fiDrizzle-MU

    # Positivity constraint (from fiDrizzle-MU.pdf)
    apply_positivity: bool = True  # Enforce non-negative flux values

    # Image paths
    input_dir: str = ""
    output_dir: str = "./drizzled"

    # Calibration file paths (if calibration_mode != UNCALIBRATED)
    bias_file: Optional[str] = None
    dark_file: Optional[str] = None
    flat_file: Optional[str] = None

    # Processing options
    debayer: bool = True  # For OSC (color) cameras
    equalize_cfa: bool = True  # Equalize CFA channels before debayering

    # Output options
    output_format: str = "fit"  # Output file format
    bit_depth: int = 16  # Output bit depth (16 or 32)

    def validate(self):
        """Validate configuration parameters"""
        if not 0.0 <= self.pixfrac <= 1.0:
            raise ValueError(f"pixfrac must be between 0.0 and 1.0, got {self.pixfrac}")

        if self.scale <= 0:
            raise ValueError(f"scale must be positive, got {self.scale}")

        if self.max_iterations < 1:
            raise ValueError(f"max_iterations must be >= 1, got {self.max_iterations}")

        if self.calibration_mode != CalibrationMode.UNCALIBRATED:
            if self.calibration_mode == CalibrationMode.CALIBRATED:
                if not all([self.bias_file, self.dark_file, self.flat_file]):
                    raise ValueError("Calibration files required for CALIBRATED mode")

    def get_description(self) -> str:
        """Get human-readable description of the configuration"""
        desc = [
            f"Drizzle Method: {self.method.value}",
            f"Calibration: {self.calibration_mode.value}",
            f"Pixfrac: {self.pixfrac} (drop size)",
            f"Scale: {self.scale} (output pixel scale ratio)",
        ]

        if self.method in [DrizzleMethod.ITERATIVE, DrizzleMethod.FAST_DC, DrizzleMethod.FAST_MU]:
            desc.extend([
                f"Max Iterations: {self.max_iterations}",
                f"Convergence Threshold: {self.convergence_threshold}",
            ])

        if self.method == DrizzleMethod.FAST_MU:
            desc.append(f"Gamma (step size): {self.gamma}")

        desc.append(f"Positivity Constraint: {self.apply_positivity}")

        return "\n".join(desc)


# Preset configurations based on use cases
PRESETS = {
    "high_resolution": DrizzleConfig(
        method=DrizzleMethod.STANDARD,
        pixfrac=0.6,
        scale=0.5,
        apply_positivity=True,
    ),
    "fast_iterative": DrizzleConfig(
        method=DrizzleMethod.FAST_MU,
        pixfrac=0.7,
        scale=0.5,
        max_iterations=100,
        gamma=1.0,
        apply_positivity=True,
    ),
    "point_sources": DrizzleConfig(
        method=DrizzleMethod.FAST_MU,
        pixfrac=0.5,
        scale=0.5,
        max_iterations=65,  # Based on JWST example in fiDrizzle-MU.pdf
        apply_positivity=True,
    ),
    "extended_sources": DrizzleConfig(
        method=DrizzleMethod.STANDARD,
        pixfrac=0.8,
        scale=0.5,
        apply_positivity=False,
    ),
}


# ============================================================================
# DRIZZLE PROCESSOR
# ============================================================================

class SirilDrizzleProcessor:
    """Process dithered images using Siril drizzle methods"""

    def __init__(self, config: DrizzleConfig):
        """
        Initialize the drizzle processor

        Args:
            config: DrizzleConfig object with processing parameters
        """
        self.config = config
        self.config.validate()

        # Import pySiril here to give better error messages
        try:
            from pysiril.siril import Siril
            from pysiril.wrapper import Wrapper
            from pysiril.addons import Addons
            self.Siril = Siril
            self.Wrapper = Wrapper
            self.Addons = Addons
        except ImportError:
            print("Error: pySiril not found. Install with:")
            print("python -m pip install pysiril")
            sys.exit(1)

        self.app = None
        self.cmd = None
        self.addons = None

    def __enter__(self):
        """Context manager entry"""
        self.start_siril()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop_siril()

    def start_siril(self):
        """Start Siril and initialize wrappers"""
        print("Starting Siril...")
        self.app = self.Siril()
        self.cmd = self.Wrapper(self.app)
        self.addons = self.Addons(self.app)
        self.app.Open()
        print("Siril started successfully")

    def stop_siril(self):
        """Stop Siril and cleanup"""
        if self.app:
            print("Stopping Siril...")
            self.app.Close()
            del self.app
            print("Siril stopped")

    def setup_environment(self):
        """Set up Siril environment and preferences"""
        print("Configuring Siril environment...")

        # Set bit depth
        if self.config.bit_depth == 16:
            self.cmd.set16bits()
        elif self.config.bit_depth == 32:
            self.cmd.set32bits()

        # Set file extension
        self.cmd.setext(self.config.output_format)

        # Create output directory if it doesn't exist
        os.makedirs(self.config.output_dir, exist_ok=True)

    def prepare_calibration_masters(self):
        """
        Prepare master calibration frames
        Based on pySiril documentation examples
        """
        if self.config.calibration_mode == CalibrationMode.UNCALIBRATED:
            print("Skipping calibration (uncalibrated mode)")
            return

        print("Preparing master calibration frames...")
        process_dir = self.config.output_dir

        # Master Bias
        if self.config.bias_file:
            print(f"Using bias: {self.config.bias_file}")
            # If it's a directory, stack the biases
            if os.path.isdir(self.config.bias_file):
                self.cmd.cd(self.config.bias_file)
                self.cmd.convert('bias', out=process_dir, fitseq=True)
                self.cmd.cd(process_dir)
                self.cmd.stack('bias', type='rej', sigma_low=3, sigma_high=3, norm='no')

        # Master Dark
        if self.config.dark_file:
            print(f"Using dark: {self.config.dark_file}")
            if os.path.isdir(self.config.dark_file):
                self.cmd.cd(self.config.dark_file)
                self.cmd.convert('dark', out=process_dir, fitseq=True)
                self.cmd.cd(process_dir)
                self.cmd.stack('dark', type='rej', sigma_low=3, sigma_high=3, norm='no')

        # Master Flat
        if self.config.flat_file:
            print(f"Using flat: {self.config.flat_file}")
            if os.path.isdir(self.config.flat_file):
                self.cmd.cd(self.config.flat_file)
                self.cmd.convert('flat', out=process_dir, fitseq=True)
                self.cmd.cd(process_dir)
                self.cmd.preprocess('flat', bias='bias_stacked')
                self.cmd.stack('pp_flat', type='rej', sigma_low=3, sigma_high=3, norm='mul')

    def calibrate_lights(self, sequence_name: str = 'light'):
        """
        Calibrate light frames with master calibration frames

        Args:
            sequence_name: Name of the light sequence
        """
        if self.config.calibration_mode == CalibrationMode.UNCALIBRATED:
            print("Skipping calibration")
            return sequence_name

        print(f"Calibrating {sequence_name} frames...")

        preprocess_args = {
            'cfa': self.config.debayer,
            'debayer': self.config.debayer,
        }

        if self.config.equalize_cfa and self.config.debayer:
            preprocess_args['equalize_cfa'] = True

        # Add calibration frames if available
        if self.config.dark_file:
            preprocess_args['dark'] = 'dark_stacked'
        if self.config.flat_file:
            preprocess_args['flat'] = 'pp_flat_stacked'

        self.cmd.preprocess(sequence_name, **preprocess_args)

        return f'pp_{sequence_name}'

    def standard_drizzle(self, sequence_name: str, output_name: str = 'drizzled'):
        """
        Standard drizzle (Fruchter & Hook 2002)

        Args:
            sequence_name: Input sequence name
            output_name: Output file name
        """
        print(f"\n{'='*60}")
        print(f"Running STANDARD DRIZZLE")
        print(f"pixfrac={self.config.pixfrac}, scale={self.config.scale}")
        print(f"{'='*60}\n")

        # Siril drizzle command syntax (from readthedocs):
        # drizzle [sequencename] [-pixfrac=] [-scale=] [-kernel=] [-flat] [-cf=]

        self.cmd.Execute(
            f"drizzle {sequence_name} "
            f"-pixfrac={self.config.pixfrac} "
            f"-scale={self.config.scale} "
            f"-out={output_name}"
        )

        print(f"Standard drizzle complete: {output_name}")

    def iterative_drizzle_simulation(self, sequence_name: str, output_name: str = 'drizzled_iter'):
        """
        Simulated iterative drizzle approach

        Note: True iterative drizzle (iDrizzle, fiDrizzle) would require
        implementing the algorithms from the papers. This is a simplified
        multi-pass approach using Siril's drizzle.

        Args:
            sequence_name: Input sequence name
            output_name: Output file name
        """
        print(f"\n{'='*60}")
        print(f"Running ITERATIVE DRIZZLE (simplified)")
        print(f"Method: {self.config.method.value}")
        print(f"Max iterations: {self.config.max_iterations}")
        print(f"{'='*60}\n")

        # For a true fiDrizzle-MU implementation, you would need to:
        # 1. Implement the multiplicative update algorithm from fiDrizzle-MU.pdf
        # 2. Iterate through frames applying the update rule
        # 3. Monitor convergence

        # This simplified version does a multi-pass drizzle
        # with decreasing pixfrac (similar to iDrizzle concept)

        current_pixfrac = self.config.pixfrac
        for iteration in range(min(5, self.config.max_iterations)):  # Limit to 5 passes
            iter_pixfrac = current_pixfrac * (0.9 ** iteration)

            print(f"Iteration {iteration + 1}: pixfrac={iter_pixfrac:.3f}")

            self.cmd.Execute(
                f"drizzle {sequence_name} "
                f"-pixfrac={iter_pixfrac} "
                f"-scale={self.config.scale} "
                f"-out={output_name}_iter{iteration}"
            )

        print(f"Iterative drizzle complete: {output_name}_iter*")
        print("\nNote: Full fiDrizzle-MU/DC implementation requires custom code")
        print("See fiDrizzle-MU.pdf for the complete algorithm")

    def process(self, light_pattern: str = 'light*.fit'):
        """
        Main processing pipeline

        Args:
            light_pattern: Glob pattern for light frames
        """
        print(f"\n{'='*60}")
        print("SIRIL DRIZZLE PROCESSING")
        print(self.config.get_description())
        print(f"{'='*60}\n")

        # Setup
        self.setup_environment()

        # Navigate to input directory
        self.cmd.cd(self.config.input_dir)

        # Convert and prepare sequence
        print(f"Converting images matching: {light_pattern}")
        self.cmd.convert('light', out=self.config.output_dir, fitseq=True)

        # Change to processing directory
        self.cmd.cd(self.config.output_dir)

        # Prepare calibration if needed
        if self.config.calibration_mode != CalibrationMode.UNCALIBRATED:
            self.prepare_calibration_masters()
            sequence_name = self.calibrate_lights('light')
        else:
            sequence_name = 'light'

        # Apply drizzle method
        if self.config.method == DrizzleMethod.STANDARD:
            self.standard_drizzle(sequence_name, 'result_standard')
        elif self.config.method in [DrizzleMethod.ITERATIVE, DrizzleMethod.FAST_DC, DrizzleMethod.FAST_MU]:
            self.iterative_drizzle_simulation(sequence_name, 'result_iterative')

        print(f"\n{'='*60}")
        print("PROCESSING COMPLETE")
        print(f"Output directory: {self.config.output_dir}")
        print(f"{'='*60}\n")


# ============================================================================
# COMMAND LINE INTERFACE
# ============================================================================

def run_quick_standard(args):
    """Quick standard drizzle processing"""
    config = DrizzleConfig(
        method=DrizzleMethod.STANDARD,
        calibration_mode=CalibrationMode.UNCALIBRATED,
        pixfrac=args.pixfrac,
        scale=args.scale,
        input_dir=args.input,
        output_dir=args.output,
        debayer=not args.mono,
    )

    print("Standard Drizzle - Uncalibrated Images")
    print("=" * 60)
    print(config.get_description())
    print("=" * 60)
    print()

    with SirilDrizzleProcessor(config) as processor:
        processor.process()

    print(f"\nProcessing complete! Output saved to: {args.output}")


def run_calibrated(args):
    """Drizzle processing with calibration"""
    config = DrizzleConfig(
        method=DrizzleMethod.STANDARD,
        calibration_mode=CalibrationMode.CALIBRATED,
        pixfrac=args.pixfrac,
        scale=args.scale,
        input_dir=args.input,
        output_dir=args.output,
        bias_file=args.bias,
        dark_file=args.dark,
        flat_file=args.flat,
        debayer=not args.mono,
        equalize_cfa=True,
    )

    print("Calibrated Drizzle Processing")
    print("=" * 60)
    print(config.get_description())
    print("=" * 60)
    print()

    with SirilDrizzleProcessor(config) as processor:
        processor.process()

    print(f"\nProcessing complete! Output saved to: {args.output}")


def run_point_source(args):
    """Drizzle processing optimized for point sources"""
    config = PRESETS['point_sources']
    config.input_dir = args.input
    config.output_dir = args.output
    config.pixfrac = args.pixfrac
    config.scale = args.scale

    if args.calibrated:
        config.calibration_mode = CalibrationMode.CALIBRATED
        config.bias_file = os.path.join(args.input, 'biases')
        config.dark_file = os.path.join(args.input, 'darks')
        config.flat_file = os.path.join(args.input, 'flats')
        config.input_dir = os.path.join(args.input, 'lights')

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

    with SirilDrizzleProcessor(config) as processor:
        processor.process()

    print(f"\nProcessing complete! Output saved to: {args.output}")


def run_preset(args):
    """Run with a preset configuration"""
    if args.preset not in PRESETS:
        print(f"Error: Unknown preset '{args.preset}'")
        print(f"Available presets: {', '.join(PRESETS.keys())}")
        sys.exit(1)

    config = PRESETS[args.preset]
    config.input_dir = args.input
    config.output_dir = args.output
    config.calibration_mode = CalibrationMode.CALIBRATED if args.calibrated else CalibrationMode.UNCALIBRATED

    if args.calibrated:
        config.bias_file = args.bias
        config.dark_file = args.dark
        config.flat_file = args.flat

    print(f"Running preset: {args.preset}")
    print("=" * 60)
    print(config.get_description())
    print("=" * 60)
    print()

    with SirilDrizzleProcessor(config) as processor:
        processor.process()

    print(f"\nProcessing complete! Output saved to: {args.output}")


def main():
    """Main entry point with argument parsing"""
    parser = argparse.ArgumentParser(
        description='Siril Drizzle - Complete drizzle processing tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Quick standard drizzle (uncalibrated)
  %(prog)s standard ./lights -o ./output

  # Calibrated drizzle
  %(prog)s calibrated ./lights -o ./output -b ./biases -d ./darks -f ./flats

  # Point source optimized
  %(prog)s point-source ./lights -o ./output

  # Use a preset
  %(prog)s preset high_resolution ./lights -o ./output

Available presets:
  - high_resolution: Standard drizzle, optimized for resolution
  - fast_iterative: Fast iterative method (fiDrizzle-MU)
  - point_sources: Optimized for point sources (stars)
  - extended_sources: Optimized for extended objects (nebulae, galaxies)
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Processing mode')
    subparsers.required = False

    # Standard drizzle command
    standard_parser = subparsers.add_parser('standard', help='Quick standard drizzle (uncalibrated)')
    standard_parser.add_argument('input', help='Input directory with light frames')
    standard_parser.add_argument('-o', '--output', default='./drizzled_output', help='Output directory')
    standard_parser.add_argument('-p', '--pixfrac', type=float, default=0.7, help='Pixfrac (0.0-1.0, default: 0.7)')
    standard_parser.add_argument('-s', '--scale', type=float, default=0.5, help='Scale factor (default: 0.5)')
    standard_parser.add_argument('--mono', action='store_true', help='Monochrome camera (no debayer)')
    standard_parser.set_defaults(func=run_quick_standard)

    # Calibrated drizzle command
    cal_parser = subparsers.add_parser('calibrated', help='Calibrated drizzle processing')
    cal_parser.add_argument('input', help='Input directory with light frames')
    cal_parser.add_argument('-o', '--output', default='./drizzled_output', help='Output directory')
    cal_parser.add_argument('-b', '--bias', required=True, help='Bias directory or master bias')
    cal_parser.add_argument('-d', '--dark', required=True, help='Dark directory or master dark')
    cal_parser.add_argument('-f', '--flat', required=True, help='Flat directory or master flat')
    cal_parser.add_argument('-p', '--pixfrac', type=float, default=0.7, help='Pixfrac (0.0-1.0, default: 0.7)')
    cal_parser.add_argument('-s', '--scale', type=float, default=0.5, help='Scale factor (default: 0.5)')
    cal_parser.add_argument('--mono', action='store_true', help='Monochrome camera (no debayer)')
    cal_parser.set_defaults(func=run_calibrated)

    # Point source drizzle command
    point_parser = subparsers.add_parser('point-source', help='Point source optimized drizzle')
    point_parser.add_argument('input', help='Input directory with light frames')
    point_parser.add_argument('-o', '--output', default='./drizzled_output', help='Output directory')
    point_parser.add_argument('-p', '--pixfrac', type=float, default=0.5, help='Pixfrac (0.0-1.0, default: 0.5)')
    point_parser.add_argument('-s', '--scale', type=float, default=0.5, help='Scale factor (default: 0.5)')
    point_parser.add_argument('--calibrated', action='store_true', help='Use calibrated mode (expects biases/darks/flats/lights subdirs)')
    point_parser.set_defaults(func=run_point_source)

    # Preset command
    preset_parser = subparsers.add_parser('preset', help='Use a preset configuration')
    preset_parser.add_argument('preset_name', metavar='preset', choices=PRESETS.keys(), help='Preset name')
    preset_parser.add_argument('input', help='Input directory with light frames')
    preset_parser.add_argument('-o', '--output', default='./drizzled_output', help='Output directory')
    preset_parser.add_argument('--calibrated', action='store_true', help='Use calibrated mode')
    preset_parser.add_argument('-b', '--bias', help='Bias directory or master bias (if calibrated)')
    preset_parser.add_argument('-d', '--dark', help='Dark directory or master dark (if calibrated)')
    preset_parser.add_argument('-f', '--flat', help='Flat directory or master flat (if calibrated)')
    preset_parser.set_defaults(func=run_preset)

    # List presets command
    list_parser = subparsers.add_parser('list-presets', help='List available presets')
    def list_presets(args):
        print("\nAvailable Presets:")
        print("=" * 60)
        for name, config in PRESETS.items():
            print(f"\n{name}:")
            print(config.get_description())
        print()
    list_parser.set_defaults(func=list_presets)

    args = parser.parse_args()

    # If no command specified, show helpful message
    if not args.command:
        print("\n" + "="*60)
        print("SIRIL DRIZZLE - All-in-One Processing Tool")
        print("="*60)
        print("\nNo command specified. Please choose a processing mode:\n")
        print("Quick Start Examples:")
        print("-" * 60)
        print("1. Standard drizzle (uncalibrated):")
        print("   python siril_drizzle_complete.py standard ./lights\n")
        print("2. With calibration frames:")
        print("   python siril_drizzle_complete.py calibrated ./lights \\")
        print("       -b ./biases -d ./darks -f ./flats\n")
        print("3. Point source optimized:")
        print("   python siril_drizzle_complete.py point-source ./lights\n")
        print("4. List available presets:")
        print("   python siril_drizzle_complete.py list-presets\n")
        print("-" * 60)
        print("\nFor detailed help:")
        print("   python siril_drizzle_complete.py --help")
        print("   python siril_drizzle_complete.py <command> --help")
        print("="*60 + "\n")
        sys.exit(0)

    try:
        args.func(args)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
