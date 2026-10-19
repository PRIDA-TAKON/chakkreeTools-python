"""
PySide6 Native Parametric Beam Dialog
Allows specifying span length, b x h, top/bottom bars, and multi-zone stirrup spacing.
"""

from typing import Optional, Any
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QDoubleSpinBox,
    QDialogButtonBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
)

from chakkree_tools.rc.beam import Beam


class BeamDialog(QDialog):
    """
    Parametric dialog for creating Beam instances in IngeTrazo.
    """

    def __init__(self, parent: Optional[Any] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Parametric RC Beam")
        self.resize(380, 520)

        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        group_box = QGroupBox("Beam Parameters", self)
        form_layout = QFormLayout(group_box)

        # Beam ID
        self.id_input = QLineEdit("B1", self)
        form_layout.addRow("Beam ID:", self.id_input)

        # Span Length (L)
        self.length_spin = QDoubleSpinBox(self)
        self.length_spin.setRange(0.50, 30.00)
        self.length_spin.setSingleStep(0.25)
        self.length_spin.setValue(4.00)
        self.length_spin.setSuffix(" m")
        form_layout.addRow("Span Length (L):", self.length_spin)

        # Width (b)
        self.width_spin = QDoubleSpinBox(self)
        self.width_spin.setRange(0.10, 2.00)
        self.width_spin.setSingleStep(0.05)
        self.width_spin.setValue(0.20)
        self.width_spin.setSuffix(" m")
        form_layout.addRow("Width (b):", self.width_spin)

        # Depth (h)
        self.depth_spin = QDoubleSpinBox(self)
        self.depth_spin.setRange(0.15, 3.00)
        self.depth_spin.setSingleStep(0.05)
        self.depth_spin.setValue(0.40)
        self.depth_spin.setSuffix(" m")
        form_layout.addRow("Depth (h):", self.depth_spin)

        # Elevation Z (m)
        self.elevation_spin = QDoubleSpinBox(self)
        self.elevation_spin.setRange(-10.0, 50.0)
        self.elevation_spin.setSingleStep(0.10)
        self.elevation_spin.setValue(3.20)
        self.elevation_spin.setSuffix(" m")
        form_layout.addRow("Elevation Z:", self.elevation_spin)

        # Top Bar Spec
        self.top_bar_input = QLineEdit("2DB12", self)
        form_layout.addRow("Top Main Bars:", self.top_bar_input)

        # Bottom Bar Spec
        self.bot_bar_input = QLineEdit("3DB12", self)
        form_layout.addRow("Bottom Main Bars:", self.bot_bar_input)

        # Extra Bottom Bar Spec
        self.extra_bar_input = QLineEdit("1DB12", self)
        form_layout.addRow("Extra Bottom Bars:", self.extra_bar_input)

        # Multi-Zone Stirrups Group
        stirrup_box = QGroupBox("Multi-Zone Stirrup Spacing", self)
        stirrup_layout = QFormLayout(stirrup_box)

        self.stirrup_bar_combo = QComboBox(self)
        self.stirrup_bar_combo.addItems(["RB6", "RB9", "DB10"])
        stirrup_layout.addRow("Stirrup Bar:", self.stirrup_bar_combo)

        self.stirrup_zone_end_spin = QDoubleSpinBox(self)
        self.stirrup_zone_end_spin.setRange(0.05, 0.40)
        self.stirrup_zone_end_spin.setSingleStep(0.025)
        self.stirrup_zone_end_spin.setDecimals(3)
        self.stirrup_zone_end_spin.setValue(0.100)
        self.stirrup_zone_end_spin.setSuffix(" m")
        stirrup_layout.addRow("End Zones Spacing (L/4):", self.stirrup_zone_end_spin)

        self.stirrup_zone_mid_spin = QDoubleSpinBox(self)
        self.stirrup_zone_mid_spin.setRange(0.05, 0.40)
        self.stirrup_zone_mid_spin.setSingleStep(0.025)
        self.stirrup_zone_mid_spin.setDecimals(3)
        self.stirrup_zone_mid_spin.setValue(0.200)
        self.stirrup_zone_mid_spin.setSuffix(" m")
        stirrup_layout.addRow("Mid Zone Spacing (L/2):", self.stirrup_zone_mid_spin)

        form_layout.addRow(stirrup_box)

        # Covering (m)
        self.covering_spin = QDoubleSpinBox(self)
        self.covering_spin.setRange(0.01, 0.10)
        self.covering_spin.setSingleStep(0.005)
        self.covering_spin.setDecimals(3)
        self.covering_spin.setValue(0.025)
        self.covering_spin.setSuffix(" m")
        form_layout.addRow("Covering:", self.covering_spin)

        layout.addWidget(group_box)

        # Buttons
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def get_beam(self) -> Beam:
        """
        Creates and returns a Beam model based on user input.
        """
        beam_id = self.id_input.text().strip() or "B1"
        length = self.length_spin.value()
        width = self.width_spin.value()
        depth = self.depth_spin.value()
        elevation = self.elevation_spin.value()
        top_spec = self.top_bar_input.text().strip() or "2DB12"
        bot_spec = self.bot_bar_input.text().strip() or "3DB12"
        extra_spec = self.extra_bar_input.text().strip() or None

        bar_type = self.stirrup_bar_combo.currentText()
        s_end = self.stirrup_zone_end_spin.value()
        s_mid = self.stirrup_zone_mid_spin.value()

        if abs(s_end - s_mid) < 1e-4:
            stirrup_spec = f"{bar_type}@{s_end:.3f}"
        else:
            stirrup_spec = f"{bar_type}@{s_end:.3f}/{s_mid:.3f}/{s_end:.3f}"

        covering = self.covering_spin.value()

        return Beam(
            id=beam_id,
            name=f"Beam_{beam_id}",
            width=width,
            depth=depth,
            start_point=(0.0, 0.0),
            end_point=(length, 0.0),
            elevation=elevation,
            top_bar_spec=top_spec,
            bot_bar_spec=bot_spec,
            extra_bar_spec=extra_spec,
            stirrup_spec=stirrup_spec,
            covering=covering,
        )
