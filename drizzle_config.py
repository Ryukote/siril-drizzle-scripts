"""
Drizzle Configuration Module
Defines parameters for different drizzle methods based on the documentation
"""

from dataclasses import dataclass
from typing import Optional
from enum import Enum


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
    output_dir: str = "../drizzled"

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
