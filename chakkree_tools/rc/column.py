"""
Parametric Column Models
Ported from Chakkree Tools (Rectangular 4/6/8/14/16 bars & Circular columns)
Original Author: Chakkree Tiyawongsuwan
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class Column:
    id: str
    name: str = ""
    profile: str = "RECTANGULAR"  # 'RECTANGULAR' or 'CIRCULAR'
    width: float = 0.30  # b (m)
    depth: float = 0.30  # t (m)
    height: float = 3.50  # h (m)
    elevation: float = 0.0  # base Z
    position: Tuple[float, float] = (0.0, 0.0)  # [x, y]
    grid_ref: Optional[Tuple[str, str]] = None  # e.g. ["1", "A"]

    # Rebars
    main_bar_count: int = 8
    main_bar_dia: float = 0.016  # DB16
    stirrup_dia: float = 0.009  # RB9
    stirrup_spacing: float = 0.150  # 150mm
    covering: float = 0.030  # 30mm

    # Extension beyond column ends for lap splice
    ext_top: float = -0.050
    ext_bottom: float = 0.200

    @property
    def concrete_volume(self) -> float:
        """Volume in m3."""
        if self.profile.upper() == "CIRCULAR":
            radius = self.width / 2.0
            return 3.14159265 * (radius**2) * self.height
        return self.width * self.depth * self.height

    @property
    def formwork_area(self) -> float:
        """Surface formwork area in m2."""
        if self.profile.upper() == "CIRCULAR":
            return 3.14159265 * self.width * self.height
        return 2.0 * (self.width + self.depth) * self.height

    def to_debim_dict(self, storey_id: str = "ST_01") -> Dict[str, Any]:
        """Converts to debim declarative manifest element."""
        res: Dict[str, Any] = {
            "id": self.id,
            "class": "IfcColumn",
            "storey": storey_id,
            "tag": "S-COLS",
            "profile": self.profile.upper(),
            "dimensions": {
                "width": round(self.width, 3),
                "depth": round(self.depth, 3),
            },
            "height": round(self.height, 3),
            "rebar": {
                "main_bars": f"{self.main_bar_count}DB{int(self.main_bar_dia * 1000)}",
                "stirrups": f"RB{int(self.stirrup_dia * 1000)}@{round(self.stirrup_spacing, 3)}",
                "covering": round(self.covering, 3),
            },
            "qto": {
                "concrete_m3": round(self.concrete_volume, 3),
                "formwork_m2": round(self.formwork_area, 3),
            },
        }
        if self.grid_ref:
            res["placement"] = {"grid": list(self.grid_ref)}
        else:
            res["placement"] = {
                "position": [round(self.position[0], 3), round(self.position[1], 3)],
                "offset_z": round(self.elevation, 3),
            }
        return res
