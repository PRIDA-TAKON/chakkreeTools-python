"""
Parametric Slab Models
Ported from Chakkree Tools (Precast Plank Slab PS.crs and Cast-in-place slabs)
Original Author: Chakkree Tiyawongsuwan
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class Slab:
    id: str
    name: str = ""
    slab_type: str = "PS"  # 'PS' (Precast plank slab) or 'RC' (Cast-in-place)
    boundary: List[Tuple[float, float]] = field(default_factory=list)
    thickness: float = 0.10  # 10cm or 5cm plank + 5cm topping
    elevation: float = 0.0  # Top of finish level
    topping_thickness: float = 0.05  # for PS slab
    wire_mesh: str = "WM4@0.20"
    rebar_spec: str = "RB9@0.15"

    @property
    def area(self) -> float:
        """Calculates 2D planar polygon area using Shoelace formula."""
        n = len(self.boundary)
        if n < 3:
            return 0.0
        a = 0.0
        for i in range(n):
            j = (i + 1) % n
            a += self.boundary[i][0] * self.boundary[j][1]
            a -= self.boundary[j][0] * self.boundary[i][1]
        return abs(a) / 2.0

    @property
    def concrete_volume(self) -> float:
        """Volume of concrete (topping only for PS, full for RC) in m3."""
        eff_thick = self.topping_thickness if self.slab_type.upper() == "PS" else self.thickness
        return self.area * eff_thick

    @property
    def formwork_area(self) -> float:
        """Formwork area in m2 (0 for PS on beams, full soffit for RC)."""
        return 0.0 if self.slab_type.upper() == "PS" else self.area

    def to_debim_dict(self, storey_id: str = "ST_01") -> Dict[str, Any]:
        """Converts to debim declarative manifest element."""
        return {
            "id": self.id,
            "class": "IfcSlab",
            "storey": storey_id,
            "tag": "S-SLAB",
            "slab_type": self.slab_type.upper(),
            "thickness": round(self.thickness, 3),
            "elevation": round(self.elevation, 3),
            "boundary": [[round(p[0], 3), round(p[1], 3)] for p in self.boundary],
            "reinforcement": {
                "mesh": self.wire_mesh if self.slab_type.upper() == "PS" else self.rebar_spec,
            },
            "qto": {
                "area_m2": round(self.area, 3),
                "concrete_m3": round(self.concrete_volume, 3),
                "formwork_m2": round(self.formwork_area, 3),
            },
        }
