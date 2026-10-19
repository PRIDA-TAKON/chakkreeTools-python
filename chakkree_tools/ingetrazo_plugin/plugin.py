"""
IngeTrazo Plugin Entry Point for Chakkree Tools
Registers toolbars, menus, and 3D modeling actions within IngeTrazo CAD.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

try:
    from ingetrazo.sdk import Tool  # type: ignore
except ImportError:
    class Tool:
        """Fallback base Tool class when IngeTrazo SDK is not installed."""
        def __init__(self, name: str = "ChakkreeToolsPlugin") -> None:
            self.name = name
            self.active = False

        def activate(self) -> None:
            self.active = True

        def deactivate(self) -> None:
            self.active = False


class ChakkreeToolsPlugin(Tool):
    """
    IngeTrazo plugin providing parametric RC structural tools and .debim export.
    """

    def __init__(self, app: Optional[Any] = None) -> None:
        super().__init__(name="chakkree_tools")
        self.app = app
        self.active_elements: List[Any] = []

    def get_menu_registration(self) -> Dict[str, Any]:
        """
        Registers menu items under Extensions > Chakkree Tools.
        """
        return {
            "menu_path": "Extensions > Chakkree Tools",
            "items": [
                {
                    "label": "Create Pile Cap (1-9 Piles)...",
                    "action": self.cmd_create_pile_cap,
                },
                {
                    "label": "Create RC Column (4-16 Bars)...",
                    "action": self.cmd_create_column,
                },
                {
                    "label": "Create RC Beam...",
                    "action": self.cmd_create_beam,
                },
                {
                    "label": "Create Slab (PS Plank / RC)...",
                    "action": self.cmd_create_slab,
                },
                {
                    "label": "Export Model to .debim...",
                    "action": self.cmd_export_debim,
                    "shortcut": "Ctrl+Shift+E",
                },
            ],
        }

    def get_toolbar_registration(self) -> Dict[str, Any]:
        """
        Registers toolbar actions for IngeTrazo matching the original Chakkree Tools UI.
        """
        icons_dir = Path(__file__).resolve().parent / "resources" / "icons"
        return {
            "toolbar_name": "chakkree_tools",
            "actions": [
                {
                    "name": "RebarTools",
                    "label": "Rebar Tools",
                    "tooltip": "เครื่องมือเหล็กเสริม (Rebar Tools) - ดัดขอและสร้างเหล็กเสริม 3D",
                    "icon": str(icons_dir / "RebarTools.svg"),
                    "action": self.cmd_rebar_tools,
                },
                {
                    "name": "FootingTools",
                    "label": "Footings",
                    "tooltip": "เครื่องมือฐานราก (Footing Tools) - ฐานรากเสาเข็ม 1-9 ต้น และฐานแผ่",
                    "icon": str(icons_dir / "FootingTools.svg"),
                    "action": self.cmd_create_pile_cap,
                },
                {
                    "name": "BeamTools",
                    "label": "Beams",
                    "tooltip": "เครื่องมือคาน ค.ส.ล. (Beam Tools) - คานและเหล็กปลอกหลายระยะ",
                    "icon": str(icons_dir / "BeamTools.svg"),
                    "action": self.cmd_create_beam,
                },
                {
                    "name": "ColumnTools",
                    "label": "Columns",
                    "tooltip": "เครื่องมือเสา ค.ส.ล. (Column Tools) - เสาสี่เหลี่ยม/กลม เหล็กยืน 4-16 เส้น",
                    "icon": str(icons_dir / "ColumnTools.svg"),
                    "action": self.cmd_create_column,
                },
                {"name": "separator_1", "type": "separator"},
                {
                    "name": "GridLine",
                    "label": "Grid Lines",
                    "tooltip": "เครื่องมือกริตไลน์ (GridLine v2026) - ระบบแกน X/Y และระดับชั้น",
                    "icon": str(icons_dir / "GridLine.svg"),
                    "action": self.cmd_create_grids,
                },
                {"name": "separator_2", "type": "separator"},
                {
                    "name": "TakeOff",
                    "label": "QTO Take-off",
                    "tooltip": "ถอดปริมาณ คอนกรีต ไม้แบบ เหล็กเสริม และ Bar Bending Schedule",
                    "icon": str(icons_dir / "TakeOff.svg"),
                    "action": self.cmd_qto_takeoff,
                },
                {
                    "name": "AnalysisRC",
                    "label": "RC Analysis",
                    "tooltip": "วิเคราะห์กำลังรับแรงหน้าตัด ค.ส.ล. และส่งออก .debim",
                    "icon": str(icons_dir / "AnalysisTool.svg"),
                    "action": self.cmd_export_debim,
                },
                {"name": "separator_3", "type": "separator"},
                {
                    "name": "ConfigColorRebar",
                    "label": "Config Colors",
                    "tooltip": "ตั้งค่าสีเหล็กเสริมแยกตามขนาดเส้นผ่านศูนย์กลาง (RB6, RB9, DB12-DB32)",
                    "icon": str(icons_dir / "ConfigColorRebar.svg"),
                    "action": self.cmd_config_colors,
                },
                {"name": "separator_4", "type": "separator"},
                {
                    "name": "About",
                    "label": "About",
                    "tooltip": "เกี่ยวกับ Chakkree Tools (Python Edition) © อ.จักรี ติยะวงศ์สุวรรณ",
                    "icon": str(icons_dir / "About.svg"),
                    "action": self.cmd_about,
                },
            ],
        }

    def cmd_rebar_tools(self, parent: Optional[Any] = None) -> None:
        """Handler for Rebar Tools & Standards."""
        try:
            from PySide6.QtWidgets import QApplication, QMessageBox
            if QApplication.instance() is not None:
                win = parent or getattr(self.app, "window", getattr(self.app, "_window", None))
                if callable(win):
                    win = win()
                msg = (
                    "Chakkree Rebar Standards (ว.ส.ท. / EIT):\n\n"
                    "• Standard Hook: 90° hook = 12 x db, 180° hook = 4 x db (min 6.5 cm)\n"
                    "• Stirrup Hook: 135° seismic hook = 6 x db (min 7.5 cm)\n"
                    "• Lap Splice Length: Tension = 40 x db, Compression = 30 x db\n"
                    "• Minimum Concrete Cover: Footing 7.5cm, Column 4.0cm, Beam 4.0cm, Slab 2.5cm"
                )
                QMessageBox.information(win, "Rebar Standard Details", msg)
        except ImportError:
            pass

    def cmd_create_grids(self, parent: Optional[Any] = None) -> None:
        """Handler for GridLine creation."""
        try:
            from PySide6.QtWidgets import QApplication, QMessageBox
            if QApplication.instance() is not None:
                win = parent or getattr(self.app, "window", getattr(self.app, "_window", None))
                if callable(win):
                    win = win()
                QMessageBox.information(
                    win,
                    "Grid Lines",
                    "Grid Lines (GridLine v2026)\n\nGenerates structural axes X/Y with datum level markers.",
                )
        except ImportError:
            pass

    def cmd_qto_takeoff(self, parent: Optional[Any] = None) -> Any:
        """Handler for QTO TakeOff."""
        from chakkree_tools.qto.takeoff import generate_qto_summary
        summary = generate_qto_summary(self.active_elements)
        try:
            from PySide6.QtWidgets import QApplication, QMessageBox
            if QApplication.instance() is not None:
                win = parent or getattr(self.app, "window", getattr(self.app, "_window", None))
                if callable(win):
                    win = win()
                lines = [
                    "=== Chakkree Tools QTO Summary ===",
                    f"Total Elements: {summary.total_elements}",
                    f"Concrete Volume: {summary.total_concrete_volume_m3:.3f} m³",
                    f"Formwork Area: {summary.total_formwork_area_m2:.2f} m²",
                    f"Total Rebar Weight: {summary.total_rebar_weight_kg:.2f} kg",
                    "",
                    "Rebar Breakdown (BBS):",
                ]
                for bar_type, wt in summary.rebar_weight_by_size.items():
                    lines.append(f"  • {bar_type}: {wt:.2f} kg")
                QMessageBox.information(
                    win,
                    "QTO & Bar Bending Schedule",
                    "\n".join(lines),
                )
        except ImportError:
            pass
        return summary

    def cmd_config_colors(self, parent: Optional[Any] = None) -> None:
        """Handler for Rebar Colors Configuration."""
        try:
            from PySide6.QtWidgets import QApplication, QMessageBox
            if QApplication.instance() is not None:
                win = parent or getattr(self.app, "window", getattr(self.app, "_window", None))
                if callable(win):
                    win = win()
                msg = (
                    "Rebar Standard Diameter Color Mapping:\n\n"
                    "• RB6 (6mm)  : #B0C4DE (Light Steel Blue)\n"
                    "• RB9 (9mm)  : #4682B4 (Steel Blue)\n"
                    "• DB12 (12mm): #2E8B57 (Sea Green)\n"
                    "• DB16 (16mm): #FF8C00 (Dark Orange)\n"
                    "• DB20 (20mm): #DC143C (Crimson)\n"
                    "• DB25 (25mm): #8B0000 (Dark Red)\n"
                    "• DB28 (28mm): #4B0082 (Indigo)\n"
                    "• DB32 (32mm): #2F4F4F (Dark Slate Gray)"
                )
                QMessageBox.information(win, "Rebar Color Standards", msg)
        except ImportError:
            pass

    def cmd_about(self, parent: Optional[Any] = None) -> None:
        """Handler for About info."""
        try:
            from PySide6.QtWidgets import QApplication, QMessageBox
            if QApplication.instance() is not None:
                win = parent or getattr(self.app, "window", getattr(self.app, "_window", None))
                if callable(win):
                    win = win()
                title = "About Chakkree Tools (Python Edition)"
                message = (
                    "Chakkree Tools (Python Edition for IngeTrazo) v0.1.0\n\n"
                    "Reverse-engineered and ported to IngeTrazo CAD with OpenBIM .debim integration.\n"
                    "Original SketchUp extension created by อ.จักรี ติยะวงศ์สุวรรณ.\n\n"
                    "หากคุณชอบและได้รับประโยชน์จากส่วนขยายนี้ สามารถสนับสนุนนักพัฒนาต้นฉบับได้ที่:\n"
                    "https://sites.google.com/view/learn-sketchup/myextension/chakkree_tools-v0-4?authuser=0\n\n"
                    "GitHub: https://github.com/PRIDA-TAKON/chakkreeTools-python"
                )
                QMessageBox.information(win, title, message)
        except ImportError:
            pass

    def cmd_stream_to_bridge(self, host: str = "127.0.0.1", port: int = 8482) -> bool:
        """Handler to live-stream active elements to IngeTrazo via Agent Bridge."""
        from chakkree_tools.exporter.debim_exporter import DebimExporter
        from chakkree_tools.ingetrazo_plugin.agent_streamer import stream_to_ingetrazo
        exporter = DebimExporter(project_name="Chakkree Live Stream")
        for el in self.active_elements:
            exporter.add_element(el)
        manifest_yaml = exporter.to_yaml()
        try:
            result = stream_to_ingetrazo(manifest_yaml, host=host, port=port)
            if hasattr(self.app, "flash_status"):
                self.app.flash_status("Chakkree Tools: Streamed to IngeTrazo successfully!")
            return result
        except Exception as e:
            if hasattr(self.app, "flash_status"):
                self.app.flash_status(f"Stream error: {e}")
            return False

    def cmd_create_pile_cap(
        self, pile_count: int = 1, show_dialog: bool = True, parent: Optional[Any] = None
    ) -> Any:
        """
        Action to create Footing / Pile Cap. Opens FootingDialog if show_dialog is True and PySide6 is available.
        """
        if show_dialog:
            try:
                from PySide6.QtWidgets import QApplication, QDialog
                from chakkree_tools.ingetrazo_plugin.ui.footing_dialog import FootingDialog

                if QApplication.instance() is not None:
                    dlg = FootingDialog(parent=parent)
                    if dlg.exec() == QDialog.Accepted:
                        f = dlg.get_footing()
                        self.active_elements.append(f)
                        return f
                    return None
            except ImportError:
                pass

        from chakkree_tools.rc.footing import PileCap
        f = PileCap.create_n_piles(
            id_str=f"F_{len(self.active_elements) + 1}",
            pile_count=pile_count,
        )
        self.active_elements.append(f)
        return f

    def cmd_create_column(
        self,
        width: float = 0.3,
        depth: float = 0.3,
        height: float = 3.5,
        show_dialog: bool = True,
        parent: Optional[Any] = None,
    ) -> Any:
        """
        Action to create RC Column. Opens ColumnDialog if show_dialog is True and PySide6 is available.
        """
        if show_dialog:
            try:
                from PySide6.QtWidgets import QApplication, QDialog
                from chakkree_tools.ingetrazo_plugin.ui.column_dialog import ColumnDialog

                if QApplication.instance() is not None:
                    dlg = ColumnDialog(parent=parent)
                    if dlg.exec() == QDialog.Accepted:
                        c = dlg.get_column()
                        self.active_elements.append(c)
                        return c
                    return None
            except ImportError:
                pass

        from chakkree_tools.rc.column import Column
        c = Column(
            id=f"C_{len(self.active_elements) + 1}",
            width=width,
            depth=depth,
            height=height,
        )
        self.active_elements.append(c)
        return c

    def cmd_create_beam(
        self,
        width: float = 0.2,
        depth: float = 0.4,
        length: float = 4.0,
        show_dialog: bool = True,
        parent: Optional[Any] = None,
    ) -> Any:
        """
        Action to create RC Beam. Opens BeamDialog if show_dialog is True and PySide6 is available.
        """
        if show_dialog:
            try:
                from PySide6.QtWidgets import QApplication, QDialog
                from chakkree_tools.ingetrazo_plugin.ui.beam_dialog import BeamDialog

                if QApplication.instance() is not None:
                    dlg = BeamDialog(parent=parent)
                    if dlg.exec() == QDialog.Accepted:
                        b = dlg.get_beam()
                        self.active_elements.append(b)
                        return b
                    return None
            except ImportError:
                pass

        from chakkree_tools.rc.beam import Beam
        b = Beam(
            id=f"B_{len(self.active_elements) + 1}",
            width=width,
            depth=depth,
            start_point=(0.0, 0.0),
            end_point=(length, 0.0),
        )
        self.active_elements.append(b)
        return b

    def cmd_create_slab(self, boundary: Optional[List[Any]] = None) -> Any:
        from chakkree_tools.rc.slab import Slab
        s = Slab(
            id=f"SLAB_{len(self.active_elements) + 1}",
            boundary=boundary or [(0.0, 0.0), (4.0, 0.0), (4.0, 4.0), (0.0, 4.0)],
        )
        self.active_elements.append(s)
        return s

    def cmd_export_debim(
        self,
        output_path: Optional[Union[str, Path]] = None,
        parent: Optional[Any] = None,
    ) -> Optional[Path]:
        if output_path is None:
            try:
                from PySide6.QtWidgets import QApplication, QFileDialog
                if QApplication.instance() is not None:
                    win = parent or getattr(self.app, "window", getattr(self.app, "_window", None))
                    if callable(win):
                        win = win()
                    chosen_path, _ = QFileDialog.getSaveFileName(
                        win,
                        "Export Model to .debim",
                        "chakkree_model.debim.yaml",
                        "debim Manifest (*.debim.yaml *.yaml *.debim);;All Files (*.*)",
                    )
                    if not chosen_path:
                        return None
                    output_path = chosen_path
                else:
                    output_path = "chakkree_model.debim.yaml"
            except ImportError:
                output_path = "chakkree_model.debim.yaml"

        from chakkree_tools.exporter.debim_exporter import export_to_debim
        res = export_to_debim(
            elements=self.active_elements,
            output_path=str(output_path),
            project_name="Chakkree Tools IngeTrazo Export",
        )
        if hasattr(self.app, "flash_status"):
            self.app.flash_status(f"Exported .debim to {Path(output_path).name}")
        return res


def setup(app: Any) -> ChakkreeToolsPlugin:
    """
    Official setup(app) entry point called by IngeTrazo extension loader.
    Registers menus, actions, and the native PySide6 toolbar in IngeTrazo.
    """
    plugin = ChakkreeToolsPlugin(app=app)

    # 1. Register Menus under Extensions -> Chakkree Tools
    menu = None
    if hasattr(app, "add_menu"):
        menu = app.add_menu("Chakkree Tools")

    if menu is not None:
        menu.addAction("Create Pile Cap (1-9 Piles)...", lambda: plugin.cmd_create_pile_cap())
        menu.addAction("Create RC Column (4-16 Bars)...", lambda: plugin.cmd_create_column())
        menu.addAction("Create RC Beam...", lambda: plugin.cmd_create_beam())
        menu.addAction("Create Slab (PS Plank / RC)...", lambda: plugin.cmd_create_slab())
        menu.addSeparator()
        menu.addAction("Rebar Tools & Details...", lambda: plugin.cmd_rebar_tools())
        menu.addAction("Grid Lines...", lambda: plugin.cmd_create_grids())
        menu.addAction("Rebar Color Config...", lambda: plugin.cmd_config_colors())
        menu.addSeparator()
        menu.addAction("QTO Take-off Report...", lambda: plugin.cmd_qto_takeoff())
        menu.addAction("Export Model to .debim...", lambda: plugin.cmd_export_debim())
        menu.addAction("Live Stream to IngeTrazo (Port 8482)...", lambda: plugin.cmd_stream_to_bridge())
        menu.addSeparator()
        menu.addAction("About Chakkree Tools...", lambda: plugin.cmd_about())

    # Fallback or additional quick-access actions directly in Extensions menu
    if hasattr(app, "add_menu_action"):
        app.add_menu_action("Chakkree: Footings (Pile Cap)...", lambda: plugin.cmd_create_pile_cap(), tip="Create Pile Cap / Footing")
        app.add_menu_action("Chakkree: RC Columns...", lambda: plugin.cmd_create_column(), tip="Create RC Column")
        app.add_menu_action("Chakkree: RC Beams...", lambda: plugin.cmd_create_beam(), tip="Create RC Beam")
        app.add_menu_action("Chakkree: Slabs...", lambda: plugin.cmd_create_slab(), tip="Create RC Slab")
        app.add_menu_action("Chakkree: QTO Take-off...", lambda: plugin.cmd_qto_takeoff(), tip="Automated BBS & Quantity Take-off")
        app.add_menu_action("Chakkree: Export .debim...", lambda: plugin.cmd_export_debim(), tip="Export to .debim manifest")
        app.add_menu_action("Chakkree: Stream to Bridge (Port 8482)...", lambda: plugin.cmd_stream_to_bridge(), tip="Stream to IngeTrazo port 8482")
        app.add_menu_action("Chakkree: About...", lambda: plugin.cmd_about(), tip="About Chakkree Tools")

    # 2. Register Toolbar on IngeTrazo main window
    win = getattr(app, "window", getattr(app, "_window", None))
    if callable(win):
        win = win()
    if win is None and hasattr(app, "viewport") and hasattr(app.viewport, "window"):
        win = app.viewport.window()
        if callable(win):
            win = win()

    if win is not None:
        try:
            from PySide6.QtWidgets import QToolBar
            from PySide6.QtGui import QIcon, QAction
            from PySide6.QtCore import Qt, QSize

            tb_id = "ChakkreeToolsToolbar"
            existing_tb = win.findChild(QToolBar, tb_id)
            if existing_tb is None:
                toolbar = QToolBar("Chakkree Tools", win)
                toolbar.setObjectName(tb_id)
                toolbar.setIconSize(QSize(24, 24))

                icons_dir = Path(__file__).resolve().parent / "resources" / "icons"
                if not icons_dir.exists():
                    icons_dir = Path(__file__).resolve().parent.parent / "resources" / "icons"

                actions_data = [
                    ("RebarTools.svg", "Rebar Tools", "เครื่องมือเหล็กเสริม (Rebar Tools) - ดัดขอและสร้างเหล็กเสริม 3D", plugin.cmd_rebar_tools),
                    ("FootingTools.svg", "Footings", "เครื่องมือฐานราก (Footing Tools) - ฐานรากเสาเข็ม 1-9 ต้น", plugin.cmd_create_pile_cap),
                    ("ColumnTools.svg", "Columns", "เครื่องมือเสา ค.ส.ล. (Column Tools)", plugin.cmd_create_column),
                    ("BeamTools.svg", "Beams", "เครื่องมือคาน ค.ส.ล. (Beam Tools)", plugin.cmd_create_beam),
                    (None, None, None, None),  # Separator
                    ("GridLine.svg", "Grid Lines", "เครื่องมือกริตไลน์ (GridLine v2026)", plugin.cmd_create_grids),
                    ("TakeOff.svg", "QTO Take-off", "ถอดปริมาณ คอนกรีต ไม้แบบ เหล็กเสริม และ Bar Bending Schedule", plugin.cmd_qto_takeoff),
                    ("AnalysisTool.svg", "Export .debim", "ส่งออกโมเดล .debim สำหรับ debim CLI / OpenBIM", plugin.cmd_export_debim),
                    (None, None, None, None),  # Separator
                    ("ConfigColorRebar.svg", "Config Colors", "ตั้งค่าสีเหล็กเสริมแยกตามขนาดเส้นผ่านศูนย์กลาง", plugin.cmd_config_colors),
                    ("About.svg", "About", "เกี่ยวกับ Chakkree Tools (Python Edition)", plugin.cmd_about),
                ]

                for item in actions_data:
                    icon_name, label, tooltip, callback = item
                    if icon_name is None:
                        toolbar.addSeparator()
                        continue
                    icon_file = icons_dir / icon_name
                    action = QAction(label, toolbar)
                    if icon_file.exists():
                        action.setIcon(QIcon(str(icon_file)))
                    if tooltip:
                        action.setToolTip(tooltip)
                    if callback:
                        action.triggered.connect(lambda _c=False, cb=callback: cb())
                    toolbar.addAction(action)

                win.addToolBar(Qt.TopToolBarArea, toolbar)
        except Exception as e:
            print(f"[chakkree_tools] Notice: Could not register toolbar: {e}")

    return plugin

