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
    QLayout,
)

from chakkree_tools.rc.beam import Beam


class BeamDialog(QDialog):
    """
    Parametric dialog for creating Beam instances in IngeTrazo.
    """

    def __init__(self, parent: Optional[Any] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Parametric RC Beam")
        self.setMinimumWidth(400)

        self._setup_ui()
        self._update_live_calc()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSizeConstraint(QLayout.SetMinimumSize)

        group_box = QGroupBox("Beam Parameters", self)
        form_layout = QFormLayout(group_box)

        # Beam ID
        self.id_input = QLineEdit("B1", self)
        form_layout.addRow("Beam ID:", self.id_input)

        # Span Length (L)
        self.length_spin = QDoubleSpinBox(self)
        self.length_spin.setRange(0.10, 100.00)
        self.length_spin.setSingleStep(0.25)
        self.length_spin.setValue(4.00)
        self.length_spin.setSuffix(" m")
        self.length_spin.valueChanged.connect(self._update_live_calc)
        form_layout.addRow("Span Length (L):", self.length_spin)

        # Width (b)
        self.width_spin = QDoubleSpinBox(self)
        self.width_spin.setRange(0.05, 5.00)
        self.width_spin.setSingleStep(0.05)
        self.width_spin.setValue(0.20)
        self.width_spin.setSuffix(" m")
        self.width_spin.valueChanged.connect(self._update_live_calc)
        form_layout.addRow("Width (b):", self.width_spin)

        # Depth (h)
        self.depth_spin = QDoubleSpinBox(self)
        self.depth_spin.setRange(0.05, 5.00)
        self.depth_spin.setSingleStep(0.05)
        self.depth_spin.setValue(0.40)
        self.depth_spin.setSuffix(" m")
        self.depth_spin.valueChanged.connect(self._update_live_calc)
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
        self.stirrup_zone_end_spin.setRange(0.01, 1.00)
        self.stirrup_zone_end_spin.setSingleStep(0.025)
        self.stirrup_zone_end_spin.setDecimals(3)
        self.stirrup_zone_end_spin.setValue(0.100)
        self.stirrup_zone_end_spin.setSuffix(" m")
        self.stirrup_zone_end_spin.valueChanged.connect(self._update_live_calc)
        stirrup_layout.addRow("End Zones Spacing (L/4):", self.stirrup_zone_end_spin)

        self.stirrup_zone_mid_spin = QDoubleSpinBox(self)
        self.stirrup_zone_mid_spin.setRange(0.01, 1.00)
        self.stirrup_zone_mid_spin.setSingleStep(0.025)
        self.stirrup_zone_mid_spin.setDecimals(3)
        self.stirrup_zone_mid_spin.setValue(0.200)
        self.stirrup_zone_mid_spin.setSuffix(" m")
        self.stirrup_zone_mid_spin.valueChanged.connect(self._update_live_calc)
        stirrup_layout.addRow("Mid Zone Spacing (L/2):", self.stirrup_zone_mid_spin)

        form_layout.addRow(stirrup_box)

        # Covering (m)
        self.covering_spin = QDoubleSpinBox(self)
        self.covering_spin.setRange(0.005, 0.20)
        self.covering_spin.setSingleStep(0.005)
        self.covering_spin.setDecimals(3)
        self.covering_spin.setValue(0.025)
        self.covering_spin.setSuffix(" m")
        self.covering_spin.valueChanged.connect(self._update_live_calc)
        form_layout.addRow("Covering:", self.covering_spin)

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
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def _update_live_calc(self) -> None:
        """Recalculate beam properties and update summary label in real-time."""
        try:
            beam = self.get_beam()
            end_zone_len = beam.length / 4.0
            mid_zone_len = beam.length / 2.0
            self.calc_info_label.setText(
                f"Span: {beam.length:.2f} m (L/4 end: {end_zone_len:.2f} m, L/2 mid: {mid_zone_len:.2f} m)\n"
                f"Concrete: {beam.concrete_volume:.3f} m³ | Formwork: {beam.formwork_area:.2f} m²"
            )
        except ValueError as exc:
            self.calc_info_label.setText(f"Invalid input: {exc}")

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

        if length <= 0:
            raise ValueError("Beam span length must be greater than zero.")
        if width <= 0 or depth <= 0:
            raise ValueError("Beam width and depth must be greater than zero.")
        if s_end <= 0 or s_mid <= 0:
            raise ValueError("Stirrup spacing must be greater than zero.")

        covering = self.covering_spin.value()
        if covering <= 0:
            raise ValueError("Covering must be greater than zero.")

        if abs(s_end - s_mid) < 1e-4:
            stirrup_spec = f"{bar_type}@{s_end:.3f}"
        else:
            stirrup_spec = f"{bar_type}@{s_end:.3f}/{s_mid:.3f}/{s_end:.3f}"

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
