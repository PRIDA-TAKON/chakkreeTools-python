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
        Registers toolbar actions for IngeTrazo.
        """
        return {
            "toolbar_name": "Chakkree Tools (RC)",
            "actions": [
                {
                    "name": "PileFooting",
                    "label": "Pile Cap",
                    "tooltip": "Generate 1-9 Piles Pile Cap & Rebars",
                    "action": self.cmd_create_pile_cap,
                },
                {
                    "name": "Column",
                    "label": "RC Column",
                    "tooltip": "Generate RC Column with Longitudinal & Tie Rebars",
                    "action": self.cmd_create_column,
                },
                {
                    "name": "Beam",
                    "label": "RC Beam",
                    "tooltip": "Generate RC Beam with Rebars & Multi-zone Stirrups",
                    "action": self.cmd_create_beam,
                },
                {
                    "name": "ExportDebim",
                    "label": "Export .debim",
                    "tooltip": "Export designed structural model to .debim manifest",
                    "action": self.cmd_export_debim,
                },
            ],
        }

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
