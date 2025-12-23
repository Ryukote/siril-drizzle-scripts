# Siril Drizzle Scripts

Python scripts for advanced drizzle processing in Siril, supporting multiple drizzle methods for both calibrated and uncalibrated images.

## ⭐ NEW: VeraLux Drizzle Studio

**Professional GUI for complete calibration + drizzle workflow!**

```bash
python veralux_drizzle_studio.py
```

Features:
- 🎨 **Modern Dark UI** - VeraLux design system
- 📁 **Complete Workflow** - Calibration + Drizzle in one tool
- ⚡ **4 Drizzle Methods** - Standard, iDrizzle, fiDrizzle-DC, fiDrizzle-MU
- 📊 **Real-time Progress** - Live log output and progress tracking
- 🎯 **Smart Presets** - Optimized configurations for different targets
- 💾 **Settings Persistence** - Remembers your preferences

Perfect for both beginners and advanced users!

---

## Overview

This repository provides easy-to-use Python scripts for drizzle processing in Siril, based on the latest research in image reconstruction:

- **Standard Drizzle** (Fruchter & Hook 2002)
- **Iterative Drizzle** (iDrizzle, Fruchter 2011)
- **Fast Iterative Drizzle** (fiDrizzle-DC, Wang & Li 2017)
- **Fast Iterative Drizzle with Multiplicative Updates** (fiDrizzle-MU, Zhang et al. 2025)

## Features

✨ **Multiple Drizzle Methods**: Choose from standard, iterative, and fast iterative methods
🎯 **Optimized Presets**: Point sources, extended sources, high resolution
🔧 **Flexible Calibration**: Support for both calibrated and uncalibrated workflows
🖥️ **GUI Interface**: Easy-to-use graphical interface for configuration
📊 **Configuration Files**: Save and load processing parameters
🚀 **Command-line Scripts**: Quick processing from the terminal

## Installation

### Prerequisites

1. **Siril**: Install Siril from [free-astro.org/siril](https://www.siril.org/)

2. **Python 3.7+**: Ensure Python is installed

3. **pySiril**: Install the Python bindings for Siril

```bash
python -m pip install pysiril
```

Download the latest version from: https://gitlab.com/free-astro/pysiril/-/releases

### Clone This Repository

```bash
git clone <repository-url>
cd siril-drizzle-scripts
```

## Quick Start

### 1. ⭐ Using VeraLux Drizzle Studio (RECOMMENDED)

**The easiest way to process your images!**

```bash
python veralux_drizzle_studio.py
```

**Complete workflow in 5 steps:**

1. **Select Light Frames** - Browse to your light frames directory
2. **Add Calibration** (Optional) - Select bias, dark, and flat frames for best quality
3. **Choose Method** - Pick from 4 drizzle algorithms (fiDrizzle-MU recommended)
4. **Adjust Parameters** - Fine-tune pixfrac and scale (or use presets)
5. **Click STACK** - Monitor real-time progress and enjoy your result!

The studio provides:
- ✨ **Beautiful Dark UI** inspired by professional imaging software
- 📋 **Real-time Processing Log** with detailed progress information
- 🎯 **Smart Presets** for point sources, extended sources, high resolution
- 💾 **Persistent Settings** remembers your last configuration
- 🛠️ **Complete Control** over all drizzle parameters

### 2. Using the Classic GUI

```bash
python drizzle_gui.py
```

The classic GUI provides:
- **Presets** for common use cases
- **Visual parameter adjustment** with sliders
- **Configuration save/load**
- **One-click processing**

### 3. Standalone fiDrizzle-MU (ADVANCED) ⭐ NEW!

**Direct implementation of the fiDrizzle-MU algorithm!**

#### Option A: GUI (Najlakše!) 🎨

```bash
python fidrizzle_mu_gui.py
# ili
./fidrizzle_mu_gui.py
```

**Funkcionalnosti GUI-a:**
- 📁 File picker za slike (drag & drop support)
- ⚙️ Intuitivno podešavanje parametara
- ⭐ Presets za različite tipove objekata
- 📊 Live progress bar i log output
- 🎨 Dark theme interface

#### Option B: Command Line

```bash
# Basic usage with registered images
./siril_fidrizzle_mu.py r_pp_light_*.fit -o result.fits

# With custom parameters (recommended for point sources)
./siril_fidrizzle_mu.py r_pp_light_*.fit -o result.fits \
    --psr 0.5 \
    --iterations 65 \
    --gamma 1.0

# With shift data file
./siril_fidrizzle_mu.py image_*.fit -o result.fits --shifts shifts.txt
```

**See [FIDRIZZLE_MU_GUIDE.md](FIDRIZZLE_MU_GUIDE.md) for complete documentation!**

This is a **complete standalone implementation** of the algorithm from Zhang et al. (2025), offering:
- ✅ True multiplicative updates (not just Siril's drizzle)
- ✅ Positivity constraints
- ✅ Optimal for point sources and gravitational lenses
- ✅ 5-7x faster convergence than fiDrizzle-DC

### 4. Quick Command-line Scripts

#### Uncalibrated Images (Standard Drizzle)

```bash
python quick_standard_drizzle.py ./lights ./drizzled_output
```

#### Calibrated Images

```bash
python calibrated_drizzle.py ./lights ./biases ./darks ./flats ./drizzled_output
```

#### Point Sources (Stars, Quasars)

```bash
python point_source_drizzle.py ./lights ./drizzled_output
```

### 4. Using Configuration Files

```bash
# Use a preset configuration
python -c "
from drizzle_config import DrizzleConfig
from siril_drizzle import SirilDrizzleProcessor
import json

with open('examples/calibrated_point_sources.json') as f:
    config_dict = json.load(f)

# Create config and process
config = DrizzleConfig(**config_dict)
with SirilDrizzleProcessor(config) as processor:
    processor.process()
"
```

## Drizzle Methods Explained

### Standard Drizzle

**Reference**: Fruchter & Hook (2002) - "A novel image reconstruction method applied to deep Hubble Space Telescope images"

The classic drizzle algorithm that:
- Maps input pixels to output grid
- Allows pixel "shrinking" via **pixfrac** parameter
- Preserves photometry

**Best for**: General-purpose imaging, when you have many dithered frames

**Parameters**:
- `pixfrac = 1.0`: Shift-and-add (more noise correlation)
- `pixfrac = 0.0`: Interlacing (less noise, more artifacts)
- `pixfrac = 0.6-0.8`: **Recommended** (good balance)

### 3D Drizzle (JWST IFU)

**Reference**: Law et al. (2023) - "A 3D Drizzle Algorithm for JWST"

Extends drizzle to 3D spectroscopic data from JWST integral field units (IFU). This handles:
- Two spatial dimensions
- One spectral dimension
- Reduces covariance between spaxels

**Best for**: JWST NIRSpec and MIRI-MRS spectroscopic data

### fiDrizzle-DC (Fast Iterative with Difference Correction)

**Reference**: Wang & Li (2017) - "fiDrizzle: An Iterative Drizzle Method"

Iterative refinement using difference corrections:
- Faster than iDrizzle
- Better convergence
- Reduces noise correlation

**Best for**: When you need better reconstruction than standard drizzle

### fiDrizzle-MU (Fast Iterative with Multiplicative Updates)

**Reference**: Zhang et al. (2025) - "fiDrizzle-MU: A Fast Iterative Drizzle with Multiplicative Updates"

State-of-the-art method using multiplicative updates:
- **5-7x faster convergence** than fiDrizzle-DC
- Superior flux re-concentration
- Excellent for point sources
- Positivity constraints reduce ringing

**Best for**: Point sources, gravitational lenses, high-precision astrometry

**Example from the paper**: Resolved a gravitationally lensed quasar system that was blurred in standard JWST pipeline processing

## Key Parameters

### pixfrac (Drop Size)

Controls how much input pixels are "shrunk" before drizzling:

```
pixfrac = 0.0  →  Interlacing (sharp, but gaps)
pixfrac = 0.5  →  Good for point sources
pixfrac = 0.7  →  General purpose (RECOMMENDED)
pixfrac = 0.8  →  Extended sources
pixfrac = 1.0  →  Shift-and-add (smooth, more correlation)
```

### scale (PSR - Pixel Scale Ratio)

Output pixel scale relative to input:

```
scale = 1.0  →  Same resolution as input
scale = 0.5  →  2x finer sampling (RECOMMENDED)
scale = 0.25 →  4x finer sampling
```

### Iterations (for iterative methods)

From the fiDrizzle-MU paper:
- **65 iterations**: Recommended for JWST point sources
- **100 iterations**: Standard maximum
- Monitor PSNR to find optimal stopping point

### Positivity Constraint

Enforces non-negative flux values:
- **Enabled**: Reduces ringing artifacts (recommended)
- **Disabled**: May allow more detail recovery but with artifacts

## Directory Structure

```
siril-drizzle-scripts/
├── drizzle_config.py              # Configuration module
├── siril_drizzle.py               # Main processing engine
├── drizzle_gui.py                 # Classic GUI interface
├── veralux_drizzle_studio.py      # Modern GUI (VeraLux)
├── siril_drizzle_complete.py      # All-in-one script
├── siril_fidrizzle_mu.py          # ⭐ Standalone fiDrizzle-MU
├── quick_standard_drizzle.py      # Quick standard drizzle
├── calibrated_drizzle.py          # Calibrated processing
├── point_source_drizzle.py        # Point source optimized
├── FIDRIZZLE_MU_GUIDE.md          # ⭐ Complete fiDrizzle-MU guide
├── examples/                      # Example configurations
│   ├── uncalibrated_standard.json
│   ├── calibrated_point_sources.json
│   └── extended_sources.json
├── documentation/                 # Research papers
│   ├── Drizzle.pdf
│   ├── 3D drizzle.pdf
│   ├── fiDrizzle-MU.pdf           # ⭐ Original research paper
│   └── pySiril documentation.md
└── README.md
```

## Workflow Examples

### Example 1: Deep Sky Object (DSO) - Uncalibrated

```python
from drizzle_config import DrizzleConfig, DrizzleMethod, CalibrationMode
from siril_drizzle import SirilDrizzleProcessor

config = DrizzleConfig(
    method=DrizzleMethod.STANDARD,
    calibration_mode=CalibrationMode.UNCALIBRATED,
    pixfrac=0.7,
    scale=0.5,
    input_dir="./m31_lights",
    output_dir="./m31_drizzled",
    debayer=True,  # OSC camera
)

with SirilDrizzleProcessor(config) as processor:
    processor.process()
```

### Example 2: Planetary - Calibrated

```python
config = DrizzleConfig(
    method=DrizzleMethod.STANDARD,
    calibration_mode=CalibrationMode.CALIBRATED,
    pixfrac=0.8,  # Larger for extended source
    scale=0.5,
    input_dir="./jupiter/lights",
    output_dir="./jupiter_drizzled",
    bias_file="./jupiter/biases",
    dark_file="./jupiter/darks",
    flat_file="./jupiter/flats",
    debayer=False,  # Monochrome camera
)

with SirilDrizzleProcessor(config) as processor:
    processor.process()
```

### Example 3: Variable Stars - Point Source Optimized

```python
config = DrizzleConfig(
    method=DrizzleMethod.FAST_MU,  # Best for point sources
    calibration_mode=CalibrationMode.CALIBRATED,
    pixfrac=0.5,  # Smaller for tight PSF
    scale=0.5,
    max_iterations=65,  # From fiDrizzle-MU paper
    apply_positivity=True,
    input_dir="./vstar/lights",
    output_dir="./vstar_drizzled",
    bias_file="./vstar/biases",
    dark_file="./vstar/darks",
    flat_file="./vstar/flats",
)

with SirilDrizzleProcessor(config) as processor:
    processor.process()
```

### Example 4: Standalone fiDrizzle-MU - Maximum Quality

**Direct implementation of the algorithm from Zhang et al. (2025)**

First, register your images in Siril:
```
# In Siril
register pp_light
```

Then use standalone fiDrizzle-MU:
```bash
# For point sources (stars, quasars, gravitational lenses)
./siril_fidrizzle_mu.py r_pp_light_*.fit -o fidrizzle_result.fits \
    --psr 0.5 \
    --iterations 65 \
    --gamma 1.0

# For extended sources (galaxies, nebulae)
./siril_fidrizzle_mu.py r_pp_light_*.fit -o fidrizzle_result.fits \
    --psr 0.5 \
    --iterations 100 \
    --gamma 1.0

# High resolution mode (4x finer sampling)
./siril_fidrizzle_mu.py r_pp_light_*.fit -o fidrizzle_result.fits \
    --psr 0.25 \
    --iterations 150 \
    --gamma 1.0
```

**Or use Python API:**

```python
from siril_fidrizzle_mu import FiDrizzleMU

# Create processor
processor = FiDrizzleMU(
    psr=0.5,              # 2x finer sampling
    gamma=1.0,            # Standard convergence rate
    max_iterations=65,    # As per Zhang et al. 2025
    positivity_constraint=True,  # Suppress ringing
    verbose=True
)

# Load registered images
processor.load_images(['r_pp_light_00001.fit', 'r_pp_light_00002.fit', ...])

# Process
result = processor.process()

# Save
processor.save_result(result, 'fidrizzle_result.fits')
```

**Why use standalone fiDrizzle-MU?**
- Direct implementation of the research paper algorithm
- Better convergence (5-7x faster than fiDrizzle-DC)
- Superior flux concentration for point sources
- Optimal for gravitational lensing studies
- Complete control over all parameters

## Calibration Modes

### UNCALIBRATED

Process raw light frames without calibration:
- Fastest workflow
- Good for quick testing
- Not recommended for science-grade data

### CALIBRATED

Full calibration with master frames:
- Requires bias, dark, and flat frames
- Best image quality
- Recommended for publication-quality data

Process:
1. Scripts stack bias/dark/flat frames into masters
2. Calibrate light frames
3. Apply drizzle to calibrated data

### AUTO

Automatically detects if calibration frames are available

## Performance

From the fiDrizzle-MU paper (Zhang et al. 2025):

| Method | Time (relative) | Iterations to PSNR=20 |
|--------|----------------|----------------------|
| Standard Drizzle | 1x | N/A (single pass) |
| iDrizzle | 36x | 164 |
| fiDrizzle-DC | 4x | 123 |
| **fiDrizzle-MU** | **1x** | **27** ⭐ |

**fiDrizzle-MU is 4-6x faster** than other iterative methods while achieving better reconstruction quality.

## Troubleshooting

### "pySiril not found"

Install pySiril:
```bash
python -m pip install pysiril-0.0.7-py3-none-any.whl
```

Download from: https://gitlab.com/free-astro/pysiril/-/releases

### "Siril command failed"

- Ensure Siril is installed and accessible
- Check that input directory contains valid images
- Verify file paths are correct

### Poor Results

Try adjusting:
- **pixfrac**: Start with 0.7, adjust up/down
- **scale**: Ensure output is oversampled (0.5 recommended)
- **iterations**: For iterative methods, try 50-100 iterations
- **method**: Try fiDrizzle-MU for point sources

### Ringing Artifacts

- Enable **positivity constraint**
- Reduce **pixfrac** (try 0.5-0.6)
- For fiDrizzle methods, reduce iterations

## Advanced Usage

### Custom Algorithm Implementation

The scripts currently use Siril's built-in drizzle command. For a full implementation of fiDrizzle-MU as described in Zhang et al. (2025), you would need to:

1. Implement the multiplicative update rule (Equation 1 from the paper)
2. Add positivity constraints (Equation 2)
3. Monitor convergence (PSNR, OCFR metrics)
4. Optimize iteration count based on noise characteristics

See `fiDrizzle-MU.pdf` for the complete mathematical formulation.

### Integration with Siril Scripts

You can also call these from Siril scripts (`.ssf` files):

```
# In Siril script
requires 0.99.8
cd /path/to/lights
convert light -out=../process
cd ../process
# Then call Python script
```

## References

1. **Fruchter & Hook (2002)**: "A novel image reconstruction method applied to deep Hubble Space Telescope images"
   - Original drizzle paper
   - DOI: 10.1086/338393

2. **Law et al. (2023)**: "A 3D Drizzle Algorithm for JWST and Practical Application to the MIRI Medium Resolution Spectrometer"
   - 3D drizzle for spectroscopic data
   - arXiv:2306.05520

3. **Zhang et al. (2025)**: "fiDrizzle-MU: A Fast Iterative Drizzle with Multiplicative Updates"
   - State-of-the-art multiplicative update method
   - arXiv:2511.09881

4. **Wang & Li (2017)**: "fiDrizzle: An Iterative Drizzle with Difference Correction"
   - Research in Astronomy and Astrophysics, 17, 100

## Contributing

Contributions welcome! Areas for improvement:
- Full fiDrizzle-MU/DC implementation in Python
- Additional quality metrics (SSIM, etc.)
- GPU acceleration
- Automatic parameter optimization
- Integration with other astronomy tools

## License

See LICENSE file.

## Citation

If you use these scripts in your research, please cite:

```bibtex
@software{siril_drizzle_scripts,
  title = {Siril Drizzle Scripts},
  author = {[Your Name]},
  year = {2025},
  url = {https://github.com/...}
}
```

And cite the relevant drizzle papers based on the method you use.

## Contact

For questions or issues, please open an issue on GitHub.

---

**Happy Drizzling! 🌟**
