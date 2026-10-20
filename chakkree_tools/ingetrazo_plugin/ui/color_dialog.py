"""
PySide6 Native Rebar Color Configuration Dialog
Allows viewing and customizing color mapping for rebar sizes (RB6 - DB32).
"""

from typing import Any, Dict, Optional
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QColorDialog,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

DEFAULT_REBAR_COLORS: Dict[str, str] = {
    "RB6": "#B0C4DE",
    "RB9": "#4682B4",
    "DB12": "#2E8B57",
    "DB16": "#FF8C00",
    "DB20": "#DC143C",
    "DB25": "#8B0000",
    "DB28": "#4B0082",
    "DB32": "#2F4F4F",
}


class ColorConfigDialog(QDialog):
    """
    Interactive color configuration dialog for steel reinforcement diameters.
    """

    def __init__(self, parent: Optional[Any] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Rebar Color Configuration")
        self.resize(460, 400)
        self.current_colors = dict(DEFAULT_REBAR_COLORS)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        info_label = QLabel("Click on the color preview button to change color mapping for each rebar size:")
        layout.addWidget(info_label)

        self.table = QTableWidget(len(self.current_colors), 4, self)
        self.table.setHorizontalHeaderLabels(["Size", "Diameter", "Hex Code", "Color Pick"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        dias = {
            "RB6": "6 mm",
            "RB9": "9 mm",
            "DB12": "12 mm",
            "DB16": "16 mm",
            "DB20": "20 mm",
            "DB25": "25 mm",
            "DB28": "28 mm",
            "DB32": "32 mm",
        }

        for row, (sz, hex_val) in enumerate(self.current_colors.items()):
            self.table.setItem(row, 0, QTableWidgetItem(sz))
            self.table.setItem(row, 1, QTableWidgetItem(dias.get(sz, "")))
            hex_item = QTableWidgetItem(hex_val)
            self.table.setItem(row, 2, hex_item)

            btn = QPushButton()
            btn.setStyleSheet(f"background-color: {hex_val}; min-height: 22px; border: 1px solid #555;")
            btn.clicked.connect(lambda checked, s=sz, r=row, b=btn: self._pick_color(s, r, b))
            self.table.setCellWidget(row, 3, btn)

        layout.addWidget(self.table)

        btn_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal,
            self,
        )
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def _pick_color(self, size: str, row: int, btn: QPushButton) -> None:
        curr = QColor(self.current_colors[size])
        col = QColorDialog.getColor(curr, self, f"Select Color for {size}")
        if col.isValid():
            hex_code = col.name().upper()
            self.current_colors[size] = hex_code
            self.table.item(row, 2).setText(hex_code)
            btn.setStyleSheet(f"background-color: {hex_code}; min-height: 22px; border: 1px solid #555;")

    def get_colors(self) -> Dict[str, str]:
        return dict(self.current_colors)
