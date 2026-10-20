"""
PySide6 Native Grid Line Generator Dialog
Creates structural X/Y grids and datum level markers.
"""

from typing import Any, Dict, List, Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QLineEdit,
    QSpinBox,
    QVBoxLayout,
)


class GridLineDialog(QDialog):
    """
    Dialog for configuring parametric structural grid axes.
    """

    def __init__(self, parent: Optional[Any] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Structural Grid Lines (GridLine v2026)")
        self.resize(360, 320)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        group = QGroupBox("Grid System Configuration", self)
        form = QFormLayout(group)

        # X Grids (e.g. 1, 2, 3, 4)
        self.x_count_spin = QSpinBox(self)
        self.x_count_spin.setRange(1, 50)
        self.x_count_spin.setValue(4)
        form.addRow("X Grid Count:", self.x_count_spin)

        self.x_spacing_spin = QDoubleSpinBox(self)
        self.x_spacing_spin.setRange(1.0, 50.0)
        self.x_spacing_spin.setValue(4.0)
        self.x_spacing_spin.setSuffix(" m")
        form.addRow("X Spacing:", self.x_spacing_spin)

        # Y Grids (e.g. A, B, C)
        self.y_count_spin = QSpinBox(self)
        self.y_count_spin.setRange(1, 50)
        self.y_count_spin.setValue(3)
        form.addRow("Y Grid Count:", self.y_count_spin)

        self.y_spacing_spin = QDoubleSpinBox(self)
        self.y_spacing_spin.setRange(1.0, 50.0)
        self.y_spacing_spin.setValue(4.0)
        self.y_spacing_spin.setSuffix(" m")
        form.addRow("Y Spacing:", self.y_spacing_spin)

        self.height_spin = QDoubleSpinBox(self)
        self.height_spin.setRange(0.0, 100.0)
        self.height_spin.setValue(3.5)
        self.height_spin.setSuffix(" m")
        form.addRow("Storey Height:", self.height_spin)

        layout.addWidget(group)

        btn_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal,
            self,
        )
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def get_grid_specs(self) -> Dict[str, Any]:
        return {
            "x_count": self.x_count_spin.value(),
            "x_spacing": self.x_spacing_spin.value(),
            "y_count": self.y_count_spin.value(),
            "y_spacing": self.y_spacing_spin.value(),
            "height": self.height_spin.value(),
        }
