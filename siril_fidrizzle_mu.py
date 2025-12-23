#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fiDrizzle-MU: Fast Iterative Drizzle with Multiplicative Updates for Siril
===========================================================================

Implementation of the fiDrizzle-MU algorithm from the paper:
"fiDrizzle-MU: A Fast Iterative Drizzle with Multiplicative Updates"
by Shen Zhang et al., arXiv:2511.09881v1

This script implements the multiplicative update iterative drizzle algorithm
for combining multiple dithered astronomical images with superior performance
in decorrelating adjacent pixels and reducing noise complexity.

Author: Implementation for Siril
Date: 2025
License: GPLv3
"""

import os
import sys
import numpy as np
from astropy.io import fits
from scipy import ndimage
import argparse
from pathlib import Path
import time


class FiDrizzleMU:
    """
    fiDrizzle-MU: Fast Iterative Drizzle with Multiplicative Updates

    This class implements the fiDrizzle-MU algorithm which uses multiplicative
    updates in each iteration instead of difference correction terms.

    Algorithm:
    F_(i+1) = F_i × (1/L_E × Σ(S^k_u(I^k / S^k_d(F_i))))^γ

    Where:
    - F_i: Image approximation at i-th iteration
    - I^k: k-th dithered exposure image
    - S^k_u: Upsampling operator for k-th exposure
    - S^k_d: Downsampling operator for k-th exposure
    - L_E: Effective overlapping layer (normalization factor)
    - γ: Step-size parameter (default: 1)
    """

    def __init__(self, psr=0.5, gamma=1.0, max_iterations=100,
                 positivity_constraint=True, verbose=True):
        """
        Initialize fiDrizzle-MU processor.

        Parameters:
        -----------
        psr : float
            Pixel Scale Ratio - ratio of output to input pixel scale (default: 0.5)
            PSR=0.5 means output pixels are half the size (2x finer sampling)
        gamma : float
            Step-size parameter for convergence rate (default: 1.0)
        max_iterations : int
            Maximum number of iterations (default: 100)
        positivity_constraint : bool
            Apply positivity constraint to suppress ringing (default: True)
        verbose : bool
            Print progress information (default: True)
        """
        self.psr = psr
        self.gamma = gamma
        self.max_iterations = max_iterations
        self.positivity_constraint = positivity_constraint
        self.verbose = verbose

        self.input_images = []
        self.shift_data = []
        self.output_shape = None
        self.input_shape = None

    def log(self, message):
        """Print message if verbose mode is enabled."""
        if self.verbose:
            print(f"[fiDrizzle-MU] {message}")

    def load_images(self, image_files, shift_file=None):
        """
        Load dithered images and their shift information.

        Parameters:
        -----------
        image_files : list
            List of paths to FITS files containing dithered images
        shift_file : str, optional
            Path to file containing shift information (dx, dy for each image)
            If None, assumes images are already registered (zero shifts)
        """
        self.log(f"Loading {len(image_files)} dithered images...")

        self.input_images = []
        for img_file in image_files:
            with fits.open(img_file) as hdul:
                data = hdul[0].data
                if data is None:
                    raise ValueError(f"No data in {img_file}")
                self.input_images.append(data.astype(np.float64))

        self.input_shape = self.input_images[0].shape
        self.log(f"Input image shape: {self.input_shape}")

        # Calculate output shape based on PSR
        scale_factor = int(1.0 / self.psr)
        self.output_shape = (
            self.input_shape[0] * scale_factor,
            self.input_shape[1] * scale_factor
        )
        self.log(f"Output image shape: {self.output_shape} (PSR={self.psr})")

        # Load or initialize shifts
        if shift_file and os.path.exists(shift_file):
            self.log(f"Loading shifts from {shift_file}...")
            self.shift_data = self._load_shifts(shift_file)
        else:
            self.log("No shift file provided, assuming zero shifts (registered images)")
            self.shift_data = [(0.0, 0.0) for _ in self.input_images]

    def _load_shifts(self, shift_file):
        """Load shift data from file."""
        shifts = []
        with open(shift_file, 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        dx, dy = float(parts[0]), float(parts[1])
                        shifts.append((dx, dy))
        return shifts

    def upsampling(self, image, k_idx):
        """
        Upsampling operator S^k_u: from coarse frame to fine grid.

        This implements shift-and-add (pixfrac=1) with sub-pixel shifts.

        Parameters:
        -----------
        image : ndarray
            Input image on coarse grid
        k_idx : int
            Index of exposure (for shift information)

        Returns:
        --------
        ndarray
            Upsampled image on fine grid
        """
        scale_factor = int(1.0 / self.psr)

        # Get shift for this exposure
        dx, dy = self.shift_data[k_idx]

        # Zoom to fine grid using nearest-neighbor (preserves flux per pixel)
        upsampled = np.kron(image, np.ones((scale_factor, scale_factor)))

        # Apply sub-pixel shift
        if abs(dx) > 1e-6 or abs(dy) > 1e-6:
            # Convert shift to fine grid coordinates
            shift_fine = (dy * scale_factor, dx * scale_factor)
            upsampled = ndimage.shift(upsampled, shift_fine, order=1, mode='constant', cval=0)

        return upsampled

    def downsampling(self, image, k_idx):
        """
        Downsampling operator S^k_d: from fine grid to coarse frame.

        Implements area-weighted flux conservation scheme.

        Parameters:
        -----------
        image : ndarray
            Input image on fine grid
        k_idx : int
            Index of exposure (for shift information)

        Returns:
        --------
        ndarray
            Downsampled image on coarse grid
        """
        scale_factor = int(1.0 / self.psr)

        # Get shift for this exposure (reverse direction)
        dx, dy = self.shift_data[k_idx]

        # Apply reverse sub-pixel shift
        shifted = image.copy()
        if abs(dx) > 1e-6 or abs(dy) > 1e-6:
            shift_fine = (-dy * scale_factor, -dx * scale_factor)
            shifted = ndimage.shift(shifted, shift_fine, order=1, mode='constant', cval=0)

        # Downsample by averaging blocks (flux conservation)
        h, w = shifted.shape
        new_h, new_w = h // scale_factor, w // scale_factor

        downsampled = shifted[:new_h*scale_factor, :new_w*scale_factor].reshape(
            new_h, scale_factor, new_w, scale_factor
        ).mean(axis=(1, 3)) * (scale_factor ** 2)

        return downsampled

    def initial_drizzle(self):
        """
        Create initial F_0 by drizzling all input images.
        This is standard shift-and-add on the fine grid.

        Returns:
        --------
        tuple
            (F_0, L_E) where F_0 is initial drizzled image and
            L_E is effective overlapping layer
        """
        self.log("Creating initial drizzle (F_0)...")

        F_0 = np.zeros(self.output_shape, dtype=np.float64)
        L_E = np.zeros(self.output_shape, dtype=np.float64)

        for k_idx, image in enumerate(self.input_images):
            # Upsample each image to fine grid
            upsampled = self.upsampling(image, k_idx)

            # Accumulate (using weight=1 for all pixels)
            mask = upsampled > 0
            F_0 += upsampled
            L_E += mask.astype(np.float64)

        # Normalize by overlap count
        L_E[L_E == 0] = 1  # Avoid division by zero
        F_0 /= L_E

        self.log(f"Initial drizzle complete. Non-zero pixels: {np.sum(F_0 > 0)}")

        return F_0, L_E

    def iterate(self, F_i, L_E, iteration):
        """
        Perform one iteration of fiDrizzle-MU algorithm.

        F_(i+1) = F_i × (R_i)^γ

        where R_i = 1/L_E × Σ_k S^k_u(I^k / S^k_d(F_i))

        Parameters:
        -----------
        F_i : ndarray
            Current image estimate
        L_E : ndarray
            Effective overlapping layer
        iteration : int
            Current iteration number

        Returns:
        --------
        ndarray
            Updated image F_(i+1)
        """
        N = len(self.input_images)
        R_i = np.zeros(self.output_shape, dtype=np.float64)

        for k_idx in range(N):
            # Step 1: Downsample F_i to k-th frame
            G_k = self.downsampling(F_i, k_idx)

            # Step 2: Compute ratio I^k / G^k (with numerical stability)
            I_k = self.input_images[k_idx]
            ratio = np.ones_like(I_k)
            mask = G_k > 1e-10
            ratio[mask] = I_k[mask] / G_k[mask]
            ratio[~mask] = 1.0  # No correction where G_k is too small

            # Step 3: Upsample ratio back to fine grid
            ratio_upsampled = self.upsampling(ratio, k_idx)

            # Accumulate
            R_i += ratio_upsampled

        # Normalize by L_E
        R_i /= L_E

        # Multiplicative update with gamma exponent
        if self.gamma != 1.0:
            R_i = np.power(R_i, self.gamma)

        F_new = F_i * R_i

        # Apply positivity constraint (Equation 2 in paper)
        if self.positivity_constraint:
            negative_mask = F_new < 0
            F_new[negative_mask] = F_i[negative_mask]

        return F_new

    def compute_metrics(self, F_i, F_prev):
        """
        Compute convergence metrics.

        Parameters:
        -----------
        F_i : ndarray
            Current image
        F_prev : ndarray
            Previous iteration image

        Returns:
        --------
        dict
            Dictionary with metrics (relative_change, etc.)
        """
        diff = np.abs(F_i - F_prev)
        relative_change = np.sum(diff) / (np.sum(F_i) + 1e-10)

        return {
            'relative_change': relative_change,
            'mean_flux': np.mean(F_i),
            'max_flux': np.max(F_i)
        }

    def process(self):
        """
        Run the complete fiDrizzle-MU algorithm.

        Returns:
        --------
        ndarray
            Final reconstructed image
        """
        if len(self.input_images) == 0:
            raise ValueError("No images loaded. Call load_images() first.")

        self.log("=" * 60)
        self.log("Starting fiDrizzle-MU processing")
        self.log("=" * 60)
        self.log(f"Parameters: PSR={self.psr}, gamma={self.gamma}, "
                f"max_iter={self.max_iterations}, "
                f"positivity={self.positivity_constraint}")

        start_time = time.time()

        # Step 1: Initial drizzle (F_0)
        F_i, L_E = self.initial_drizzle()

        # Iterative refinement
        self.log("\nStarting iterations...")
        for iteration in range(1, self.max_iterations + 1):
            F_prev = F_i.copy()

            # Perform one iteration
            F_i = self.iterate(F_i, L_E, iteration)

            # Compute metrics
            metrics = self.compute_metrics(F_i, F_prev)

            if iteration % 10 == 0 or iteration == 1:
                self.log(f"Iteration {iteration:3d}: "
                        f"rel_change={metrics['relative_change']:.6e}, "
                        f"mean_flux={metrics['mean_flux']:.2f}, "
                        f"max_flux={metrics['max_flux']:.2f}")

            # Check convergence
            if metrics['relative_change'] < 1e-6:
                self.log(f"Converged at iteration {iteration}")
                break

        elapsed = time.time() - start_time
        self.log("=" * 60)
        self.log(f"Processing complete in {elapsed:.2f} seconds")
        self.log(f"Final image shape: {F_i.shape}")
        self.log(f"Total flux: {np.sum(F_i):.2f}")
        self.log("=" * 60)

        return F_i

    def save_result(self, image, output_file, header=None):
        """
        Save result to FITS file.

        Parameters:
        -----------
        image : ndarray
            Image data to save
        output_file : str
            Output FITS file path
        header : fits.Header, optional
            FITS header to use (will be updated with processing info)
        """
        self.log(f"Saving result to {output_file}...")

        # Create or update header
        if header is None:
            header = fits.Header()

        header['FDRZMETH'] = ('fiDrizzle-MU', 'Drizzle method')
        header['FDRZ_PSR'] = (self.psr, 'Pixel scale ratio')
        header['FDRZ_GAM'] = (self.gamma, 'Step-size parameter')
        header['FDRZ_POS'] = (self.positivity_constraint, 'Positivity constraint')
        header['FDRZ_NIM'] = (len(self.input_images), 'Number of input images')

        hdu = fits.PrimaryHDU(data=image.astype(np.float32), header=header)
        hdu.writeto(output_file, overwrite=True)

        self.log(f"Result saved successfully")


def main():
    """Main entry point for command-line usage."""
    parser = argparse.ArgumentParser(
        description='fiDrizzle-MU: Fast Iterative Drizzle with Multiplicative Updates',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage with registered images
  %(prog)s image_*.fit -o result.fits

  # With custom parameters
  %(prog)s image_*.fit -o result.fits --psr 0.5 --iterations 100

  # With shift file
  %(prog)s image_*.fit -o result.fits --shifts shifts.txt

  # Disable positivity constraint
  %(prog)s image_*.fit -o result.fits --no-positivity

For more information, see the paper:
"fiDrizzle-MU: A Fast Iterative Drizzle with Multiplicative Updates"
arXiv:2511.09881v1
        """
    )

    parser.add_argument('images', nargs='+', help='Input FITS images (dithered exposures)')
    parser.add_argument('-o', '--output', required=True, help='Output FITS file')
    parser.add_argument('--psr', type=float, default=0.5,
                       help='Pixel Scale Ratio (default: 0.5 = 2x finer sampling)')
    parser.add_argument('--gamma', type=float, default=1.0,
                       help='Step-size parameter (default: 1.0)')
    parser.add_argument('--iterations', type=int, default=100,
                       help='Maximum iterations (default: 100)')
    parser.add_argument('--shifts', type=str, default=None,
                       help='File with shift data (dx dy per line)')
    parser.add_argument('--no-positivity', action='store_true',
                       help='Disable positivity constraint')
    parser.add_argument('-q', '--quiet', action='store_true',
                       help='Quiet mode (minimal output)')

    args = parser.parse_args()

    # Validate inputs
    if not args.images:
        parser.error("No input images specified")

    for img_file in args.images:
        if not os.path.exists(img_file):
            parser.error(f"Input file not found: {img_file}")

    # Create processor
    processor = FiDrizzleMU(
        psr=args.psr,
        gamma=args.gamma,
        max_iterations=args.iterations,
        positivity_constraint=not args.no_positivity,
        verbose=not args.quiet
    )

    # Load images
    processor.load_images(args.images, shift_file=args.shifts)

    # Process
    result = processor.process()

    # Save result
    processor.save_result(result, args.output)

    print(f"\n✓ fiDrizzle-MU processing complete!")
    print(f"  Output: {args.output}")
    print(f"  Shape: {result.shape}")
    print(f"  Total flux: {np.sum(result):.2f}")


if __name__ == '__main__':
    main()
