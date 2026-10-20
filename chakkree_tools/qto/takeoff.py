"""
Automated Quantity Take-off (QTO) and Material Report Module.
Calculates concrete volume (m3), formwork area (m2), lean concrete (m3), sand bedding (m3),
excavation volume (m3), and rebar weight summary for structural RC models.

Original Spec: Chakkree Tools QTO Engine
Author: Chakkree Tools Port
"""

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union

from chakkree_tools.qto.bar_schedule import BarBendingSchedule, REBAR_WEIGHTS


def calculate_excavation_volume(footing: Any, working_space_offset: float = 0.30) -> float:
    """
    Calculates excavation volume (m3) for footing with working space offset and bedding depth.
    """
    w = getattr(footing, "width", 1.0) + 2.0 * working_space_offset
    l = getattr(footing, "length", 1.0) + 2.0 * working_space_offset

    elev = getattr(footing, "elevation", -0.70)
    thick = getattr(footing, "thickness", 0.35)

    # Bedding extra depth: 0.05m lean concrete + 0.10m sand bedding
    bedding_depth = 0.15

    if elev < 0:
        depth = abs(elev) + thick + bedding_depth
    else:
        depth = thick + bedding_depth

    return round(w * l * depth, 3)


class MaterialTakeoff:
    """
    Material Take-off (QTO) Report and Quantity Aggregator.
    """

    def __init__(self, title: str = "Material Take-off Report", elements: Optional[List[Any]] = None):
        self.title = title
        self.elements: List[Any] = []
        if elements:
            self.add_elements(elements)

    def add_element(self, element: Any) -> None:
        self.elements.append(element)

    def add_elements(self, elements: List[Any]) -> None:
        self.elements.extend(elements)

    def get_summary(self) -> Dict[str, Any]:
        """
        Computes total quantities broken down by structural category and material.
        """
        summary_by_category: Dict[str, Dict[str, float]] = {
            "Footings": {"count": 0, "concrete_m3": 0.0, "formwork_m2": 0.0},
            "Columns": {"count": 0, "concrete_m3": 0.0, "formwork_m2": 0.0},
            "Beams": {"count": 0, "concrete_m3": 0.0, "formwork_m2": 0.0},
            "Slabs": {"count": 0, "concrete_m3": 0.0, "formwork_m2": 0.0},
        }

        total_lean_concrete_m3 = 0.0
        total_sand_bedding_m3 = 0.0
        total_excavation_m3 = 0.0

        for elem in self.elements:
            elem_class = elem.__class__.__name__

            c_vol = getattr(elem, "concrete_volume", 0.0)
            f_area = getattr(elem, "formwork_area", 0.0)

            if elem_class == "Footing":
                cat = "Footings"
                total_lean_concrete_m3 += getattr(elem, "lean_concrete_volume", 0.0)
                total_sand_bedding_m3 += getattr(elem, "sand_bedding_volume", 0.0)
                total_excavation_m3 += calculate_excavation_volume(elem)
            elif elem_class == "Column":
                cat = "Columns"
            elif elem_class == "Beam":
                cat = "Beams"
            elif elem_class == "Slab":
                cat = "Slabs"
            else:
                cat = "Other"
                if cat not in summary_by_category:
                    summary_by_category[cat] = {"count": 0, "concrete_m3": 0.0, "formwork_m2": 0.0}

            summary_by_category[cat]["count"] += 1
            summary_by_category[cat]["concrete_m3"] = round(
                summary_by_category[cat]["concrete_m3"] + c_vol, 3
            )
            summary_by_category[cat]["formwork_m2"] = round(
                summary_by_category[cat]["formwork_m2"] + f_area, 3
            )

        # Bar bending schedule for steel weights
        bbs = BarBendingSchedule.from_elements(self.elements)
        rebar_summary = bbs.get_summary_by_bar_type()

        total_concrete_m3 = round(
            sum(data["concrete_m3"] for data in summary_by_category.values()), 3
        )
        total_formwork_m2 = round(
            sum(data["formwork_m2"] for data in summary_by_category.values()), 3
        )

        return {
            "title": self.title,
            "total_elements": len(self.elements),
            "total_concrete_m3": total_concrete_m3,
            "total_formwork_m2": total_formwork_m2,
            "total_lean_concrete_m3": round(total_lean_concrete_m3, 3),
            "total_sand_bedding_m3": round(total_sand_bedding_m3, 3),
            "total_excavation_m3": round(total_excavation_m3, 3),
            "total_rebar_weight_kg": bbs.total_weight_kg,
            "category_summary": summary_by_category,
            "rebar_summary": rebar_summary,
        }

    def to_dict(self) -> Dict[str, Any]:
        return self.get_summary()

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    def to_markdown(self) -> str:
        """Exports Material Take-off report to Markdown table string."""
        summary = self.get_summary()

        lines = [
            f"# {self.title}",
            "",
            "## Executive Quantity Summary",
            "",
            "| Material / Item | Total Quantity | Unit |",
            "| :--- | :---: | :---: |",
            f"| Concrete Volume | {summary['total_concrete_m3']:,.3f} | m³ |",
            f"| Formwork Area | {summary['total_formwork_m2']:,.2f} | m² |",
            f"| Lean Concrete (5cm) | {summary['total_lean_concrete_m3']:,.3f} | m³ |",
            f"| Compacted Sand Bedding | {summary['total_sand_bedding_m3']:,.3f} | m³ |",
            f"| Foundation Excavation | {summary['total_excavation_m3']:,.3f} | m³ |",
            f"| Total Steel Reinforcement | {summary['total_rebar_weight_kg']:,.2f} | kg |",
            "",
            "## Breakdown by Structural Element Category",
            "",
            "| Category | Element Count | Concrete (m³) | Formwork (m²) |",
            "| :--- | :---: | :---: | :---: |",
        ]

        for cat, data in summary["category_summary"].items():
            if data["count"] > 0:
                lines.append(
                    f"| {cat} | {data['count']:,} | {data['concrete_m3']:,.3f} | {data['formwork_m2']:,.2f} |"
                )

        lines.extend([
            "",
            "## Steel Reinforcement Weight Breakdown",
            "",
            "| Bar Mark | Unit Weight (kg/m) | Length (m) | Total Weight (kg) |",
            "| :--- | :---: | :---: | :---: |",
        ])

        for mark in sorted(REBAR_WEIGHTS.keys()):
            r_data = summary["rebar_summary"].get(mark, {"total_length_m": 0.0, "total_weight_kg": 0.0})
            if r_data["total_length_m"] > 0 or r_data["total_weight_kg"] > 0:
                uw = REBAR_WEIGHTS[mark]
                lines.append(
                    f"| {mark} | {uw:.3f} | {r_data['total_length_m']:,.2f} | {r_data['total_weight_kg']:,.2f} |"
                )

        return "\n".join(lines)

    def to_csv(self) -> str:
        """Exports Material Take-off summary to CSV string."""
        summary = self.get_summary()

        lines = [
            "Category,Item,Quantity,Unit",
            f'Executive,Concrete Volume,{summary["total_concrete_m3"]:.3f},m3',
            f'Executive,Formwork Area,{summary["total_formwork_m2"]:.3f},m2',
            f'Executive,Lean Concrete,{summary["total_lean_concrete_m3"]:.3f},m3',
            f'Executive,Sand Bedding,{summary["total_sand_bedding_m3"]:.3f},m3',
            f'Executive,Excavation Volume,{summary["total_excavation_m3"]:.3f},m3',
            f'Executive,Total Rebar Weight,{summary["total_rebar_weight_kg"]:.3f},kg',
        ]

        for cat, data in summary["category_summary"].items():
            if data["count"] > 0:
                lines.append(f'ElementCategory,"{cat} Count",{data["count"]},pcs')
                lines.append(f'ElementCategory,"{cat} Concrete",{data["concrete_m3"]:.3f},m3')
                lines.append(f'ElementCategory,"{cat} Formwork",{data["formwork_m2"]:.3f},m2')

        for mark, r_data in summary["rebar_summary"].items():
            if r_data["total_weight_kg"] > 0:
                lines.append(f'RebarWeight,"{mark} Weight",{r_data["total_weight_kg"]:.3f},kg')

        return "\n".join(lines)


def export_takeoff_to_markdown(takeoff: MaterialTakeoff) -> str:
    return takeoff.to_markdown()


def export_takeoff_to_csv(takeoff: MaterialTakeoff) -> str:
    return takeoff.to_csv()


def export_takeoff_to_json(takeoff: MaterialTakeoff) -> str:
    return takeoff.to_json()

@dataclass
class QTOSummaryResult:
    total_elements: int
    total_concrete_volume_m3: float
    total_formwork_area_m2: float
    total_lean_concrete_m3: float
    total_sand_bedding_m3: float
    total_excavation_m3: float
    total_rebar_weight_kg: float
    rebar_weight_by_size: Dict[str, float]
    category_summary: Dict[str, Dict[str, float]]


def generate_qto_summary(elements: List[Any]) -> QTOSummaryResult:
    takeoff = MaterialTakeoff(elements=elements)
    s = takeoff.get_summary()
    rebar_map = {k: v.get('total_weight_kg', 0.0) for k, v in s.get('rebar_summary', {}).items() if v.get('total_weight_kg', 0.0) > 0}
    return QTOSummaryResult(
        total_elements=s.get('total_elements', 0),
        total_concrete_volume_m3=s.get('total_concrete_m3', 0.0),
        total_formwork_area_m2=s.get('total_formwork_m2', 0.0),
        total_lean_concrete_m3=s.get('total_lean_concrete_m3', 0.0),
        total_sand_bedding_m3=s.get('total_sand_bedding_m3', 0.0),
        total_excavation_m3=s.get('total_excavation_m3', 0.0),
        total_rebar_weight_kg=s.get('total_rebar_weight_kg', 0.0),
        rebar_weight_by_size=rebar_map,
        category_summary=s.get('category_summary', {}),
    )
