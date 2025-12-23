#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fiDrizzle-MU GUI - Jednostavan grafički interfejs za fiDrizzle-MU
=================================================================

Omogućava lako korišćenje fiDrizzle-MU algoritma bez komandne linije.
"""

import sys
import os
from pathlib import Path

try:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
        QWidget, QLabel, QPushButton, QGroupBox, QFileDialog,
        QTextEdit, QProgressBar, QSpinBox, QDoubleSpinBox,
        QCheckBox, QMessageBox
    )
    from PyQt6.QtCore import Qt, QThread, pyqtSignal
    from PyQt6.QtGui import QFont
except ImportError:
    print("GREŠKA: PyQt6 nije instaliran!")
    print("\nInstaliraj sa:")
    print("  pip install PyQt6")
    sys.exit(1)

try:
    from siril_fidrizzle_mu import FiDrizzleMU
except ImportError:
    print("GREŠKA: siril_fidrizzle_mu modul nije pronađen!")
    print("\nProveri da li se siril_fidrizzle_mu.py nalazi u istom folderu.")
    sys.exit(1)


# Dark tema
DARK_THEME = """
QWidget {
    background-color: #2b2b2b;
    color: #e0e0e0;
    font-size: 10pt;
}

QGroupBox {
    border: 2px solid #4a4a4a;
    border-radius: 5px;
    margin-top: 10px;
    font-weight: bold;
    padding-top: 10px;
    color: #88aaff;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
}

QPushButton {
    background-color: #3c3c3c;
    color: #ffffff;
    border: 1px solid #555555;
    border-radius: 4px;
    padding: 8px 16px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #4a4a4a;
    border-color: #777777;
}

QPushButton:disabled {
    background-color: #2b2b2b;
    color: #666666;
}

QPushButton#StartButton {
    background-color: #285299;
    font-size: 12pt;
    min-height: 40px;
}

QPushButton#StartButton:hover {
    background-color: #355ea1;
}

QLabel {
    color: #cccccc;
}

QSpinBox, QDoubleSpinBox {
    background-color: #3c3c3c;
    color: #ffffff;
    border: 1px solid #555555;
    border-radius: 3px;
    padding: 5px;
}

QCheckBox {
    color: #cccccc;
}

QTextEdit {
    background-color: #1a1a1a;
    color: #d0d0d0;
    border: 1px solid #444444;
    border-radius: 4px;
    font-family: 'Consolas', monospace;
    font-size: 9pt;
}

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


class ProcessWorker(QThread):
    """Thread za procesiranje u pozadini"""

    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, image_files, output_file, psr, iterations, gamma, positivity):
        super().__init__()
        self.image_files = image_files
        self.output_file = output_file
        self.psr = psr
        self.iterations = iterations
        self.gamma = gamma
        self.positivity = positivity

    def run(self):
        """Pokreni procesiranje"""
        try:
            self.log_signal.emit("="*60)
            self.log_signal.emit("fiDrizzle-MU - Početak procesiranja")
            self.log_signal.emit("="*60)
            self.log_signal.emit(f"\nBroj slika: {len(self.image_files)}")
            self.log_signal.emit(f"PSR: {self.psr}")
            self.log_signal.emit(f"Iteracije: {self.iterations}")
            self.log_signal.emit(f"Gamma: {self.gamma}")
            self.log_signal.emit(f"Positivity: {'Da' if self.positivity else 'Ne'}\n")

            self.progress_signal.emit(5)

            # Kreiraj processor
            processor = FiDrizzleMU(
                psr=self.psr,
                gamma=self.gamma,
                max_iterations=self.iterations,
                positivity_constraint=self.positivity,
                verbose=True
            )

            self.progress_signal.emit(10)
            self.log_signal.emit("Učitavanje slika...")

            # Učitaj slike
            processor.load_images(self.image_files)

            self.progress_signal.emit(20)
            self.log_signal.emit("Procesiranje...")

            # Procesiraj
            result = processor.process()

            self.progress_signal.emit(90)
            self.log_signal.emit("\nČuvanje rezultata...")

            # Sačuvaj
            processor.save_result(result, self.output_file)

            self.progress_signal.emit(100)
            self.log_signal.emit("\n" + "="*60)
            self.log_signal.emit("✓ USPEŠNO ZAVRŠENO!")
            self.log_signal.emit("="*60)

            self.finished_signal.emit(True, f"Rezultat sačuvan u:\n{self.output_file}")

        except Exception as e:
            error_msg = str(e)
            self.log_signal.emit(f"\n✗ GREŠKA: {error_msg}")
            self.finished_signal.emit(False, error_msg)


class FiDrizzleMU_GUI(QMainWindow):
    """Glavni prozor aplikacije"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("fiDrizzle-MU - Profesionalni Drizzle Stack")
        self.setStyleSheet(DARK_THEME)
        self.resize(900, 700)

        self.image_files = []
        self.worker = None

        self.init_ui()

    def init_ui(self):
        """Kreiraj interfejs"""
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        # Header
        header = QLabel("fiDrizzle-MU Stack")
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        header.setFont(font)
        header.setStyleSheet("color: #88aaff;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)

        subtitle = QLabel("Fast Iterative Drizzle with Multiplicative Updates")
        subtitle.setStyleSheet("color: #888888; font-style: italic;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        # Input slike
        input_group = QGroupBox("1. Slike za stackiranje")
        input_layout = QVBoxLayout(input_group)

        self.label_files = QLabel("Nije izabrano nijedna slika")
        self.label_files.setStyleSheet("color: #ff8888;")
        input_layout.addWidget(self.label_files)

        btn_layout = QHBoxLayout()

        btn_add = QPushButton("📁 Izaberi slike...")
        btn_add.clicked.connect(self.select_images)
        btn_layout.addWidget(btn_add)

        btn_clear = QPushButton("🗑️ Obriši")
        btn_clear.clicked.connect(self.clear_images)
        btn_layout.addWidget(btn_clear)

        input_layout.addLayout(btn_layout)

        self.info_label = QLabel("💡 Tip: Izaberi registrovane slike iz Siril-a (r_pp_light_*.fit)")
        self.info_label.setStyleSheet("color: #888888; font-size: 9pt; font-style: italic;")
        self.info_label.setWordWrap(True)
        input_layout.addWidget(self.info_label)

        layout.addWidget(input_group)

        # Output
        output_group = QGroupBox("2. Izlazni fajl")
        output_layout = QVBoxLayout(output_group)

        out_layout = QHBoxLayout()
        self.label_output = QLabel("fidrizzle_result.fits")
        out_layout.addWidget(self.label_output)

        btn_output = QPushButton("Promeni...")
        btn_output.clicked.connect(self.select_output)
        out_layout.addWidget(btn_output)

        output_layout.addLayout(out_layout)
        layout.addWidget(output_group)

        # Parametri
        params_group = QGroupBox("3. Parametri")
        params_layout = QVBoxLayout(params_group)

        # PSR
        psr_layout = QHBoxLayout()
        psr_layout.addWidget(QLabel("PSR (Pixel Scale Ratio):"))
        self.spin_psr = QDoubleSpinBox()
        self.spin_psr.setRange(0.1, 1.0)
        self.spin_psr.setSingleStep(0.05)
        self.spin_psr.setValue(0.5)
        self.spin_psr.setToolTip("0.5 = 2x veća rezolucija (preporučeno)")
        psr_layout.addWidget(self.spin_psr)
        psr_layout.addStretch()
        params_layout.addLayout(psr_layout)

        # Iterations
        iter_layout = QHBoxLayout()
        iter_layout.addWidget(QLabel("Iteracije:"))
        self.spin_iterations = QSpinBox()
        self.spin_iterations.setRange(1, 1000)
        self.spin_iterations.setValue(65)
        self.spin_iterations.setToolTip("Broj iteracija (65 preporučeno za point sources)")
        iter_layout.addWidget(self.spin_iterations)
        iter_layout.addStretch()
        params_layout.addLayout(iter_layout)

        # Gamma
        gamma_layout = QHBoxLayout()
        gamma_layout.addWidget(QLabel("Gamma (step-size):"))
        self.spin_gamma = QDoubleSpinBox()
        self.spin_gamma.setRange(0.1, 10.0)
        self.spin_gamma.setSingleStep(0.1)
        self.spin_gamma.setValue(1.0)
        self.spin_gamma.setToolTip("Brzina konvergencije (1.0 preporučeno)")
        gamma_layout.addWidget(self.spin_gamma)
        gamma_layout.addStretch()
        params_layout.addLayout(gamma_layout)

        # Positivity
        self.check_positivity = QCheckBox("Positivity Constraint (sprečava negativne piksele)")
        self.check_positivity.setChecked(True)
        self.check_positivity.setToolTip("Preporučeno - smanjuje ringing artefakte")
        params_layout.addWidget(self.check_positivity)

        layout.addWidget(params_group)

        # Presets
        preset_group = QGroupBox("Presets")
        preset_layout = QHBoxLayout(preset_group)

        btn_preset1 = QPushButton("⭐ Point Sources")
        btn_preset1.setToolTip("Optimalno za zvezde, kvazare")
        btn_preset1.clicked.connect(lambda: self.load_preset(0.5, 65, 1.0))
        preset_layout.addWidget(btn_preset1)

        btn_preset2 = QPushButton("🌌 Extended Sources")
        btn_preset2.setToolTip("Optimalno za galaksije, maglice")
        btn_preset2.clicked.connect(lambda: self.load_preset(0.5, 100, 1.0))
        preset_layout.addWidget(btn_preset2)

        btn_preset3 = QPushButton("🔬 High Resolution")
        btn_preset3.setToolTip("4x veća rezolucija")
        btn_preset3.clicked.connect(lambda: self.load_preset(0.25, 150, 1.0))
        preset_layout.addWidget(btn_preset3)

        layout.addWidget(preset_group)

        # Progress
        self.progress = QProgressBar()
        self.progress.setValue(0)
        layout.addWidget(self.progress)

        # Log
        log_label = QLabel("Log:")
        log_label.setStyleSheet("color: #88aaff; font-weight: bold;")
        layout.addWidget(log_label)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        layout.addWidget(self.log_text)

        self.log("Spremno. Izaberi slike i klikni 'POKRENI STACK'.")

        # Action buttons
        action_layout = QHBoxLayout()

        btn_help = QPushButton("❓ Pomoć")
        btn_help.clicked.connect(self.show_help)
        action_layout.addWidget(btn_help)

        action_layout.addStretch()

        btn_close = QPushButton("Zatvori")
        btn_close.clicked.connect(self.close)
        action_layout.addWidget(btn_close)

        self.btn_start = QPushButton("⚡ POKRENI STACK")
        self.btn_start.setObjectName("StartButton")
        self.btn_start.clicked.connect(self.start_processing)
        self.btn_start.setEnabled(False)
        action_layout.addWidget(self.btn_start)

        layout.addLayout(action_layout)

    def select_images(self):
        """Izaberi slike"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Izaberi FITS slike",
            str(Path.home()),
            "FITS Files (*.fit *.fits *.fts);;All Files (*.*)"
        )

        if files:
            self.image_files = files
            count = len(files)
            self.label_files.setText(f"✓ Izabrano {count} slika")
            self.label_files.setStyleSheet("color: #88ff88;")
            self.btn_start.setEnabled(True)
            self.log(f"Izabrano {count} slika")

    def clear_images(self):
        """Obriši slike"""
        self.image_files = []
        self.label_files.setText("Nije izabrano nijedna slika")
        self.label_files.setStyleSheet("color: #ff8888;")
        self.btn_start.setEnabled(False)
        self.log("Slike obrisane")

    def select_output(self):
        """Izaberi output fajl"""
        file, _ = QFileDialog.getSaveFileName(
            self,
            "Sačuvaj rezultat kao",
            "fidrizzle_result.fits",
            "FITS Files (*.fits *.fit);;All Files (*.*)"
        )

        if file:
            self.label_output.setText(os.path.basename(file))
            self.label_output.setProperty("fullpath", file)
            self.log(f"Output: {file}")

    def load_preset(self, psr, iterations, gamma):
        """Učitaj preset"""
        self.spin_psr.setValue(psr)
        self.spin_iterations.setValue(iterations)
        self.spin_gamma.setValue(gamma)
        self.log(f"✓ Preset učitan: PSR={psr}, Iter={iterations}, Gamma={gamma}")

    def log(self, message):
        """Dodaj poruku u log"""
        self.log_text.append(message)

    def start_processing(self):
        """Pokreni procesiranje"""
        if not self.image_files:
            QMessageBox.warning(self, "Greška", "Nisu izabrane slike!")
            return

        # Output fajl
        if hasattr(self.label_output, 'property') and self.label_output.property("fullpath"):
            output_file = self.label_output.property("fullpath")
        else:
            output_file = os.path.join(os.getcwd(), "fidrizzle_result.fits")

        # Potvrda
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setWindowTitle("Potvrda")
        msg.setText(f"Procesirati {len(self.image_files)} slika?")
        msg.setInformativeText(
            f"PSR: {self.spin_psr.value()}\n"
            f"Iteracije: {self.spin_iterations.value()}\n"
            f"Gamma: {self.spin_gamma.value()}\n"
            f"Positivity: {'Da' if self.check_positivity.isChecked() else 'Ne'}"
        )
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if msg.exec() != QMessageBox.StandardButton.Yes:
            return

        # Pokreni worker
        self.log_text.clear()
        self.progress.setValue(0)
        self.btn_start.setEnabled(False)

        self.worker = ProcessWorker(
            self.image_files,
            output_file,
            self.spin_psr.value(),
            self.spin_iterations.value(),
            self.spin_gamma.value(),
            self.check_positivity.isChecked()
        )

        self.worker.log_signal.connect(self.log)
        self.worker.progress_signal.connect(self.progress.setValue)
        self.worker.finished_signal.connect(self.processing_finished)
        self.worker.start()

    def processing_finished(self, success, message):
        """Završeno procesiranje"""
        self.btn_start.setEnabled(True)

        if success:
            QMessageBox.information(self, "Uspešno!", message)
        else:
            QMessageBox.critical(self, "Greška!", f"Procesiranje neuspešno:\n{message}")

    def show_help(self):
        """Prikaži pomoć"""
        help_text = """
<h2>fiDrizzle-MU - Brzi vodič</h2>

<h3>Koraci:</h3>
<ol>
<li><b>Registruj slike u Sirilu</b>:<br>
   U Sirilu: <code>register pp_light</code></li>

<li><b>Izaberi registrovane slike</b>:<br>
   Klikni "Izaberi slike" i odaberi <code>r_pp_light_*.fit</code></li>

<li><b>Podesi parametre</b> (ili koristi preset)</li>

<li><b>Klikni "POKRENI STACK"</b></li>

<li><b>Učitaj rezultat u Siril</b>:<br>
   <code>File → Open → fidrizzle_result.fits</code></li>
</ol>

<h3>Parametri:</h3>
<ul>
<li><b>PSR 0.5</b> = 2x veća rezolucija (preporučeno)</li>
<li><b>Iteracije 65</b> = optimalno za point sources</li>
<li><b>Gamma 1.0</b> = standardna brzina</li>
<li><b>Positivity</b> = sprečava artefakte (preporučeno)</li>
</ul>

<h3>Presets:</h3>
<ul>
<li><b>Point Sources</b> - za zvezde, kvazare</li>
<li><b>Extended Sources</b> - za galaksije, maglice</li>
<li><b>High Resolution</b> - za maksimalnu rezoluciju</li>
</ul>

<h3>Za više informacija:</h3>
Pogledaj <code>FIDRIZZLE_MU_GUIDE.md</code>
        """

        msg = QMessageBox()
        msg.setWindowTitle("Pomoć")
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setText(help_text)
        msg.exec()


def main():
    """Glavni program"""
    app = QApplication(sys.argv)

    window = FiDrizzleMU_GUI()
    window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
