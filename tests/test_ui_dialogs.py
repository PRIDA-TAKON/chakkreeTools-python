"""
Unit tests for PySide6 Parametric Dialogs (FootingDialog, ColumnDialog, BeamDialog)
and ChakkreeToolsPlugin UI integration.
"""

import os
import pytest

# Skip test suite if PySide6 or system GL/EGL GUI libraries are not available
QtWidgets = pytest.importorskip("PySide6.QtWidgets")
QApplication = QtWidgets.QApplication
QDialog = QtWidgets.QDialog

# Ensure Qt offscreen platform for headless test environment
os.environ["QT_QPA_PLATFORM"] = "offscreen"


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_footing_dialog_validation_and_live_calc(qapp):
    from chakkree_tools.ingetrazo_plugin.ui.footing_dialog import FootingDialog
    from PySide6.QtWidgets import QLayout

    dlg = FootingDialog()

    # Verify numerical validation bounds
    assert dlg.thickness_spin.minimum() > 0
    assert dlg.covering_spin.minimum() > 0

    # Verify High-DPI responsiveness properties
    assert dlg.minimumWidth() >= 380
    assert dlg.layout().sizeConstraint() == QLayout.SetMinimumSize

    # Verify live calculation summary label updates when pile count / dimensions change
    initial_text = dlg.calc_info_label.text()
    assert "Footing Size:" in initial_text

    dlg.pile_count_combo.setCurrentIndex(3)  # Change from 1 pile to 4 piles
    updated_text = dlg.calc_info_label.text()
    assert updated_text != initial_text
    assert "Concrete:" in updated_text

    # Test QDoubleSpinBox bounds clamping preventing negative or zero dimensions
    dlg.thickness_spin.setValue(0.0)
    assert dlg.thickness_spin.value() == dlg.thickness_spin.minimum()
    assert dlg.thickness_spin.value() > 0

    dlg.covering_spin.setValue(-0.05)
    assert dlg.covering_spin.value() == dlg.covering_spin.minimum()
    assert dlg.covering_spin.value() > 0


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


def test_column_dialog_validation_and_live_calc(qapp):
    from chakkree_tools.ingetrazo_plugin.ui.column_dialog import ColumnDialog
    from PySide6.QtWidgets import QLayout

    dlg = ColumnDialog()

    # Verify numerical validation bounds
    assert dlg.width_spin.minimum() > 0
    assert dlg.depth_spin.minimum() > 0
    assert dlg.height_spin.minimum() > 0
    assert dlg.stirrup_spacing_spin.minimum() > 0
    assert dlg.covering_spin.minimum() > 0

    # Verify High-DPI responsiveness properties
    assert dlg.minimumWidth() >= 380
    assert dlg.layout().sizeConstraint() == QLayout.SetMinimumSize

    # Verify live calculation summary label updates on height / profile change
    initial_text = dlg.calc_info_label.text()
    assert "Section:" in initial_text

    dlg.height_spin.setValue(5.00)
    updated_text = dlg.calc_info_label.text()
    assert updated_text != initial_text
    assert "Height: 5.00 m" in updated_text

    # Test QDoubleSpinBox bounds clamping preventing negative or zero dimensions
    dlg.width_spin.setValue(0.0)
    assert dlg.width_spin.value() == dlg.width_spin.minimum()
    assert dlg.width_spin.value() > 0

    dlg.height_spin.setValue(-5.0)
    assert dlg.height_spin.value() == dlg.height_spin.minimum()
    assert dlg.height_spin.value() > 0


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


def test_beam_dialog_validation_and_live_calc(qapp):
    from chakkree_tools.ingetrazo_plugin.ui.beam_dialog import BeamDialog
    from PySide6.QtWidgets import QLayout

    dlg = BeamDialog()

    # Verify numerical validation bounds
    assert dlg.length_spin.minimum() > 0
    assert dlg.width_spin.minimum() > 0
    assert dlg.depth_spin.minimum() > 0
    assert dlg.stirrup_zone_end_spin.minimum() > 0
    assert dlg.stirrup_zone_mid_spin.minimum() > 0
    assert dlg.covering_spin.minimum() > 0

    # Verify High-DPI responsiveness properties
    assert dlg.minimumWidth() >= 400
    assert dlg.layout().sizeConstraint() == QLayout.SetMinimumSize

    # Verify live calculation summary label updates when beam span changes
    initial_text = dlg.calc_info_label.text()
    assert "Span: 4.00 m" in initial_text

    dlg.length_spin.setValue(8.00)
    updated_text = dlg.calc_info_label.text()
    assert updated_text != initial_text
    assert "Span: 8.00 m" in updated_text
    assert "L/4 end: 2.00 m" in updated_text

    # Test QDoubleSpinBox bounds clamping preventing negative or zero dimensions
    dlg.length_spin.setValue(0.0)
    assert dlg.length_spin.value() == dlg.length_spin.minimum()
    assert dlg.length_spin.value() > 0

    dlg.depth_spin.setValue(-1.0)
    assert dlg.depth_spin.value() == dlg.depth_spin.minimum()
    assert dlg.depth_spin.value() > 0


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


def test_slab_dialog_validation_and_live_calc(qapp):
    from chakkree_tools.ingetrazo_plugin.ui.slab_dialog import SlabDialog
    from PySide6.QtWidgets import QLayout

    dlg = SlabDialog()

    # Verify numerical validation bounds
    assert dlg.span_x_spin.minimum() > 0
    assert dlg.span_y_spin.minimum() > 0
    assert dlg.thickness_spin.minimum() > 0
    assert dlg.topping_spin.minimum() > 0

    # Verify High-DPI responsiveness properties
    assert dlg.minimumWidth() >= 380
    assert dlg.layout().sizeConstraint() == QLayout.SetMinimumSize

    # Verify live calculation summary label updates when span_x or type changes
    initial_text = dlg.calc_info_label.text()
    assert "Area: 16.00 m²" in initial_text

    dlg.span_x_spin.setValue(5.0)
    updated_text = dlg.calc_info_label.text()
    assert updated_text != initial_text
    assert "Area: 20.00 m²" in updated_text

    # Test type change updates live calculations
    dlg.type_combo.setCurrentIndex(1)  # Cast-in-place RC
    rc_text = dlg.calc_info_label.text()
    assert "Type: RC" in rc_text

    # Test QDoubleSpinBox bounds clamping preventing negative or zero dimensions
    dlg.span_x_spin.setValue(0.0)
    assert dlg.span_x_spin.value() == dlg.span_x_spin.minimum()
    assert dlg.span_x_spin.value() > 0

    dlg.thickness_spin.setValue(-0.5)
    assert dlg.thickness_spin.value() == dlg.thickness_spin.minimum()
    assert dlg.thickness_spin.value() > 0


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


def test_plugin_setup(qapp):
    from chakkree_tools.ingetrazo_plugin.plugin import setup

    class MockIngeTrazoApp:
        def __init__(self):
            self.menus = {}
            self.actions = []

        def add_menu(self, title):
            class MockSubMenu:
                def __init__(self):
                    self.items = []

                def addAction(self, label, cb=None):
                    self.items.append(label)

                def addSeparator(self):
                    self.items.append("---")

            sub = MockSubMenu()
            self.menus[title] = sub
            return sub

        def add_menu_action(self, title, cb, shortcut=None, tip=None):
            self.actions.append(title)

    app = MockIngeTrazoApp()
    plugin = setup(app)
    assert plugin is not None
    assert "Chakkree Tools" in app.menus
    assert "Create Pile Cap (1-9 Piles)..." in app.menus["Chakkree Tools"].items
    # With submenu present, root actions must NOT be duplicated
    assert len(app.actions) == 0

    # Test fallback when add_menu is not available
    app_fallback = MockIngeTrazoApp()
    app_fallback.add_menu = None
    setup(app_fallback)
    assert len(app_fallback.actions) > 0


def test_get_toolbar_registration():
    from pathlib import Path
    from chakkree_tools.ingetrazo_plugin.plugin import ChakkreeToolsPlugin

    plugin = ChakkreeToolsPlugin()
    tb_reg = plugin.get_toolbar_registration()

    assert tb_reg["toolbar_name"] == "chakkree_tools"
    actions = tb_reg["actions"]
    assert len(actions) > 0

    action_names = [a.get("name") for a in actions]
    assert "FootingTools" in action_names
    assert "BeamTools" in action_names
    assert "ColumnTools" in action_names
    assert "SlabTools" in action_names
    assert "GridLine" in action_names
    assert "TakeOff" in action_names
    assert "ConfigColorRebar" in action_names
    assert "About" in action_names

    # Check SVG icon file existence for all actions that have icons
    for item in actions:
        if item.get("type") != "separator" and "icon" in item:
            icon_path = Path(item["icon"])
            assert icon_path.exists(), f"Icon file {icon_path} should exist"


def test_native_qtoolbar_creation_and_actions(qapp):
    from pathlib import Path
    from PySide6.QtWidgets import QMainWindow, QToolBar
    from chakkree_tools.ingetrazo_plugin.plugin import setup

    main_win = QMainWindow()

    class MockAppWithWindow:
        def __init__(self, win):
            self._win = win

        def window(self):
            return self._win

    app = MockAppWithWindow(main_win)
    plugin = setup(app)

    toolbar = main_win.findChild(QToolBar, "ChakkreeToolsToolbar")
    assert toolbar is not None
    assert toolbar.windowTitle() == "Chakkree Tools"
    assert toolbar.isFloatable() is True
    assert toolbar.isMovable() is True

    actions = toolbar.actions()
    action_texts = [act.text() for act in actions if act.text()]

    expected_labels = [
        "Rebar Tools",
        "Footings",
        "Columns",
        "Beams",
        "Slabs",
        "Grid Lines",
        "QTO Take-off",
        "Export .debim",
        "Config Colors",
        "About",
    ]
    for label in expected_labels:
        assert label in action_texts

    # Verify tooltips and icons on QAction
    for act in actions:
        if act.isSeparator():
            continue
        assert act.toolTip() != ""
        assert not act.icon().isNull()
