"""
PySide6 Native Parametric Footing Dialog
Allows specifying 1-9 Piles, pile diameter, rebar sizes, covering, and dimensions.
"""

from typing import Optional, Dict, Any
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QDoubleSpinBox,
    QDialogButtonBox,
    QLabel,
    QGroupBox,
)
from PySide6.QtCore import Qt

from chakkree_tools.rc.footing import Footing, PileCap


class FootingDialog(QDialog):
    """
    Parametric dialog for creating Footing / Pile Cap instances in IngeTrazo.
    """

    def __init__(self, parent: Optional[Any] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Parametric Footing / Pile Cap")
        self.resize(360, 420)

        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        group_box = QGroupBox("Footing Parameters", self)
        form_layout = QFormLayout(group_box)

        # Footing ID
        self.id_input = QLineEdit("F1", self)
        form_layout.addRow("Footing ID:", self.id_input)

        # Pile Count (1 to 9 Piles)
        self.pile_count_combo = QComboBox(self)
        for i in range(1, 10):
            self.pile_count_combo.addItem(f"{i} Pile{'s' if i > 1 else ''}", i)
        form_layout.addRow("Pile Count:", self.pile_count_combo)

        # Pile Diameter (180, 220, 250, 300, 350 mm)
        self.pile_dia_combo = QComboBox(self)
        pile_dias = [
            ("180 mm", 0.180),
            ("220 mm", 0.220),
            ("250 mm", 0.250),
            ("300 mm", 0.300),
            ("350 mm", 0.350),
        ]
        for label, val in pile_dias:
            self.pile_dia_combo.addItem(label, val)
        self.pile_dia_combo.setCurrentIndex(1)  # Default 220 mm
        form_layout.addRow("Pile Diameter:", self.pile_dia_combo)

        # Rebar Size (DB12, DB16, DB20, DB25)
        self.rebar_size_combo = QComboBox(self)
        rebar_sizes = [
            ("DB12", 0.012),
            ("DB16", 0.016),
            ("DB20", 0.020),
            ("DB25", 0.025),
        ]
        for label, val in rebar_sizes:
            self.rebar_size_combo.addItem(label, val)
        self.rebar_size_combo.setCurrentIndex(1)  # Default DB16
        form_layout.addRow("Rebar Size:", self.rebar_size_combo)

        # Thickness (m)
        self.thickness_spin = QDoubleSpinBox(self)
        self.thickness_spin.setRange(0.20, 3.00)
        self.thickness_spin.setSingleStep(0.05)
        self.thickness_spin.setValue(0.60)
        self.thickness_spin.setSuffix(" m")
        form_layout.addRow("Thickness (t):", self.thickness_spin)

        # Elevation Z (m)
        self.elevation_spin = QDoubleSpinBox(self)
        self.elevation_spin.setRange(-20.0, 10.0)
        self.elevation_spin.setSingleStep(0.10)
        self.elevation_spin.setValue(-0.70)
        self.elevation_spin.setSuffix(" m")
        form_layout.addRow("Elevation Z:", self.elevation_spin)

        # Covering (m)
        self.covering_spin = QDoubleSpinBox(self)
        self.covering_spin.setRange(0.02, 0.20)
        self.covering_spin.setSingleStep(0.005)
        self.covering_spin.setDecimals(3)
        self.covering_spin.setValue(0.070)
        self.covering_spin.setSuffix(" m")
        form_layout.addRow("Covering:", self.covering_spin)

        layout.addWidget(group_box)

        # Dialog Buttons
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def get_footing(self) -> Footing:
        """
        Creates and returns a Footing model based on user input.
        """
        footing_id = self.id_input.text().strip() or "F1"
        pile_count = self.pile_count_combo.currentData()
        pile_size = self.pile_dia_combo.currentData()
        rebar_dia = self.rebar_size_combo.currentData()
        thickness = self.thickness_spin.value()
        elevation = self.elevation_spin.value()
        covering = self.covering_spin.value()

        return PileCap.create_n_piles(
            id_str=footing_id,
            pile_count=pile_count,
            pile_size=pile_size,
            thickness=thickness,
            elevation=elevation,
            covering=covering,
            rebar_dia=rebar_dia,
        )
