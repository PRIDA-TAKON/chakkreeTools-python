"""
Stirrup Pattern & Multi-Zone Spacing Calculator
Direct Python port of Chakkree_tools::Structure::RC::Reinforcement::RebarPattern::StirrupPattern
Original Author: Chakkree Tiyawongsuwan (30 Oct 2568 / 2025)
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class StirrupPlacement:
    position_along_axis: float  # distance in meters from start
    width: float  # cross-section width in meters
    depth: float  # cross-section depth in meters
    diameter: float  # bar diameter in meters
    hook_type: str = "135"  # '90' or '135'


class StirrupPattern:
    """
    Parametric Stirrup generator supporting multi-zone spacing (1-zone or 3-zone),
    variable spacing distributions, and standard seismic/structural hook bents.
    All dimensions in SI units (Meters).
    """

    def __init__(
        self,
        diameter: float,
        width: float,
        depth: float,
        length: float = 4.0,
        pattern: str = "2",
        end_hook: str = "135",
        n_spacing: Optional[List[List[float]]] = None,
        factor_db: float = 4.0,
        factor_lh: float = 6.0,
    ):
        self.dia = diameter
        self.a = width
        self.b = depth
        self.length = length
        self.pattern = pattern
        self.end_hook = end_hook
        # n_spacing: list of [count, spacing, (optional offset)]
        self.n_spacing: List[List[float]] = n_spacing or [[1, 0.150]]
        self.factor_db = factor_db
        self.factor_lh = factor_lh

    def adjust_offset_for_length(
        self,
        length: float,
        offset: Tuple[float, float] = (0.05, 0.05),
        sub_length: Tuple[float, float] = (1.0, 1.0),
    ) -> None:
        """
        Calculates exact count and offsets for 1-zone or 3-zone beam/column stirrups.
        Matches Chakkree Tools original structural algorithm.
        """
        self.length = length
        if len(self.n_spacing) == 1:
            s = self.n_spacing[0][1]
            n = int(length / s) + 1
            if (n - 1) * s > length:
                n -= 1
            gap = (length - (n - 1) * s) / 2.0
            self.n_spacing[0] = [float(n), float(s), float(gap)]
        elif len(self.n_spacing) == 3:
            s1 = self.n_spacing[0][1]
            s2 = self.n_spacing[1][1]
            s3 = self.n_spacing[2][1]

            # Zone 1 (Left end)
            n1 = int((sub_length[0] - offset[0]) / s1) + 1
            if (offset[0] + (n1 - 1) * s1) > sub_length[0]:
                n1 -= 1
            x1 = offset[0] + (n1 - 1) * s1

            # Zone 3 (Right end)
            n3 = int((sub_length[1] - offset[1]) / s3) + 1
            if (offset[1] + (n3 - 1) * s3) > sub_length[1]:
                n3 -= 1
            x3 = length - offset[1] - (n3 - 1) * s3

            # Zone 2 (Middle)
            mid_length = x3 - x1
            n2 = int(mid_length / s2) + 1
            gap = (mid_length - (n2 - 1) * s2) / 2.0
            if gap <= s1:
                n2 -= 1
                gap = (mid_length - (n2 - 1) * s2) / 2.0

            self.n_spacing[0] = [float(n1), float(s1), float(offset[0])]
            self.n_spacing[1] = [float(n2), float(s2), float(gap)]
            self.n_spacing[2] = [float(n3), float(s3), float(gap)]

    def count_stirrups(self) -> int:
        return sum(int(zone[0]) for zone in self.n_spacing)

    def generate_positions(self) -> List[StirrupPlacement]:
        """Generates list of individual stirrups positioned along axis."""
        placements: List[StirrupPlacement] = []
        current_pos = 0.0

        for zone in self.n_spacing:
            count = int(zone[0])
            spacing = zone[1]
            offset = zone[2] if len(zone) > 2 else 0.0

            current_pos += offset
            for i in range(count):
                pos = current_pos + i * spacing
                placements.append(
                    StirrupPlacement(
                        position_along_axis=pos,
                        width=self.a,
                        depth=self.b,
                        diameter=self.dia,
                        hook_type=self.end_hook,
                    )
                )
            current_pos += (count - 1) * spacing if count > 0 else 0.0

        return placements

    def summary(self) -> Dict[str, Any]:
        """Returns summary dictionary matching Chakkree Tools original summary."""
        return {
            "pattern": self.pattern,
            "dia_mm": self.dia * 1000.0,
            "width_mm": self.a * 1000.0,
            "depth_mm": self.b * 1000.0,
            "length_m": self.length,
            "spacing": self.n_spacing,
            "total_count": self.count_stirrups(),
        }
