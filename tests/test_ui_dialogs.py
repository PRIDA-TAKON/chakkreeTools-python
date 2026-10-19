"""
Unit tests for PySide6 Parametric Dialogs (FootingDialog, ColumnDialog, BeamDialog)
and ChakkreeToolsPlugin UI integration.
"""

import os
import pytest
from PySide6.QtWidgets import QApplication, QDialog

# Ensure Qt offscreen platform for headless test environment
os.environ["QT_QPA_PLATFORM"] = "offscreen"


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_footing_dialog_default_and_custom(qapp):
    from chakkree_tools.ingetrazo_plugin.ui.footing_dialog import FootingDialog
    from chakkree_tools.rc.footing import Footing

    dlg = FootingDialog()
    assert dlg.id_input.text() == "F1"
    assert dlg.pile_count_combo.count() == 9

    # Default footing check
    f_default = dlg.get_footing()
    assert isinstance(f_default, Footing)
    assert f_default.id == "F1"
    assert f_default.pile_spec.count == 1
    assert f_default.pile_spec.size == 0.220
    assert f_default.thickness == 0.60
    assert f_default.elevation == -0.70
    assert f_default.covering == 0.070

    # Custom inputs check
    dlg.id_input.setText("F_TEST_4P")
    dlg.pile_count_combo.setCurrentIndex(3)  # 4 Piles (0-indexed: 0=1, 1=2, 2=3, 3=4)
    dlg.pile_dia_combo.setCurrentIndex(3)    # 300 mm (0.300 m)
    dlg.rebar_size_combo.setCurrentIndex(2)  # DB20 (0.020 m)
    dlg.thickness_spin.setValue(0.85)
    dlg.elevation_spin.setValue(-1.50)
    dlg.covering_spin.setValue(0.075)

    f_custom = dlg.get_footing()
    assert f_custom.id == "F_TEST_4P"
    assert f_custom.pile_spec.count == 4
    assert f_custom.pile_spec.size == 0.300
    assert f_custom.rebar_x_dia == 0.020
    assert f_custom.thickness == 0.85
    assert f_custom.elevation == -1.50
    assert f_custom.covering == 0.075


def test_column_dialog_default_and_custom(qapp):
    from chakkree_tools.ingetrazo_plugin.ui.column_dialog import ColumnDialog
    from chakkree_tools.rc.column import Column

    dlg = ColumnDialog()
    assert dlg.id_input.text() == "C1"

    c_default = dlg.get_column()
    assert isinstance(c_default, Column)
    assert c_default.id == "C1"
    assert c_default.profile == "RECTANGULAR"
    assert c_default.width == 0.30
    assert c_default.depth == 0.30
    assert c_default.height == 3.50
    assert c_default.main_bar_count == 8

    # Custom inputs
    dlg.id_input.setText("C_CIRCULAR")
    dlg.profile_combo.setCurrentIndex(1)  # Circular
    dlg.width_spin.setValue(0.40)
    dlg.depth_spin.setValue(0.40)
    dlg.height_spin.setValue(4.20)
    dlg.main_bar_count_combo.setCurrentIndex(4)  # 12 Bars (index 4 in [4, 6, 8, 10, 12, 14, 16])
    dlg.main_bar_dia_combo.setCurrentIndex(3)    # DB25
    dlg.stirrup_dia_combo.setCurrentIndex(2)     # DB10
    dlg.stirrup_spacing_spin.setValue(0.100)
    dlg.covering_spin.setValue(0.035)

    c_custom = dlg.get_column()
    assert c_custom.id == "C_CIRCULAR"
    assert c_custom.profile == "CIRCULAR"
    assert c_custom.width == 0.40
    assert c_custom.depth == 0.40
    assert c_custom.height == 4.20
    assert c_custom.main_bar_count == 12
    assert c_custom.main_bar_dia == 0.025
    assert c_custom.stirrup_dia == 0.010
    assert c_custom.stirrup_spacing == 0.100
    assert c_custom.covering == 0.035


def test_beam_dialog_default_and_custom(qapp):
    from chakkree_tools.ingetrazo_plugin.ui.beam_dialog import BeamDialog
    from chakkree_tools.rc.beam import Beam

    dlg = BeamDialog()
    assert dlg.id_input.text() == "B1"

    b_default = dlg.get_beam()
    assert isinstance(b_default, Beam)
    assert b_default.id == "B1"
    assert b_default.length == 4.00
    assert b_default.width == 0.20
    assert b_default.depth == 0.40
    assert b_default.top_bar_spec == "2DB12"
    assert b_default.bot_bar_spec == "3DB12"

    # Custom inputs (multi-zone stirrups)
    dlg.id_input.setText("B_ZONE_TEST")
    dlg.length_spin.setValue(6.00)
    dlg.width_spin.setValue(0.25)
    dlg.depth_spin.setValue(0.50)
    dlg.elevation_spin.setValue(4.00)
    dlg.top_bar_input.setText("3DB16")
    dlg.bot_bar_input.setText("4DB16")
    dlg.extra_bar_input.setText("2DB16")

    dlg.stirrup_bar_combo.setCurrentIndex(1)  # RB9
    dlg.stirrup_zone_end_spin.setValue(0.100)
    dlg.stirrup_zone_mid_spin.setValue(0.200)
    dlg.covering_spin.setValue(0.030)

    b_custom = dlg.get_beam()
    assert b_custom.id == "B_ZONE_TEST"
    assert b_custom.length == 6.00
    assert b_custom.width == 0.25
    assert b_custom.depth == 0.50
    assert b_custom.elevation == 4.00
    assert b_custom.top_bar_spec == "3DB16"
    assert b_custom.bot_bar_spec == "4DB16"
    assert b_custom.extra_bar_spec == "2DB16"
    assert b_custom.stirrup_spec == "RB9@0.100/0.200/0.100"
    assert b_custom.covering == 0.030


def test_plugin_cmd_creators(qapp):
    from chakkree_tools.ingetrazo_plugin.plugin import ChakkreeToolsPlugin

    plugin = ChakkreeToolsPlugin()
    assert len(plugin.active_elements) == 0

    f = plugin.cmd_create_pile_cap(pile_count=2, show_dialog=False)
    assert f.pile_spec.count == 2
    assert len(plugin.active_elements) == 1

    c = plugin.cmd_create_column(width=0.4, depth=0.4, show_dialog=False)
    assert c.width == 0.4
    assert len(plugin.active_elements) == 2

    b = plugin.cmd_create_beam(width=0.25, depth=0.5, length=5.0, show_dialog=False)
    assert b.length == 5.0
    assert len(plugin.active_elements) == 3
