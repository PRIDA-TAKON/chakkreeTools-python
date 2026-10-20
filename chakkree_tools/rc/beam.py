"""
Parametric RC Beam Models
Ported from Chakkree Tools (SimpleBeam_01.crs and Continuous Beams)
Original Author: Chakkree Tiyawongsuwan
"""

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class Beam:
    id: str
    name: str = ""
    width: float = 0.20  # b (m)
    depth: float = 0.40  # h (m)
    start_point: Tuple[float, float] = (0.0, 0.0)
    end_point: Tuple[float, float] = (4.0, 0.0)
    elevation: float = 3.20  # Top of beam level
    from_grid: Optional[Tuple[str, str]] = None
    to_grid: Optional[Tuple[str, str]] = None

    # Rebars
    top_bar_spec: str = "2DB12"
    bot_bar_spec: str = "3DB12"
    extra_bar_spec: Optional[str] = "1DB12"
    stirrup_spec: str = "RB6@0.175"
    stirrup_spacing_end: Optional[float] = None  # End support zone spacing s1 (e.g. 0.10m for L/4)
    stirrup_spacing_mid: Optional[float] = None  # Midspan zone spacing s2 (e.g. 0.20m for L/2)
    covering: float = 0.025  # 25mm

    @property
    def length(self) -> float:
        """Clear span or total span between points."""
        dx = self.end_point[0] - self.start_point[0]
        dy = self.end_point[1] - self.start_point[1]
        return math.hypot(dx, dy)

    @property
    def concrete_volume(self) -> float:
        """Volume in m3."""
        return self.width * self.depth * self.length

    @property
    def formwork_area(self) -> float:
        """Soffit + 2 sides formwork area in m2."""
        return (self.width + 2.0 * self.depth) * self.length

    def to_debim_dict(self, storey_id: str = "ST_01") -> Dict[str, Any]:
        """Converts to debim declarative manifest element."""
        res: Dict[str, Any] = {
            "id": self.id,
            "class": "IfcBeam",
            "storey": storey_id,
            "tag": "S-BEAM",
            "dimensions": {
                "width": round(self.width, 3),
                "depth": round(self.depth, 3),
            },
            "elevation": round(self.elevation, 3),
            "rebar": {
                "main_top": self.top_bar_spec,
                "main_bottom": self.bot_bar_spec,
                "stirrups": self.stirrup_spec,
                "covering": round(self.covering, 3),
            },
        }
        if self.stirrup_spacing_end is not None and self.stirrup_spacing_mid is not None:
            res["rebar"]["stirrup_spacing_end"] = round(self.stirrup_spacing_end, 3)
            res["rebar"]["stirrup_spacing_mid"] = round(self.stirrup_spacing_mid, 3)

        res["qto"] = {
            "concrete_m3": round(self.concrete_volume, 3),
            "formwork_m2": round(self.formwork_area, 3),
        }
        if self.extra_bar_spec:
            res["rebar"]["extra_bottom"] = self.extra_bar_spec

        if self.from_grid and self.to_grid:
            res["placement"] = {
                "from_grid": list(self.from_grid),
                "to_grid": list(self.to_grid),
            }
        else:
            res["placement"] = {
                "start": [round(self.start_point[0], 3), round(self.start_point[1], 3)],
                "end": [round(self.end_point[0], 3), round(self.end_point[1], 3)],
            }
        return res
