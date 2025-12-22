##############################################
# VeraLux — Drizzle Studio
# Professional Drizzle Stacking Interface
# Author: Based on VeraLux Design System (2025)
##############################################

# SPDX-License-Identifier: GPL-3.0-or-later
# Version 1.0.0
#
# Credits
# -------
#   • UI Design: Inspired by VeraLux StarComposer
#   • Drizzle Engine: Siril + pySiril
#   • Methods: Standard, iDrizzle, fiDrizzle-DC, fiDrizzle-MU

"""
Overview
--------
A professional GUI for Siril drizzle processing with full calibration support.

VeraLux Drizzle Studio provides an intuitive interface for advanced image
stacking using state-of-the-art drizzle algorithms. It handles the complete
workflow from calibration to final stacked output.

Key Features v1.0
-----------------
• **Modern Interface**: Dark theme, intuitive controls
• **Complete Workflow**: Calibration + Drizzle in one click
• **4 Drizzle Methods**: Standard, iDrizzle, fiDrizzle-DC, fiDrizzle-MU
• **Real-time Progress**: Live log output and progress tracking
• **Smart Presets**: Optimized for point sources, DSO, planetary
• **Flexible Calibration**: Optional bias, dark, flat frames

Drizzle Methods
---------------
• **Standard**: Classic drizzle (Fruchter & Hook 2002)
• **iDrizzle**: Iterative drizzle for better reconstruction
• **fiDrizzle-DC**: Fast iterative with difference correction
• **fiDrizzle-MU**: Fast iterative with multiplicative updates (BEST for point sources)

Usage
-----
1. **Load Images**: Select light frames directory
2. **Calibration** (Optional): Select bias, dark, flat frames
3. **Method**: Choose drizzle algorithm
4. **Parameters**: Adjust pixfrac and scale
5. **Process**: Click STACK and monitor progress

Inputs
------
• Lights: Raw/uncalibrated light frames (FITS, RAW, etc.)
• Bias: Bias/offset frames (optional)
• Dark: Dark frames (optional)
• Flat: Flat field frames (optional)

Outputs
-------
• Calibrated + Drizzled FITS file
• Processing log
• Quality metrics

Compatibility
-------------
• Siril 1.2+
• Python 3.7+
• Dependencies: PyQt6, pysiril

License
-------
Released under GPL-3.0-or-later.
"""

import sys
import os
from pathlib import Path
import subprocess
import threading
from datetime import datetime

try:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
        QWidget, QLabel, QSlider, QPushButton, QGroupBox,
        QComboBox, QCheckBox, QFileDialog, QTextEdit,
        QProgressBar, QLineEdit, QSpinBox, QRadioButton,
        QButtonGroup, QMessageBox
    )
    from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QSettings
    from PyQt6.QtGui import QFont, QTextCursor
except ImportError:
    print("Error: PyQt6 not found. Installing...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "PyQt6"])
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
        QWidget, QLabel, QSlider, QPushButton, QGroupBox,
        QComboBox, QCheckBox, QFileDialog, QTextEdit,
        QProgressBar, QLineEdit, QSpinBox, QRadioButton,
        QButtonGroup, QMessageBox
    )
    from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QSettings
    from PyQt6.QtGui import QFont, QTextCursor

from drizzle_config import DrizzleConfig, DrizzleMethod, CalibrationMode, PRESETS
from siril_drizzle import SirilDrizzleProcessor

# ---------------------
#  VERALUX THEME
# ---------------------

VERALUX_DARK = """
QWidget {
    background-color: #2b2b2b;
    color: #e0e0e0;
    font-size: 10pt;
    font-family: 'Segoe UI', Arial, sans-serif;
}

QToolTip {
    background-color: #333333;
    color: #ffffff;
    border: 1px solid #88aaff;
    padding: 4px;
}

QGroupBox {
    border: 1px solid #444444;
    margin-top: 8px;
    font-weight: bold;
    border-radius: 4px;
    padding-top: 14px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
    color: #88aaff;
}

QLabel {
    color: #cccccc;
}

QLabel#SectionHeader {
    color: #88aaff;
    font-size: 11pt;
    font-weight: bold;
}

QCheckBox, QRadioButton {
    spacing: 5px;
    color: #cccccc;
}

QCheckBox::indicator, QRadioButton::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #666666;
    background: #3c3c3c;
    border-radius: 3px;
}

QCheckBox::indicator:checked, QRadioButton::indicator:checked {
    background-color: #285299;
    border: 1px solid #88aaff;
}

QRadioButton::indicator {
    border-radius: 8px;
}

/* Sliders */
QSlider {
    min-height: 24px;
}

QSlider::groove:horizontal {
    background: #444444;
    height: 6px;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background-color: #cccccc;
    border: 1px solid #666666;
    width: 16px;
    height: 16px;
    margin: -5px 0;
    border-radius: 8px;
}

QSlider::handle:horizontal:hover {
    background-color: #ffffff;
    border-color: #88aaff;
}

/* Primary Control Slider */
QSlider#PrimarySlider::handle:horizontal {
    background-color: #ffb000;
    border: 1px solid #cc8800;
}

QSlider#PrimarySlider::handle:horizontal:hover {
    background-color: #ffcc00;
    border-color: #ffffff;
}

QSlider#PrimarySlider::groove:horizontal {
    background: #554400;
}

/* Buttons */
QPushButton {
    background-color: #444444;
    color: #dddddd;
    border: 1px solid #666666;
    border-radius: 4px;
    padding: 8px 16px;
    font-weight: bold;
    min-height: 28px;
}

QPushButton:hover {
    background-color: #555555;
    border-color: #888888;
}

QPushButton:pressed {
    background-color: #333333;
}

QPushButton:disabled {
    background-color: #2b2b2b;
    color: #555555;
    border-color: #444444;
}

QPushButton#ProcessButton {
    background-color: #285299;
    border: 1px solid #1e3f7a;
    font-size: 11pt;
    min-height: 40px;
}

QPushButton#ProcessButton:hover {
    background-color: #355ea1;
}

QPushButton#ProcessButton:disabled {
    background-color: #1a3050;
    color: #666666;
}

QPushButton#BrowseButton {
    min-width: 80px;
}

QPushButton#PresetButton {
    background-color: #3c3c3c;
    min-width: 100px;
}

QPushButton#PresetButton:hover {
    background-color: #4a4a4a;
}

QPushButton#CloseButton {
    background-color: #5a2a2a;
    border: 1px solid #804040;
}

QPushButton#CloseButton:hover {
    background-color: #7a3a3a;
}

/* ComboBox */
QComboBox {
    background-color: #3c3c3c;
    color: #ffffff;
    border: 1px solid #555555;
    padding: 5px 10px;
    border-radius: 3px;
    min-height: 24px;
}

QComboBox:hover {
    border-color: #777777;
}

QComboBox::drop-down {
    border: none;
    width: 20px;
}

QComboBox::down-arrow {
    width: 0;
    height: 0;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #aaaaaa;
    margin-right: 6px;
}

QComboBox QAbstractItemView {
    background-color: #3c3c3c;
    color: #ffffff;
    selection-background-color: #285299;
    border: 1px solid #555555;
}

/* LineEdit */
QLineEdit {
    background-color: #3c3c3c;
    color: #ffffff;
    border: 1px solid #555555;
    border-radius: 3px;
    padding: 5px;
    min-height: 20px;
}

QLineEdit:focus {
    border-color: #88aaff;
}

QLineEdit:disabled {
    background-color: #2b2b2b;
    color: #666666;
}

/* SpinBox */
QSpinBox {
    background-color: #3c3c3c;
    color: #ffffff;
    border: 1px solid #555555;
    border-radius: 3px;
    padding: 5px;
}

QSpinBox:focus {
    border-color: #88aaff;
}

/* TextEdit (Log) */
QTextEdit {
    background-color: #1a1a1a;
    color: #d0d0d0;
    border: 1px solid #444444;
    border-radius: 4px;
    font-family: 'Consolas', 'Monaco', monospace;
    font-size: 9pt;
}

/* Progress Bar */
QProgressBar {
    background-color: #3c3c3c;
    border: 1px solid #555555;
    border-radius: 4px;
    text-align: center;
    color: #ffffff;
    min-height: 24px;
}

QProgressBar::chunk {
    background-color: #285299;
    border-radius: 3px;
}
"""

VERSION = "1.0.0"

# =============================================================================
#  PROCESSING THREAD
# =============================================================================

class DrizzleWorker(QThread):
    """Background thread for drizzle processing"""

    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(bool, str)  # success, message

    def __init__(self, config: DrizzleConfig):
        super().__init__()
        self.config = config

    def run(self):
        """Run drizzle processing"""
        try:
            self.log_signal.emit("="*60)
            self.log_signal.emit("VERALUX DRIZZLE STUDIO - Processing Started")
            self.log_signal.emit(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            self.log_signal.emit("="*60)
            self.log_signal.emit("")

            # Show configuration
            self.log_signal.emit("Configuration:")
            self.log_signal.emit(f"  Method: {self.config.method.value}")
            self.log_signal.emit(f"  Calibration: {self.config.calibration_mode.value}")
            self.log_signal.emit(f"  Pixfrac: {self.config.pixfrac}")
            self.log_signal.emit(f"  Scale: {self.config.scale}")
            self.log_signal.emit("")

            # Validate
            self.progress_signal.emit(5)
            self.config.validate()

            # Process
            self.log_signal.emit("Starting Siril drizzle processor...")
            self.progress_signal.emit(10)

            with SirilDrizzleProcessor(self.config) as processor:
                # This would normally have callbacks for progress
                # For now, we'll update progress in stages
                self.progress_signal.emit(20)
                processor.process()
                self.progress_signal.emit(100)

            self.log_signal.emit("")
            self.log_signal.emit("="*60)
            self.log_signal.emit("✓ PROCESSING COMPLETE!")
            self.log_signal.emit("="*60)

            self.finished_signal.emit(True, "Drizzle processing completed successfully!")

        except Exception as e:
            error_msg = f"Error: {str(e)}"
            self.log_signal.emit("")
            self.log_signal.emit("="*60)
            self.log_signal.emit(f"✗ ERROR: {error_msg}")
            self.log_signal.emit("="*60)
            self.finished_signal.emit(False, error_msg)

# =============================================================================
#  RESET SLIDER (Double-click to reset)
# =============================================================================

class ResetSlider(QSlider):
    """Slider that resets to default on double-click"""

    def __init__(self, orientation, default_val=0, parent=None):
        super().__init__(orientation, parent)
        self.default_val = default_val

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.setValue(self.default_val)
            event.accept()
        else:
            super().mouseDoubleClickEvent(event)

# =============================================================================
#  MAIN GUI
# =============================================================================

class VeraLuxDrizzleStudio(QMainWindow):
    """Main application window"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"VeraLux Drizzle Studio v{VERSION}")
        self.setStyleSheet(VERALUX_DARK)
        self.resize(1200, 800)

        # Settings persistence
        self.settings = QSettings("VeraLux", "DrizzleStudio")

        # Worker thread
        self.worker = None

        # Initialize UI
        self.init_ui()
        self.load_settings()
        self.update_calibration_ui()

    def init_ui(self):
        """Initialize user interface"""
        main = QWidget()
        self.setCentralWidget(main)
        layout = QHBoxLayout(main)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Left Panel (Controls)
        left_panel = self.create_left_panel()
        layout.addWidget(left_panel, stretch=2)

        # Right Panel (Log)
        right_panel = self.create_right_panel()
        layout.addWidget(right_panel, stretch=3)

    def create_left_panel(self):
        """Create left control panel"""
        container = QWidget()
        container.setFixedWidth(450)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # Header
        header = QLabel("VeraLux Drizzle Studio")
        header.setObjectName("SectionHeader")
        header_font = QFont()
        header_font.setPointSize(14)
        header_font.setBold(True)
        header.setFont(header_font)
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)

        version_label = QLabel(f"v{VERSION} — Professional Drizzle Stacking")
        version_label.setStyleSheet("color: #888888; font-size: 8pt; font-style: italic;")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version_label)

        # 1. Input Files
        layout.addWidget(self.create_input_group())

        # 2. Calibration Files
        layout.addWidget(self.create_calibration_group())

        # 3. Drizzle Method
        layout.addWidget(self.create_method_group())

        # 4. Parameters
        layout.addWidget(self.create_parameters_group())

        # 5. Presets
        layout.addWidget(self.create_presets_group())

        # 6. Action Buttons
        layout.addWidget(self.create_action_buttons())

        layout.addStretch()

        return container

    def create_input_group(self):
        """Create input files group"""
        group = QGroupBox("1. Input Files")
        layout = QVBoxLayout(group)

        # Light Frames
        layout.addWidget(QLabel("Light Frames:"))
        row = QHBoxLayout()
        self.input_lights = QLineEdit()
        self.input_lights.setPlaceholderText("Select directory with light frames...")
        row.addWidget(self.input_lights)

        btn = QPushButton("Browse...")
        btn.setObjectName("BrowseButton")
        btn.clicked.connect(lambda: self.browse_directory(self.input_lights, "Select Light Frames Directory"))
        row.addWidget(btn)
        layout.addLayout(row)

        # Output Directory
        layout.addWidget(QLabel("Output Directory:"))
        row = QHBoxLayout()
        self.output_dir = QLineEdit()
        self.output_dir.setText("../drizzled")
        self.output_dir.setPlaceholderText("Output directory for results...")
        row.addWidget(self.output_dir)

        btn = QPushButton("Browse...")
        btn.setObjectName("BrowseButton")
        btn.clicked.connect(lambda: self.browse_directory(self.output_dir, "Select Output Directory"))
        row.addWidget(btn)
        layout.addLayout(row)

        return group

    def create_calibration_group(self):
        """Create calibration files group"""
        group = QGroupBox("2. Calibration (Optional)")
        layout = QVBoxLayout(group)

        # Calibration Mode
        self.calib_mode_group = QButtonGroup()

        row = QHBoxLayout()
        self.radio_uncalib = QRadioButton("Uncalibrated")
        self.radio_uncalib.setChecked(True)
        self.radio_uncalib.setToolTip("Process raw images without calibration")
        self.radio_uncalib.toggled.connect(self.update_calibration_ui)
        self.calib_mode_group.addButton(self.radio_uncalib)
        row.addWidget(self.radio_uncalib)

        self.radio_calib = QRadioButton("Calibrated")
        self.radio_calib.setToolTip("Use master bias, dark, and flat frames")
        self.radio_calib.toggled.connect(self.update_calibration_ui)
        self.calib_mode_group.addButton(self.radio_calib)
        row.addWidget(self.radio_calib)

        layout.addLayout(row)

        # Calibration Files (initially disabled)
        self.calib_frame = QWidget()
        calib_layout = QVBoxLayout(self.calib_frame)
        calib_layout.setContentsMargins(0, 5, 0, 0)

        # Bias
        calib_layout.addWidget(QLabel("Bias Frames:"))
        row = QHBoxLayout()
        self.input_bias = QLineEdit()
        self.input_bias.setPlaceholderText("Optional: bias/offset frames...")
        row.addWidget(self.input_bias)
        self.btn_bias = QPushButton("Browse...")
        self.btn_bias.setObjectName("BrowseButton")
        self.btn_bias.clicked.connect(lambda: self.browse_directory(self.input_bias, "Select Bias Frames Directory"))
        row.addWidget(self.btn_bias)
        calib_layout.addLayout(row)

        # Dark
        calib_layout.addWidget(QLabel("Dark Frames:"))
        row = QHBoxLayout()
        self.input_dark = QLineEdit()
        self.input_dark.setPlaceholderText("Optional: dark frames...")
        row.addWidget(self.input_dark)
        self.btn_dark = QPushButton("Browse...")
        self.btn_dark.setObjectName("BrowseButton")
        self.btn_dark.clicked.connect(lambda: self.browse_directory(self.input_dark, "Select Dark Frames Directory"))
        row.addWidget(self.btn_dark)
        calib_layout.addLayout(row)

        # Flat
        calib_layout.addWidget(QLabel("Flat Frames:"))
        row = QHBoxLayout()
        self.input_flat = QLineEdit()
        self.input_flat.setPlaceholderText("Optional: flat field frames...")
        row.addWidget(self.input_flat)
        self.btn_flat = QPushButton("Browse...")
        self.btn_flat.setObjectName("BrowseButton")
        self.btn_flat.clicked.connect(lambda: self.browse_directory(self.input_flat, "Select Flat Frames Directory"))
        row.addWidget(self.btn_flat)
        calib_layout.addLayout(row)

        layout.addWidget(self.calib_frame)

        # Debayer option
        self.chk_debayer = QCheckBox("Debayer (OSC/Color Camera)")
        self.chk_debayer.setChecked(True)
        self.chk_debayer.setToolTip("Enable for color/OSC cameras (Bayer matrix)")
        layout.addWidget(self.chk_debayer)

        return group

    def create_method_group(self):
        """Create drizzle method group"""
        group = QGroupBox("3. Drizzle Method")
        layout = QVBoxLayout(group)

        self.method_combo = QComboBox()
        self.method_combo.addItem("Standard Drizzle (Fruchter & Hook 2002)", DrizzleMethod.STANDARD)
        self.method_combo.addItem("fiDrizzle-MU — Fast Multiplicative (★ RECOMMENDED)", DrizzleMethod.FAST_MU)
        self.method_combo.addItem("fiDrizzle-DC — Fast Difference Correction", DrizzleMethod.FAST_DC)
        self.method_combo.addItem("iDrizzle — Iterative", DrizzleMethod.ITERATIVE)
        self.method_combo.setCurrentIndex(1)  # Default to FAST_MU
        self.method_combo.currentIndexChanged.connect(self.update_method_ui)
        layout.addWidget(self.method_combo)

        # Iterations (for iterative methods)
        self.iter_frame = QWidget()
        iter_layout = QHBoxLayout(self.iter_frame)
        iter_layout.setContentsMargins(0, 5, 0, 0)

        iter_layout.addWidget(QLabel("Iterations:"))
        self.spin_iterations = QSpinBox()
        self.spin_iterations.setRange(1, 1000)
        self.spin_iterations.setValue(100)
        self.spin_iterations.setToolTip("Number of iterations for iterative methods")
        iter_layout.addWidget(self.spin_iterations)

        iter_layout.addWidget(QLabel("  Gamma:"))
        self.spin_gamma = QSpinBox()
        self.spin_gamma.setRange(1, 100)
        self.spin_gamma.setValue(10)
        self.spin_gamma.setToolTip("Step size for fiDrizzle-MU (divide by 10)")
        iter_layout.addWidget(self.spin_gamma)

        iter_layout.addStretch()

        layout.addWidget(self.iter_frame)

        # Positivity constraint
        self.chk_positivity = QCheckBox("Positivity Constraint (Suppress Ringing)")
        self.chk_positivity.setChecked(True)
        self.chk_positivity.setToolTip("Enforce non-negative flux values - reduces artifacts")
        layout.addWidget(self.chk_positivity)

        return group

    def create_parameters_group(self):
        """Create parameters group"""
        group = QGroupBox("4. Drizzle Parameters")
        layout = QVBoxLayout(group)

        # Pixfrac
        self.lbl_pixfrac = QLabel("Pixfrac (Drop Size): 0.70")
        layout.addWidget(self.lbl_pixfrac)

        self.slider_pixfrac = ResetSlider(Qt.Orientation.Horizontal, 70)
        self.slider_pixfrac.setObjectName("PrimarySlider")
        self.slider_pixfrac.setRange(0, 100)
        self.slider_pixfrac.setValue(70)
        self.slider_pixfrac.setToolTip(
            "Drop size parameter:\n"
            "  0.0 = Interlacing (sharp, gaps)\n"
            "  0.5 = Point sources\n"
            "  0.7 = General purpose (RECOMMENDED)\n"
            "  0.8 = Extended sources\n"
            "  1.0 = Shift-and-add (smooth)\n"
            "Double-click to reset"
        )
        self.slider_pixfrac.valueChanged.connect(self.update_parameter_labels)
        layout.addWidget(self.slider_pixfrac)

        # Scale
        self.lbl_scale = QLabel("Output Scale (PSR): 0.50")
        layout.addWidget(self.lbl_scale)

        self.slider_scale = ResetSlider(Qt.Orientation.Horizontal, 50)
        self.slider_scale.setRange(10, 100)
        self.slider_scale.setValue(50)
        self.slider_scale.setToolTip(
            "Output pixel scale ratio:\n"
            "  1.0 = Same as input\n"
            "  0.5 = 2x finer sampling (RECOMMENDED)\n"
            "  0.25 = 4x finer sampling\n"
            "Double-click to reset"
        )
        self.slider_scale.valueChanged.connect(self.update_parameter_labels)
        layout.addWidget(self.slider_scale)

        hint = QLabel("💡 Tip: Use pixfrac=0.7, scale=0.5 for best results")
        hint.setStyleSheet("color: #888888; font-size: 8pt; font-style: italic;")
        layout.addWidget(hint)

        return group

    def create_presets_group(self):
        """Create presets group"""
        group = QGroupBox("5. Quick Presets")
        layout = QHBoxLayout(group)

        for preset_name, preset_config in PRESETS.items():
            btn = QPushButton(preset_name.replace('_', ' ').title())
            btn.setObjectName("PresetButton")
            btn.clicked.connect(lambda checked, p=preset_config: self.load_preset(p))
            layout.addWidget(btn)

        return group

    def create_action_buttons(self):
        """Create action buttons"""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 10, 0, 0)

        # Help
        btn_help = QPushButton("?")
        btn_help.setFixedWidth(40)
        btn_help.setToolTip("Show usage guide")
        btn_help.clicked.connect(self.show_help)
        layout.addWidget(btn_help)

        layout.addStretch()

        # Close
        btn_close = QPushButton("Close")
        btn_close.setObjectName("CloseButton")
        btn_close.clicked.connect(self.close)
        layout.addWidget(btn_close)

        # Process
        self.btn_process = QPushButton("⚡ STACK IMAGES")
        self.btn_process.setObjectName("ProcessButton")
        self.btn_process.clicked.connect(self.start_processing)
        layout.addWidget(self.btn_process)

        return container

    def create_right_panel(self):
        """Create right panel (log and progress)"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        # Title
        header = QLabel("Processing Log")
        header.setObjectName("SectionHeader")
        layout.addWidget(header)

        # Progress bar
        self.progress = QProgressBar()
        self.progress.setValue(0)
        layout.addWidget(self.progress)

        # Log output
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        layout.addWidget(self.log_output)

        # Initial message
        self.log("="*60)
        self.log("VERALUX DRIZZLE STUDIO")
        self.log(f"Version {VERSION}")
        self.log("="*60)
        self.log("")
        self.log("Welcome! Configure your drizzle stack on the left,")
        self.log("then click 'STACK IMAGES' to begin processing.")
        self.log("")
        self.log("Ready.")

        return container

    # -------------------------
    #  UI UPDATE METHODS
    # -------------------------

    def update_calibration_ui(self):
        """Enable/disable calibration inputs based on mode"""
        is_calibrated = self.radio_calib.isChecked()

        self.input_bias.setEnabled(is_calibrated)
        self.input_dark.setEnabled(is_calibrated)
        self.input_flat.setEnabled(is_calibrated)
        self.btn_bias.setEnabled(is_calibrated)
        self.btn_dark.setEnabled(is_calibrated)
        self.btn_flat.setEnabled(is_calibrated)

    def update_method_ui(self):
        """Show/hide iteration controls based on method"""
        method = self.method_combo.currentData()
        is_iterative = method in [DrizzleMethod.ITERATIVE, DrizzleMethod.FAST_DC, DrizzleMethod.FAST_MU]
        self.iter_frame.setVisible(is_iterative)

    def update_parameter_labels(self):
        """Update parameter labels"""
        pixfrac = self.slider_pixfrac.value() / 100.0
        scale = self.slider_scale.value() / 100.0

        self.lbl_pixfrac.setText(f"Pixfrac (Drop Size): <b>{pixfrac:.2f}</b>")
        self.lbl_scale.setText(f"Output Scale (PSR): <b>{scale:.2f}</b>")

    def browse_directory(self, line_edit: QLineEdit, title: str):
        """Browse for directory"""
        current = line_edit.text()
        if current and os.path.exists(current):
            start_dir = current
        else:
            start_dir = os.path.expanduser("~")

        directory = QFileDialog.getExistingDirectory(self, title, start_dir)
        if directory:
            line_edit.setText(directory)

    def load_preset(self, preset: DrizzleConfig):
        """Load a preset configuration"""
        # Method
        for i in range(self.method_combo.count()):
            if self.method_combo.itemData(i) == preset.method:
                self.method_combo.setCurrentIndex(i)
                break

        # Parameters
        self.slider_pixfrac.setValue(int(preset.pixfrac * 100))
        self.slider_scale.setValue(int(preset.scale * 100))

        # Iterations
        self.spin_iterations.setValue(preset.max_iterations)
        self.spin_gamma.setValue(int(preset.gamma * 10))

        # Positivity
        self.chk_positivity.setChecked(preset.apply_positivity)

        self.log(f"✓ Loaded preset: {preset.method.value}")

    # -------------------------
    #  PROCESSING
    # -------------------------

    def get_config(self) -> DrizzleConfig:
        """Build configuration from UI"""
        # Calibration mode
        if self.radio_calib.isChecked():
            calib_mode = CalibrationMode.CALIBRATED
        else:
            calib_mode = CalibrationMode.UNCALIBRATED

        # Build config
        config = DrizzleConfig(
            method=self.method_combo.currentData(),
            calibration_mode=calib_mode,
            pixfrac=self.slider_pixfrac.value() / 100.0,
            scale=self.slider_scale.value() / 100.0,
            max_iterations=self.spin_iterations.value(),
            gamma=self.spin_gamma.value() / 10.0,
            apply_positivity=self.chk_positivity.isChecked(),
            input_dir=self.input_lights.text(),
            output_dir=self.output_dir.text(),
            bias_file=self.input_bias.text() if self.input_bias.text() else None,
            dark_file=self.input_dark.text() if self.input_dark.text() else None,
            flat_file=self.input_flat.text() if self.input_flat.text() else None,
            debayer=self.chk_debayer.isChecked(),
        )

        return config

    def start_processing(self):
        """Start drizzle processing"""
        try:
            # Get and validate config
            config = self.get_config()
            config.validate()

            # Confirm
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Question)
            msg.setWindowTitle("Confirm Processing")
            msg.setText("Ready to start drizzle processing?")
            msg.setInformativeText(
                f"Method: {config.method.value}\n"
                f"Calibration: {config.calibration_mode.value}\n"
                f"Pixfrac: {config.pixfrac}\n"
                f"Scale: {config.scale}\n"
            )
            msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

            if msg.exec() == QMessageBox.StandardButton.Yes:
                # Clear log
                self.log_output.clear()
                self.progress.setValue(0)

                # Disable controls
                self.btn_process.setEnabled(False)

                # Start worker thread
                self.worker = DrizzleWorker(config)
                self.worker.log_signal.connect(self.log)
                self.worker.progress_signal.connect(self.progress.setValue)
                self.worker.finished_signal.connect(self.processing_finished)
                self.worker.start()

        except Exception as e:
            QMessageBox.critical(self, "Configuration Error", str(e))

    def processing_finished(self, success: bool, message: str):
        """Handle processing completion"""
        self.btn_process.setEnabled(True)

        if success:
            QMessageBox.information(self, "Success", message)
        else:
            QMessageBox.critical(self, "Error", message)

    def log(self, message: str):
        """Append message to log"""
        self.log_output.append(message)
        # Auto-scroll to bottom
        self.log_output.moveCursor(QTextCursor.MoveOperation.End)

    # -------------------------
    #  SETTINGS PERSISTENCE
    # -------------------------

    def load_settings(self):
        """Load saved settings"""
        try:
            self.output_dir.setText(self.settings.value("output_dir", "../drizzled"))
            self.chk_debayer.setChecked(self.settings.value("debayer", True, type=bool))

            pixfrac = self.settings.value("pixfrac", 70, type=int)
            scale = self.settings.value("scale", 50, type=int)

            self.slider_pixfrac.setValue(pixfrac)
            self.slider_scale.setValue(scale)

        except Exception:
            pass

    def save_settings(self):
        """Save current settings"""
        try:
            self.settings.setValue("output_dir", self.output_dir.text())
            self.settings.setValue("debayer", self.chk_debayer.isChecked())
            self.settings.setValue("pixfrac", self.slider_pixfrac.value())
            self.settings.setValue("scale", self.slider_scale.value())
        except Exception:
            pass

    def closeEvent(self, event):
        """Handle window close"""
        self.save_settings()
        event.accept()

    # -------------------------
    #  HELP
    # -------------------------

    def show_help(self):
        """Show help dialog"""
        help_text = """
<h2>VeraLux Drizzle Studio - Quick Guide</h2>

<h3>Workflow</h3>
<ol>
<li><b>Input Files</b>: Select your light frames directory</li>
<li><b>Calibration</b>: Optional - provide bias, dark, flat frames for best quality</li>
<li><b>Method</b>: Choose drizzle algorithm (fiDrizzle-MU recommended)</li>
<li><b>Parameters</b>: Adjust pixfrac and scale (defaults are optimal)</li>
<li><b>Process</b>: Click "STACK IMAGES" and monitor progress</li>
</ol>

<h3>Drizzle Methods</h3>
<ul>
<li><b>Standard</b>: Classic drizzle, fast and reliable</li>
<li><b>fiDrizzle-MU</b>: ★ Best for point sources (stars)</li>
<li><b>fiDrizzle-DC</b>: Good balance of speed and quality</li>
<li><b>iDrizzle</b>: Original iterative method</li>
</ul>

<h3>Key Parameters</h3>
<ul>
<li><b>Pixfrac</b>: Drop size (0.7 recommended for general use)</li>
<li><b>Scale</b>: Output sampling (0.5 = 2x finer pixels)</li>
<li><b>Iterations</b>: More = better quality but slower</li>
</ul>

<h3>Tips</h3>
<ul>
<li>Use calibration frames for best results</li>
<li>fiDrizzle-MU excels with point sources</li>
<li>Enable positivity constraint to reduce artifacts</li>
<li>Monitor the log for detailed progress</li>
</ul>
        """

        msg = QMessageBox()
        msg.setWindowTitle("Help - VeraLux Drizzle Studio")
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setText(help_text)
        msg.exec()

# =============================================================================
#  MAIN
# =============================================================================

def main():
    """Application entry point"""
    app = QApplication(sys.argv)

    # Set application metadata
    app.setApplicationName("VeraLux Drizzle Studio")
    app.setOrganizationName("VeraLux")
    app.setOrganizationDomain("veralux.space")

    # Create and show main window
    window = VeraLuxDrizzleStudio()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
