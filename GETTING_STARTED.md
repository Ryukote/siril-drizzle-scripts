# Getting Started with Siril Drizzle Scripts

Quick guide to get you processing dithered images with drizzle in minutes!

## Step 1: Test Your Installation

```bash
python test_installation.py
```

This will check that all required components are installed. If you see all ✓ PASS, you're ready to go!

## Step 2: Organize Your Images

Create a directory structure like this:

```
my_project/
├── lights/          # Your dithered light frames
│   ├── light_001.fit
│   ├── light_002.fit
│   └── ...
├── biases/          # (Optional) Bias frames
├── darks/           # (Optional) Dark frames
├── flats/           # (Optional) Flat frames
└── output/          # Output will go here
```

## Step 3: Choose Your Processing Method

### Option A: GUI (Easiest) 🖥️

```bash
python drizzle_gui.py
```

1. Click "Browse" to select your lights directory
2. Choose a preset (e.g., "High Resolution" or "Point Sources")
3. Adjust parameters if desired
4. Click "Run Drizzle"

### Option B: Quick Command Line 🚀

**For uncalibrated images:**

```bash
python quick_standard_drizzle.py ./lights ./output
```

**For calibrated images:**

```bash
python calibrated_drizzle.py ./lights ./biases ./darks ./flats ./output
```

**For point sources (stars, quasars):**

```bash
python point_source_drizzle.py ./lights ./output
```

### Option C: Custom Python Script 🐍

Create a file `my_drizzle.py`:

```python
from drizzle_config import DrizzleConfig, DrizzleMethod, CalibrationMode
from siril_drizzle import SirilDrizzleProcessor

# Configure your processing
config = DrizzleConfig(
    method=DrizzleMethod.STANDARD,
    calibration_mode=CalibrationMode.UNCALIBRATED,
    pixfrac=0.7,           # 0.5-0.8 recommended
    scale=0.5,             # 2x oversampling
    input_dir="./lights",
    output_dir="./output",
    debayer=True,          # True for color cameras, False for mono
)

# Process
with SirilDrizzleProcessor(config) as processor:
    processor.process()

print("Done!")
```

Run it:

```bash
python my_drizzle.py
```

## Step 4: Review Your Results

Your drizzled images will be in the output directory. Look for:

- `result_standard.fit` (standard drizzle) or
- `result_iterative_iter*.fit` (iterative drizzle)

Open these in Siril or your preferred FITS viewer.

## Common Scenarios

### Scenario 1: Deep Sky Object (Galaxy, Nebula)

**Goal**: Maximum detail and resolution

```python
config = DrizzleConfig(
    method=DrizzleMethod.STANDARD,
    pixfrac=0.7,      # Good general purpose
    scale=0.5,        # 2x oversampling
    # ... your directories ...
)
```

### Scenario 2: Star Field / Point Sources

**Goal**: Tight PSF, minimal flux spreading

```python
config = DrizzleConfig(
    method=DrizzleMethod.FAST_MU,  # Best for point sources
    pixfrac=0.5,                    # Smaller drop size
    scale=0.5,
    max_iterations=65,              # Based on research
    apply_positivity=True,          # Reduce ringing
    # ... your directories ...
)
```

### Scenario 3: Extended Object (Planet, Moon)

**Goal**: Smooth, extended features

```python
config = DrizzleConfig(
    method=DrizzleMethod.STANDARD,
    pixfrac=0.8,      # Larger for smoother result
    scale=0.5,
    # ... your directories ...
)
```

## Understanding Key Parameters

### pixfrac (How much to shrink pixels)

- **0.5**: Tight, good for point sources
- **0.7**: General purpose **(RECOMMENDED START HERE)**
- **0.8**: Smoother, for extended sources
- **1.0**: Maximum smoothing (shift-and-add)

### scale (Output pixel size)

- **0.5**: 2x finer than input **(RECOMMENDED)**
- **0.33**: 3x finer
- **0.25**: 4x finer

### method (Which algorithm)

- **standard**: Fast, reliable, good for most cases
- **fast_mu**: Best for point sources, cutting-edge research
- **fast_dc**: Alternative iterative method
- **iterative**: Original iterative drizzle

## Calibration Workflow

If you have calibration frames:

```python
config = DrizzleConfig(
    calibration_mode=CalibrationMode.CALIBRATED,
    input_dir="./lights",
    bias_file="./biases",   # Directory with bias frames
    dark_file="./darks",    # Directory with dark frames
    flat_file="./flats",    # Directory with flat frames
    # ... other settings ...
)
```

The script will:
1. Stack your bias frames → master bias
2. Stack your dark frames → master dark
3. Calibrate and stack flats → master flat
4. Calibrate your lights
5. Apply drizzle to calibrated lights

## Tips for Best Results

1. **Use more dithered frames** (4+ recommended, more is better)
2. **Ensure good sub-pixel dithering** (shifts should be fractional pixels)
3. **Start with default parameters** before tweaking
4. **For point sources**: Use smaller pixfrac (0.5-0.6)
5. **For extended sources**: Use larger pixfrac (0.7-0.8)
6. **Monitor your results**: Compare input vs. output

## Troubleshooting Quick Fixes

### Images look too smooth / blurry

→ Decrease `pixfrac` (try 0.5-0.6)

### Images have artifacts / ringing

→ Enable `apply_positivity=True`
→ Or increase `pixfrac` (try 0.7-0.8)

### Processing fails with error

→ Run `python test_installation.py` to check setup
→ Verify image directory paths are correct
→ Check Siril is installed

### Results not much better than input

→ Ensure you have multiple dithered frames (4+)
→ Check that dithering has sub-pixel shifts
→ Try decreasing `scale` parameter (0.5 → 0.33)

## Next Steps

1. **Read the full README.md** for detailed documentation
2. **Experiment with the GUI** to understand parameters
3. **Try the example configs** in `examples/` directory
4. **Read the research papers** in `documentation/` for deep understanding
5. **Save your favorite configs** using the GUI or as JSON files

## Getting Help

- Check `README.md` for comprehensive documentation
- See `examples/` for configuration examples
- Read the research papers for algorithm details
- Report issues on GitHub

---

**Happy imaging! 🌌✨**
