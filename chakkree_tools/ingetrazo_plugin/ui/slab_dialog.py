"""
PySide6 Native Parametric Slab Dialog
Allows specifying Slab ID, Slab Type (PS Plank Slab / Cast-in-place RC),
dimensions, thickness, topping thickness, and reinforcement specs.
"""

from typing import Any, Dict, List, Optional, Tuple
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QLayout,
)

from chakkree_tools.rc.slab import Slab


class SlabDialog(QDialog):
    """
    Parametric dialog for creating Slab instances in IngeTrazo.
    """

    def __init__(self, parent: Optional[Any] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Parametric RC / PS Slab")
        self.setMinimumWidth(380)
        self._setup_ui()
        self._update_live_calc()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSizeConstraint(QLayout.SetMinimumSize)

        group_box = QGroupBox("Slab Parameters", self)
        form_layout = QFormLayout(group_box)

        # Slab ID
        self.id_input = QLineEdit("S1", self)
        form_layout.addRow("Slab ID:", self.id_input)

        # Slab Type (PS Plank / RC Cast-in-place)
        self.type_combo = QComboBox(self)
        self.type_combo.addItem("Precast Plank Slab (PS)", "PS")
        self.type_combo.addItem("Cast-in-place RC Slab (RC)", "RC")
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        form_layout.addRow("Slab Type:", self.type_combo)

        # Span X (Width in meters)
        self.span_x_spin = QDoubleSpinBox(self)
        self.span_x_spin.setRange(0.10, 100.0)
        self.span_x_spin.setSingleStep(0.50)
        self.span_x_spin.setValue(4.0)
        self.span_x_spin.setSuffix(" m")
        self.span_x_spin.valueChanged.connect(self._update_live_calc)
        form_layout.addRow("Span X (Width):", self.span_x_spin)

        # Span Y (Length in meters)
        self.span_y_spin = QDoubleSpinBox(self)
        self.span_y_spin.setRange(0.10, 100.0)
        self.span_y_spin.setSingleStep(0.50)
        self.span_y_spin.setValue(4.0)
        self.span_y_spin.setSuffix(" m")
        self.span_y_spin.valueChanged.connect(self._update_live_calc)
        form_layout.addRow("Span Y (Length):", self.span_y_spin)

        # Slab Thickness
        self.thickness_spin = QDoubleSpinBox(self)
        self.thickness_spin.setRange(0.02, 2.0)
        self.thickness_spin.setSingleStep(0.01)
        self.thickness_spin.setValue(0.10)
        self.thickness_spin.setSuffix(" m")
        self.thickness_spin.valueChanged.connect(self._update_live_calc)
        form_layout.addRow("Total Thickness:", self.thickness_spin)

        # Topping Thickness (for PS)
        self.topping_spin = QDoubleSpinBox(self)
        self.topping_spin.setRange(0.01, 1.0)
        self.topping_spin.setSingleStep(0.01)
        self.topping_spin.setValue(0.05)
        self.topping_spin.setSuffix(" m")
        self.topping_spin.valueChanged.connect(self._update_live_calc)
        form_layout.addRow("Topping Thickness:", self.topping_spin)

        # Elevation (Z level)
        self.elevation_spin = QDoubleSpinBox(self)
        self.elevation_spin.setRange(-50.0, 100.0)
        self.elevation_spin.setSingleStep(0.50)
        self.elevation_spin.setValue(0.0)
        self.elevation_spin.setSuffix(" m")
        form_layout.addRow("Top Elevation Z:", self.elevation_spin)

        # Reinforcement Spec
        self.rebar_input = QLineEdit("WM4@0.20", self)
        form_layout.addRow("Reinforcement:", self.rebar_input)

        layout.addWidget(group_box)

        # Live Calculation Summary Group
        calc_box = QGroupBox("Live Calculation Summary", self)
        calc_layout = QVBoxLayout(calc_box)
        self.calc_info_label = QLabel(self)
        self.calc_info_label.setWordWrap(True)
        calc_layout.addWidget(self.calc_info_label)
        layout.addWidget(calc_box)

        # Buttons
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal,
            self,
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def _on_type_changed(self, idx: int) -> None:
        val = self.type_combo.currentData()
        if val == "PS":
            self.topping_spin.setEnabled(True)
            self.rebar_input.setText("WM4@0.20")
            self.thickness_spin.setValue(0.10)
        else:
            self.topping_spin.setEnabled(False)
            self.rebar_input.setText("RB9@0.15")
            self.thickness_spin.setValue(0.12)
        self._update_live_calc()

    def _update_live_calc(self) -> None:
        """Recalculate slab properties and update summary label in real-time."""
        try:
            slab = self.get_slab()
            self.calc_info_label.setText(
                f"Area: {slab.area:.2f} m² | Type: {slab.slab_type.upper()}\n"
                f"Concrete: {slab.concrete_volume:.3f} m³ | Formwork: {slab.formwork_area:.2f} m²"
            )
        except ValueError as exc:
            self.calc_info_label.setText(f"Invalid input: {exc}")

    def get_slab(self) -> Slab:
        sx = self.span_x_spin.value()
        sy = self.span_y_spin.value()
        thickness = self.thickness_spin.value()
        topping = self.topping_spin.value()
        slab_type = self.type_combo.currentData()

        if sx <= 0 or sy <= 0:
            raise ValueError("Slab spans must be greater than zero.")
        if thickness <= 0:
            raise ValueError("Slab thickness must be greater than zero.")
        if slab_type == "PS" and topping <= 0:
            raise ValueError("Topping thickness must be greater than zero.")

        boundary = [(0.0, 0.0), (sx, 0.0), (sx, sy), (0.0, sy)]
        return Slab(
            id=self.id_input.text().strip() or "S1",
            name=f"Slab_{self.id_input.text().strip() or 'S1'}",
            slab_type=slab_type,
            boundary=boundary,
            thickness=thickness,
            elevation=self.elevation_spin.value(),
            topping_thickness=topping,
            wire_mesh=self.rebar_input.text().strip() if slab_type == "PS" else "WM4@0.20",
            rebar_spec=self.rebar_input.text().strip() if slab_type == "RC" else "RB9@0.15",
        )
