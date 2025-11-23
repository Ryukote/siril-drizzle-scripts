"""
Drizzle GUI Configuration Tool
Simple GUI for configuring Siril drizzle parameters
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
from pathlib import Path

from drizzle_config import DrizzleConfig, DrizzleMethod, CalibrationMode, PRESETS
from siril_drizzle import SirilDrizzleProcessor


class DrizzleGUI:
    """GUI for drizzle configuration"""

    def __init__(self, root):
        self.root = root
        self.root.title("Siril Drizzle Configuration")
        self.root.geometry("800x900")

        self.config = DrizzleConfig()
        self.create_widgets()

    def create_widgets(self):
        """Create GUI widgets"""
        # Main container with scrollbar
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Tabs
        self.create_basic_tab()
        self.create_advanced_tab()
        self.create_calibration_tab()
        self.create_output_tab()

        # Control buttons at bottom
        self.create_control_buttons(main_frame)

    def create_basic_tab(self):
        """Create basic settings tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Basic Settings")

        # Drizzle Method
        ttk.Label(tab, text="Drizzle Method:", font=('Arial', 10, 'bold')).grid(
            row=0, column=0, sticky=tk.W, padx=10, pady=10
        )

        self.method_var = tk.StringVar(value=DrizzleMethod.STANDARD.value)
        method_frame = ttk.Frame(tab)
        method_frame.grid(row=1, column=0, columnspan=2, sticky=tk.W, padx=20, pady=5)

        methods = [
            (DrizzleMethod.STANDARD.value, "Standard Drizzle (Fruchter & Hook 2002)"),
            (DrizzleMethod.FAST_MU.value, "Fast Iterative (fiDrizzle-MU - Recommended for point sources)"),
            (DrizzleMethod.FAST_DC.value, "Fast Iterative DC (fiDrizzle-DC)"),
            (DrizzleMethod.ITERATIVE.value, "Iterative (iDrizzle)"),
        ]

        for i, (value, label) in enumerate(methods):
            ttk.Radiobutton(
                method_frame,
                text=label,
                variable=self.method_var,
                value=value,
                command=self.on_method_change
            ).pack(anchor=tk.W, pady=2)

        # Pixfrac
        ttk.Label(tab, text="Pixfrac (Drop Size):", font=('Arial', 10, 'bold')).grid(
            row=2, column=0, sticky=tk.W, padx=10, pady=(20, 5)
        )

        pixfrac_frame = ttk.Frame(tab)
        pixfrac_frame.grid(row=3, column=0, columnspan=2, sticky=tk.EW, padx=20, pady=5)

        self.pixfrac_var = tk.DoubleVar(value=0.7)
        self.pixfrac_scale = ttk.Scale(
            pixfrac_frame,
            from_=0.0,
            to=1.0,
            variable=self.pixfrac_var,
            orient=tk.HORIZONTAL,
            command=self.update_pixfrac_label
        )
        self.pixfrac_scale.pack(fill=tk.X, side=tk.LEFT, expand=True)

        self.pixfrac_label = ttk.Label(pixfrac_frame, text="0.70")
        self.pixfrac_label.pack(side=tk.LEFT, padx=10)

        ttk.Label(tab, text="0.0 = interlacing, 1.0 = shift-and-add, 0.5-0.8 recommended",
                  font=('Arial', 8, 'italic')).grid(row=4, column=0, columnspan=2, sticky=tk.W, padx=20)

        # Scale (PSR)
        ttk.Label(tab, text="Output Scale (PSR):", font=('Arial', 10, 'bold')).grid(
            row=5, column=0, sticky=tk.W, padx=10, pady=(20, 5)
        )

        scale_frame = ttk.Frame(tab)
        scale_frame.grid(row=6, column=0, columnspan=2, sticky=tk.EW, padx=20, pady=5)

        self.scale_var = tk.DoubleVar(value=0.5)
        self.scale_scale = ttk.Scale(
            scale_frame,
            from_=0.1,
            to=1.0,
            variable=self.scale_var,
            orient=tk.HORIZONTAL,
            command=self.update_scale_label
        )
        self.scale_scale.pack(fill=tk.X, side=tk.LEFT, expand=True)

        self.scale_label = ttk.Label(scale_frame, text="0.50")
        self.scale_label.pack(side=tk.LEFT, padx=10)

        ttk.Label(tab, text="< 1.0 = oversample output (0.5 = 2x finer sampling)",
                  font=('Arial', 8, 'italic')).grid(row=7, column=0, columnspan=2, sticky=tk.W, padx=20)

        # Input Directory
        ttk.Label(tab, text="Input Directory:", font=('Arial', 10, 'bold')).grid(
            row=8, column=0, sticky=tk.W, padx=10, pady=(20, 5)
        )

        input_frame = ttk.Frame(tab)
        input_frame.grid(row=9, column=0, columnspan=2, sticky=tk.EW, padx=20, pady=5)

        self.input_dir_var = tk.StringVar(value="")
        ttk.Entry(input_frame, textvariable=self.input_dir_var).pack(
            fill=tk.X, side=tk.LEFT, expand=True
        )
        ttk.Button(input_frame, text="Browse...", command=self.browse_input).pack(
            side=tk.LEFT, padx=5
        )

        # Preset Selection
        ttk.Label(tab, text="Presets:", font=('Arial', 10, 'bold')).grid(
            row=10, column=0, sticky=tk.W, padx=10, pady=(20, 5)
        )

        preset_frame = ttk.Frame(tab)
        preset_frame.grid(row=11, column=0, columnspan=2, sticky=tk.EW, padx=20, pady=5)

        for preset_name in PRESETS.keys():
            ttk.Button(
                preset_frame,
                text=preset_name.replace('_', ' ').title(),
                command=lambda name=preset_name: self.load_preset(name)
            ).pack(side=tk.LEFT, padx=5)

    def create_advanced_tab(self):
        """Create advanced settings tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Advanced")

        # Iterations (for iterative methods)
        ttk.Label(tab, text="Iterations (for iterative methods):", font=('Arial', 10, 'bold')).grid(
            row=0, column=0, sticky=tk.W, padx=10, pady=10
        )

        iter_frame = ttk.Frame(tab)
        iter_frame.grid(row=1, column=0, columnspan=2, sticky=tk.EW, padx=20, pady=5)

        ttk.Label(iter_frame, text="Max Iterations:").pack(side=tk.LEFT)
        self.max_iter_var = tk.IntVar(value=100)
        ttk.Spinbox(iter_frame, from_=1, to=1000, textvariable=self.max_iter_var, width=10).pack(
            side=tk.LEFT, padx=10
        )

        # Gamma (for fiDrizzle-MU)
        ttk.Label(tab, text="Gamma (step size for fiDrizzle-MU):").grid(
            row=2, column=0, sticky=tk.W, padx=10, pady=10
        )

        self.gamma_var = tk.DoubleVar(value=1.0)
        ttk.Entry(tab, textvariable=self.gamma_var, width=10).grid(
            row=2, column=1, sticky=tk.W, padx=10
        )

        # Positivity Constraint
        self.positivity_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            tab,
            text="Apply Positivity Constraint (suppress ringing, recommended)",
            variable=self.positivity_var
        ).grid(row=3, column=0, columnspan=2, sticky=tk.W, padx=10, pady=10)

        # Convergence threshold
        ttk.Label(tab, text="Convergence Threshold:").grid(
            row=4, column=0, sticky=tk.W, padx=10, pady=10
        )

        self.convergence_var = tk.DoubleVar(value=1e-6)
        ttk.Entry(tab, textvariable=self.convergence_var, width=15).grid(
            row=4, column=1, sticky=tk.W, padx=10
        )

    def create_calibration_tab(self):
        """Create calibration settings tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Calibration")

        # Calibration Mode
        ttk.Label(tab, text="Calibration Mode:", font=('Arial', 10, 'bold')).grid(
            row=0, column=0, sticky=tk.W, padx=10, pady=10
        )

        self.calib_mode_var = tk.StringVar(value=CalibrationMode.UNCALIBRATED.value)
        calib_frame = ttk.Frame(tab)
        calib_frame.grid(row=1, column=0, columnspan=2, sticky=tk.W, padx=20, pady=5)

        ttk.Radiobutton(
            calib_frame,
            text="Uncalibrated (raw images)",
            variable=self.calib_mode_var,
            value=CalibrationMode.UNCALIBRATED.value,
            command=self.on_calib_mode_change
        ).pack(anchor=tk.W)

        ttk.Radiobutton(
            calib_frame,
            text="Calibrated (use master calibration frames)",
            variable=self.calib_mode_var,
            value=CalibrationMode.CALIBRATED.value,
            command=self.on_calib_mode_change
        ).pack(anchor=tk.W)

        # Calibration file selections
        self.calib_files_frame = ttk.LabelFrame(tab, text="Calibration Files")
        self.calib_files_frame.grid(row=2, column=0, columnspan=2, sticky=tk.EW, padx=10, pady=10)

        # Bias
        ttk.Label(self.calib_files_frame, text="Bias:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        self.bias_var = tk.StringVar()
        ttk.Entry(self.calib_files_frame, textvariable=self.bias_var, width=40).grid(
            row=0, column=1, padx=5
        )
        ttk.Button(self.calib_files_frame, text="Browse...",
                   command=lambda: self.browse_calib('bias')).grid(row=0, column=2, padx=5)

        # Dark
        ttk.Label(self.calib_files_frame, text="Dark:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        self.dark_var = tk.StringVar()
        ttk.Entry(self.calib_files_frame, textvariable=self.dark_var, width=40).grid(
            row=1, column=1, padx=5
        )
        ttk.Button(self.calib_files_frame, text="Browse...",
                   command=lambda: self.browse_calib('dark')).grid(row=1, column=2, padx=5)

        # Flat
        ttk.Label(self.calib_files_frame, text="Flat:").grid(row=2, column=0, sticky=tk.W, padx=10, pady=5)
        self.flat_var = tk.StringVar()
        ttk.Entry(self.calib_files_frame, textvariable=self.flat_var, width=40).grid(
            row=2, column=1, padx=5
        )
        ttk.Button(self.calib_files_frame, text="Browse...",
                   command=lambda: self.browse_calib('flat')).grid(row=2, column=2, padx=5)

        # Debayer options
        self.debayer_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            tab,
            text="Debayer (for OSC/color cameras)",
            variable=self.debayer_var
        ).grid(row=3, column=0, columnspan=2, sticky=tk.W, padx=10, pady=5)

        self.equalize_cfa_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            tab,
            text="Equalize CFA channels before debayering",
            variable=self.equalize_cfa_var
        ).grid(row=4, column=0, columnspan=2, sticky=tk.W, padx=10, pady=5)

        self.on_calib_mode_change()

    def create_output_tab(self):
        """Create output settings tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Output")

        # Output Directory
        ttk.Label(tab, text="Output Directory:", font=('Arial', 10, 'bold')).grid(
            row=0, column=0, sticky=tk.W, padx=10, pady=10
        )

        output_frame = ttk.Frame(tab)
        output_frame.grid(row=1, column=0, columnspan=2, sticky=tk.EW, padx=20, pady=5)

        self.output_dir_var = tk.StringVar(value="../drizzled")
        ttk.Entry(output_frame, textvariable=self.output_dir_var).pack(
            fill=tk.X, side=tk.LEFT, expand=True
        )
        ttk.Button(output_frame, text="Browse...", command=self.browse_output).pack(
            side=tk.LEFT, padx=5
        )

        # File Format
        ttk.Label(tab, text="Output Format:").grid(row=2, column=0, sticky=tk.W, padx=10, pady=10)
        self.format_var = tk.StringVar(value="fit")
        ttk.Combobox(tab, textvariable=self.format_var, values=['fit', 'fits', 'fts'],
                     state='readonly', width=10).grid(row=2, column=1, sticky=tk.W, padx=10)

        # Bit Depth
        ttk.Label(tab, text="Bit Depth:").grid(row=3, column=0, sticky=tk.W, padx=10, pady=10)
        self.bitdepth_var = tk.IntVar(value=16)
        ttk.Combobox(tab, textvariable=self.bitdepth_var, values=[16, 32],
                     state='readonly', width=10).grid(row=3, column=1, sticky=tk.W, padx=10)

    def create_control_buttons(self, parent):
        """Create control buttons"""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=10)

        ttk.Button(button_frame, text="Save Config", command=self.save_config).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(button_frame, text="Load Config", command=self.load_config).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(button_frame, text="Run Drizzle", command=self.run_drizzle,
                   style='Accent.TButton').pack(side=tk.RIGHT, padx=5)

    # Event handlers
    def update_pixfrac_label(self, value):
        """Update pixfrac label"""
        self.pixfrac_label.config(text=f"{float(value):.2f}")

    def update_scale_label(self, value):
        """Update scale label"""
        self.scale_label.config(text=f"{float(value):.2f}")

    def on_method_change(self):
        """Handle method change"""
        # Enable/disable iteration settings based on method
        pass

    def on_calib_mode_change(self):
        """Handle calibration mode change"""
        if self.calib_mode_var.get() == CalibrationMode.UNCALIBRATED.value:
            # Disable calibration file selections
            for child in self.calib_files_frame.winfo_children():
                if isinstance(child, (ttk.Entry, ttk.Button)):
                    child.configure(state='disabled')
        else:
            # Enable calibration file selections
            for child in self.calib_files_frame.winfo_children():
                if isinstance(child, (ttk.Entry, ttk.Button)):
                    child.configure(state='normal')

    def browse_input(self):
        """Browse for input directory"""
        directory = filedialog.askdirectory(title="Select Input Directory")
        if directory:
            self.input_dir_var.set(directory)

    def browse_output(self):
        """Browse for output directory"""
        directory = filedialog.askdirectory(title="Select Output Directory")
        if directory:
            self.output_dir_var.set(directory)

    def browse_calib(self, calib_type):
        """Browse for calibration file/directory"""
        directory = filedialog.askdirectory(title=f"Select {calib_type.title()} Directory")
        if directory:
            if calib_type == 'bias':
                self.bias_var.set(directory)
            elif calib_type == 'dark':
                self.dark_var.set(directory)
            elif calib_type == 'flat':
                self.flat_var.set(directory)

    def load_preset(self, preset_name):
        """Load a preset configuration"""
        preset = PRESETS[preset_name]

        self.method_var.set(preset.method.value)
        self.pixfrac_var.set(preset.pixfrac)
        self.scale_var.set(preset.scale)
        self.max_iter_var.set(preset.max_iterations)
        self.gamma_var.set(preset.gamma)
        self.positivity_var.set(preset.apply_positivity)

        messagebox.showinfo("Preset Loaded", f"Loaded preset: {preset_name.replace('_', ' ').title()}")

    def get_config(self) -> DrizzleConfig:
        """Build DrizzleConfig from GUI values"""
        config = DrizzleConfig(
            method=DrizzleMethod(self.method_var.get()),
            calibration_mode=CalibrationMode(self.calib_mode_var.get()),
            pixfrac=self.pixfrac_var.get(),
            scale=self.scale_var.get(),
            max_iterations=self.max_iter_var.get(),
            gamma=self.gamma_var.get(),
            apply_positivity=self.positivity_var.get(),
            convergence_threshold=self.convergence_var.get(),
            input_dir=self.input_dir_var.get(),
            output_dir=self.output_dir_var.get(),
            bias_file=self.bias_var.get() or None,
            dark_file=self.dark_var.get() or None,
            flat_file=self.flat_var.get() or None,
            debayer=self.debayer_var.get(),
            equalize_cfa=self.equalize_cfa_var.get(),
            output_format=self.format_var.get(),
            bit_depth=self.bitdepth_var.get(),
        )

        return config

    def save_config(self):
        """Save configuration to JSON file"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if filename:
            config = self.get_config()
            config_dict = {
                'method': config.method.value,
                'calibration_mode': config.calibration_mode.value,
                'pixfrac': config.pixfrac,
                'scale': config.scale,
                'max_iterations': config.max_iterations,
                'gamma': config.gamma,
                'apply_positivity': config.apply_positivity,
                'convergence_threshold': config.convergence_threshold,
                'input_dir': config.input_dir,
                'output_dir': config.output_dir,
                'bias_file': config.bias_file,
                'dark_file': config.dark_file,
                'flat_file': config.flat_file,
                'debayer': config.debayer,
                'equalize_cfa': config.equalize_cfa,
                'output_format': config.output_format,
                'bit_depth': config.bit_depth,
            }

            with open(filename, 'w') as f:
                json.dump(config_dict, f, indent=2)

            messagebox.showinfo("Success", f"Configuration saved to {filename}")

    def load_config(self):
        """Load configuration from JSON file"""
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if filename:
            with open(filename, 'r') as f:
                config_dict = json.load(f)

            # Update GUI
            self.method_var.set(config_dict.get('method', DrizzleMethod.STANDARD.value))
            self.calib_mode_var.set(config_dict.get('calibration_mode', CalibrationMode.UNCALIBRATED.value))
            self.pixfrac_var.set(config_dict.get('pixfrac', 0.7))
            self.scale_var.set(config_dict.get('scale', 0.5))
            self.max_iter_var.set(config_dict.get('max_iterations', 100))
            self.gamma_var.set(config_dict.get('gamma', 1.0))
            self.positivity_var.set(config_dict.get('apply_positivity', True))
            self.convergence_var.set(config_dict.get('convergence_threshold', 1e-6))
            self.input_dir_var.set(config_dict.get('input_dir', ''))
            self.output_dir_var.set(config_dict.get('output_dir', '../drizzled'))
            self.bias_var.set(config_dict.get('bias_file', ''))
            self.dark_var.set(config_dict.get('dark_file', ''))
            self.flat_var.set(config_dict.get('flat_file', ''))
            self.debayer_var.set(config_dict.get('debayer', True))
            self.equalize_cfa_var.set(config_dict.get('equalize_cfa', True))
            self.format_var.set(config_dict.get('output_format', 'fit'))
            self.bitdepth_var.set(config_dict.get('bit_depth', 16))

            self.on_calib_mode_change()
            messagebox.showinfo("Success", f"Configuration loaded from {filename}")

    def run_drizzle(self):
        """Run the drizzle processing"""
        try:
            config = self.get_config()
            config.validate()

            # Confirm with user
            msg = f"Ready to process:\n\n{config.get_description()}\n\nContinue?"
            if messagebox.askyesno("Confirm Processing", msg):
                # Run in separate thread to keep GUI responsive
                # For now, simple blocking call
                with SirilDrizzleProcessor(config) as processor:
                    processor.process()

                messagebox.showinfo("Success", "Drizzle processing complete!")

        except Exception as e:
            messagebox.showerror("Error", f"Error during processing:\n{str(e)}")


def main():
    """Main entry point"""
    root = tk.Tk()
    app = DrizzleGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
