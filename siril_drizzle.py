"""
Siril Drizzle Processing Script
Implements various drizzle methods using pySiril

Based on documentation from:
- pySiril documentation.md
- Drizzle.pdf (Fruchter & Hook 2002)
- fiDrizzle-MU.pdf (Zhang et al. 2025)
"""

import os
import sys
from pathlib import Path
from typing import Optional, List
import glob

try:
    from pysiril.siril import Siril
    from pysiril.wrapper import Wrapper
    from pysiril.addons import Addons
except ImportError:
    print("Error: pySiril not found. Install with:")
    print("python -m pip install pysiril")
    sys.exit(1)

from drizzle_config import DrizzleConfig, DrizzleMethod, CalibrationMode


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
        self.app = Siril()
        self.cmd = Wrapper(self.app)
        self.addons = Addons(self.app)
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


def main():
    """Example usage"""
    from drizzle_config import PRESETS

    # Example 1: High resolution drizzle with uncalibrated images
    config = PRESETS['high_resolution']
    config.input_dir = "./lights"  # Directory with dithered light frames
    config.output_dir = "./drizzled_output"
    config.calibration_mode = CalibrationMode.UNCALIBRATED

    # Example 2: Or use calibrated workflow
    # config.calibration_mode = CalibrationMode.CALIBRATED
    # config.bias_file = "./biases"
    # config.dark_file = "./darks"
    # config.flat_file = "./flats"

    # Process
    with SirilDrizzleProcessor(config) as processor:
        processor.process()


if __name__ == "__main__":
    main()
