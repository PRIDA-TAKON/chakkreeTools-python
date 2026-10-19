"""
Parametric Footing and Pile Cap Models
Ported from Chakkree Tools (1Pile to 9Piles and Isolated Footings)
Original Author: Chakkree Tiyawongsuwan
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class PileSpec:
    count: int = 1
    pile_type: str = "I_PILE"  # 'I_PILE', 'SQUARE', 'BORED'
    size: float = 0.22  # meters (e.g. 220mm)
    length: float = 6.0  # meters
    spacing_factor: float = 3.0  # 3 * Dp
    edge_factor: float = 1.5  # 1.5 * Dp


@dataclass
class Footing:
    id: str
    name: str = ""
    width: float = 1.0  # B (m)
    length: float = 1.0  # L (m)
    thickness: float = 0.35  # t (m)
    elevation: float = -0.70  # Z top of footing
    covering: float = 0.07  # m
    pile_spec: Optional[PileSpec] = None

    # Rebars
    rebar_x_count: int = 5
    rebar_x_dia: float = 0.012  # DB12
    rebar_y_count: int = 5
    rebar_y_dia: float = 0.012  # DB12
    stirrup_count: int = 1
    stirrup_dia: float = 0.009  # RB9

    @property
    def concrete_volume(self) -> float:
        """Volume of concrete in cubic meters."""
        return self.width * self.length * self.thickness

    @property
    def formwork_area(self) -> float:
        """Area of side formwork in square meters."""
        return 2.0 * (self.width + self.length) * self.thickness

    @property
    def lean_concrete_volume(self) -> float:
        """Lean concrete (5cm thickness, 10cm offset) volume in m3."""
        w = self.width + 0.20
        l = self.length + 0.20
        return w * l * 0.05

    @property
    def sand_bedding_volume(self) -> float:
        """Compacted sand bedding (10cm thickness) volume in m3."""
        w = self.width + 0.20
        l = self.length + 0.20
        return w * l * 0.10

    def to_debim_dict(self, storey_id: str = "ST_01") -> Dict[str, Any]:
        """Converts to debim declarative manifest element."""
        res: Dict[str, Any] = {
            "id": self.id,
            "class": "IfcFooting",
            "storey": storey_id,
            "tag": "S-FOOTING",
            "footing_type": "PILE_CAP" if self.pile_spec else "ISOLATED",
            "dimensions": {
                "width": round(self.width, 3),
                "length": round(self.length, 3),
                "thickness": round(self.thickness, 3),
            },
            "placement": {
                "offset_z": round(self.elevation, 3),
            },
            "rebar": {
                "grid_x": f"{self.rebar_x_count}DB{int(self.rebar_x_dia * 1000)}",
                "grid_y": f"{self.rebar_y_count}DB{int(self.rebar_y_dia * 1000)}",
                "covering": round(self.covering, 3),
            },
            "qto": {
                "concrete_m3": round(self.concrete_volume, 3),
                "formwork_m2": round(self.formwork_area, 3),
                "lean_concrete_m3": round(self.lean_concrete_volume, 3),
                "sand_bedding_m3": round(self.sand_bedding_volume, 3),
            },
        }
        if self.pile_spec:
            res["pile_spec"] = {
                "count": self.pile_spec.count,
                "type": self.pile_spec.pile_type,
                "size_m": round(self.pile_spec.size, 3),
                "length_m": round(self.pile_spec.length, 3),
            }
        return res


class PileCap:
    """
    Factory for standard Chakkree Tools 1-9 Piles pile caps.
    Automatically calculates footing width, length, and depth based on pile spacing.
    """

    @staticmethod
    def create_n_piles(
        id_str: str,
        pile_count: int,
        pile_size: float = 0.22,
        thickness: float = 0.60,
        elevation: float = -0.70,
        covering: float = 0.07,
        rebar_dia: float = 0.016,
    ) -> Footing:
        ps = PileSpec(count=pile_count, size=pile_size)
        dp = pile_size
        spacing = ps.spacing_factor * dp
        edge = ps.edge_factor * dp

        if pile_count == 1:
            w = max(0.70, 3.0 * dp)
            l = w
            nx, ny = 4, 4
        elif pile_count == 2:
            w = 2.0 * edge
            l = spacing + 2.0 * edge
            nx, ny = 5, 5
        elif pile_count == 3:
            # Triangular cap
            w = spacing + 2.0 * edge
            l = spacing * 0.866 + 2.0 * edge
            nx, ny = 6, 6
        elif pile_count == 4:
            w = spacing + 2.0 * edge
            l = spacing + 2.0 * edge
            nx, ny = 6, 6
        elif pile_count == 5:
            w = 2.0 * spacing + 2.0 * edge
            l = 2.0 * spacing + 2.0 * edge
            nx, ny = 7, 7
        elif pile_count == 6:
            w = spacing + 2.0 * edge
            l = 2.0 * spacing + 2.0 * edge
            nx, ny = 7, 8
        elif pile_count == 9:
            w = 2.0 * spacing + 2.0 * edge
            l = 2.0 * spacing + 2.0 * edge
            nx, ny = 8, 8
        else:
            w = 1.0
            l = 1.0
            nx, ny = 5, 5

        return Footing(
            id=id_str,
            name=f"PileCap_{pile_count}Piles",
            width=w,
            length=l,
            thickness=thickness,
            elevation=elevation,
            covering=covering,
            pile_spec=ps,
            rebar_x_count=nx,
            rebar_x_dia=rebar_dia,
            rebar_y_count=ny,
            rebar_y_dia=rebar_dia,
        )
