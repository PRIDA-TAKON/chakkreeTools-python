"""
PySide6 Native Parametric Column Dialog
Allows specifying column section b x h, height, 4-16 longitudinal bars, stirrups, and covering.
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
    QLabel,
    QLayout,
)

from chakkree_tools.rc.column import Column


class ColumnDialog(QDialog):
    """
    Parametric dialog for creating Column instances in IngeTrazo.
    """

    def __init__(self, parent: Optional[Any] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Parametric RC Column")
        self.setMinimumWidth(380)

        self._setup_ui()
        self._update_live_calc()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSizeConstraint(QLayout.SetMinimumSize)

        group_box = QGroupBox("Column Parameters", self)
        form_layout = QFormLayout(group_box)

        # Column ID
        self.id_input = QLineEdit("C1", self)
        form_layout.addRow("Column ID:", self.id_input)

        # Profile
        self.profile_combo = QComboBox(self)
        self.profile_combo.addItem("Rectangular", "RECTANGULAR")
        self.profile_combo.addItem("Circular", "CIRCULAR")
        self.profile_combo.currentIndexChanged.connect(self._update_live_calc)
        form_layout.addRow("Profile:", self.profile_combo)

        # Width (b)
        self.width_spin = QDoubleSpinBox(self)
        self.width_spin.setRange(0.05, 5.00)
        self.width_spin.setSingleStep(0.05)
        self.width_spin.setValue(0.30)
        self.width_spin.setSuffix(" m")
        self.width_spin.valueChanged.connect(self._update_live_calc)
        form_layout.addRow("Width (b):", self.width_spin)

        # Depth / Diameter (h)
        self.depth_spin = QDoubleSpinBox(self)
        self.depth_spin.setRange(0.05, 5.00)
        self.depth_spin.setSingleStep(0.05)
        self.depth_spin.setValue(0.30)
        self.depth_spin.setSuffix(" m")
        self.depth_spin.valueChanged.connect(self._update_live_calc)
        form_layout.addRow("Depth (t):", self.depth_spin)

        # Height (H)
        self.height_spin = QDoubleSpinBox(self)
        self.height_spin.setRange(0.10, 50.00)
        self.height_spin.setSingleStep(0.10)
        self.height_spin.setValue(3.50)
        self.height_spin.setSuffix(" m")
        self.height_spin.valueChanged.connect(self._update_live_calc)
        form_layout.addRow("Height (H):", self.height_spin)

        # Longitudinal Bar Count (4 to 16 bars)
        self.main_bar_count_combo = QComboBox(self)
        for count in [4, 6, 8, 10, 12, 14, 16]:
            self.main_bar_count_combo.addItem(f"{count} Bars", count)
        self.main_bar_count_combo.setCurrentIndex(2)  # Default 8 Bars
        self.main_bar_count_combo.currentIndexChanged.connect(self._update_live_calc)
        form_layout.addRow("Main Bars:", self.main_bar_count_combo)

        # Main Bar Diameter
        self.main_bar_dia_combo = QComboBox(self)
        main_dias = [
            ("DB12", 0.012),
            ("DB16", 0.016),
            ("DB20", 0.020),
            ("DB25", 0.025),
            ("DB28", 0.028),
            ("DB32", 0.032),
        ]
        for label, val in main_dias:
            self.main_bar_dia_combo.addItem(label, val)
        self.main_bar_dia_combo.setCurrentIndex(1)  # Default DB16
        form_layout.addRow("Main Bar Dia:", self.main_bar_dia_combo)

        # Stirrup Diameter
        self.stirrup_dia_combo = QComboBox(self)
        stirrup_dias = [
            ("RB6", 0.006),
            ("RB9", 0.009),
            ("DB10", 0.010),
        ]
        for label, val in stirrup_dias:
            self.stirrup_dia_combo.addItem(label, val)
        self.stirrup_dia_combo.setCurrentIndex(1)  # Default RB9
        form_layout.addRow("Stirrup Dia:", self.stirrup_dia_combo)

        # Stirrup Spacing (m)
        self.stirrup_spacing_spin = QDoubleSpinBox(self)
        self.stirrup_spacing_spin.setRange(0.01, 1.00)
        self.stirrup_spacing_spin.setSingleStep(0.025)
        self.stirrup_spacing_spin.setDecimals(3)
        self.stirrup_spacing_spin.setValue(0.150)
        self.stirrup_spacing_spin.setSuffix(" m")
        self.stirrup_spacing_spin.valueChanged.connect(self._update_live_calc)
        form_layout.addRow("Stirrup Spacing:", self.stirrup_spacing_spin)

        # Covering (m)
        self.covering_spin = QDoubleSpinBox(self)
        self.covering_spin.setRange(0.005, 0.20)
        self.covering_spin.setSingleStep(0.005)
        self.covering_spin.setDecimals(3)
        self.covering_spin.setValue(0.030)
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
        """Recalculate column properties and update summary label in real-time."""
        try:
            col = self.get_column()
            stirrup_count = int(col.height / col.stirrup_spacing) + 1 if col.stirrup_spacing > 0 else 0
            self.calc_info_label.setText(
                f"Section: {col.profile.capitalize()} {col.width:.2f} m × {col.depth:.2f} m | Height: {col.height:.2f} m\n"
                f"Concrete: {col.concrete_volume:.3f} m³ | Formwork: {col.formwork_area:.2f} m² | Stirrups: ~{stirrup_count} pcs"
            )
        except ValueError as exc:
            self.calc_info_label.setText(f"Invalid input: {exc}")

    def get_column(self) -> Column:
        """
        Creates and returns a Column model based on user input.
        """
        col_id = self.id_input.text().strip() or "C1"
        profile = self.profile_combo.currentData()
        width = self.width_spin.value()
        depth = self.depth_spin.value()
        height = self.height_spin.value()
        bar_count = self.main_bar_count_combo.currentData()
        bar_dia = self.main_bar_dia_combo.currentData()
        stirrup_dia = self.stirrup_dia_combo.currentData()
        stirrup_spacing = self.stirrup_spacing_spin.value()
        covering = self.covering_spin.value()

        if width <= 0 or depth <= 0:
            raise ValueError("Column width and depth must be greater than zero.")
        if height <= 0:
            raise ValueError("Column height must be greater than zero.")
        if stirrup_spacing <= 0:
            raise ValueError("Stirrup spacing must be greater than zero.")
        if covering <= 0:
            raise ValueError("Covering must be greater than zero.")

        return Column(
            id=col_id,
            name=f"Column_{col_id}",
            profile=profile,
            width=width,
            depth=depth,
            height=height,
            main_bar_count=bar_count,
            main_bar_dia=bar_dia,
            stirrup_dia=stirrup_dia,
            stirrup_spacing=stirrup_spacing,
            covering=covering,
        )
