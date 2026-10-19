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

    def cmd_rebar_tools(self) -> None:
        """Handler for Rebar Tools."""
        pass

    def cmd_create_grids(self) -> None:
        """Handler for GridLine creation."""
        pass

    def cmd_qto_takeoff(self) -> None:
        """Handler for QTO TakeOff."""
        pass

    def cmd_config_colors(self) -> None:
        """Handler for Rebar Colors Configuration."""
        pass

    def cmd_about(self) -> None:
        """Handler for About info."""
        pass

    def cmd_create_pile_cap(self, pile_count: int = 1) -> Any:
        from chakkree_tools.rc.footing import PileCap
        f = PileCap.create_n_piles(
            id_str=f"F_{len(self.active_elements) + 1}",
            pile_count=pile_count,
        )
        self.active_elements.append(f)
        return f

    def cmd_create_column(self, width: float = 0.3, depth: float = 0.3, height: float = 3.5) -> Any:
        from chakkree_tools.rc.column import Column
        c = Column(
            id=f"C_{len(self.active_elements) + 1}",
            width=width,
            depth=depth,
            height=height,
        )
        self.active_elements.append(c)
        return c

    def cmd_create_beam(self, width: float = 0.2, depth: float = 0.4, length: float = 4.0) -> Any:
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

    def cmd_export_debim(self, output_path: str = "chakkree_model.debim.yaml") -> Path:
        from chakkree_tools.exporter.debim_exporter import export_to_debim
        return export_to_debim(
            elements=self.active_elements,
            output_path=output_path,
            project_name="Chakkree Tools IngeTrazo Export",
        )
