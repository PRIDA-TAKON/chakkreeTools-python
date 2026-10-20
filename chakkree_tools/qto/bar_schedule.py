"""
Automated Bar Bending Schedule (BBS) and Rebar Take-off Module.
Calculates cut lengths, hook allowances, and steel weights (kg) for RB6, RB9, DB12, DB16, DB20, DB25, DB28, DB32.

Original Spec & Standard: วสท. / EIT / TIS Standards (มอก.)
Author: Chakkree Tools Port
"""

import io
import json
import math
import re
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union

# Standard Rebar Nominal Unit Weights (kg/m) according to TIS / EIT (มอก. / วสท.)
REBAR_WEIGHTS: Dict[str, float] = {
    "RB6": 0.222,
    "RB9": 0.499,
    "DB12": 0.888,
    "DB16": 1.578,
    "DB20": 2.466,
    "DB25": 3.853,
    "DB28": 4.834,
    "DB32": 6.313,
}

# Diameter in meters mapping
REBAR_DIAMETERS: Dict[str, float] = {
    "RB6": 0.006,
    "RB9": 0.009,
    "DB12": 0.012,
    "DB16": 0.016,
    "DB20": 0.020,
    "DB25": 0.025,
    "DB28": 0.028,
    "DB32": 0.032,
}


def normalize_bar_mark(mark: Union[str, float, int]) -> str:
    """Normalizes rebar mark string (e.g. 'db12', 12, 0.012 -> 'DB12')."""
    if isinstance(mark, (int, float)):
        # Convert float meters or mm to string
        mm = int(round(mark * 1000)) if mark < 0.1 else int(round(mark))
        prefix = "RB" if mm < 10 else "DB"
        return f"{prefix}{mm}"

    mark_str = str(mark).strip().upper()
    if mark_str in REBAR_WEIGHTS:
        return mark_str

    # Extract digits
    match = re.search(r"([A-Z]*)\s*(\d+)", mark_str)
    if match:
        prefix = match.group(1) or ("RB" if int(match.group(2)) < 10 else "DB")
        dia = int(match.group(2))
        return f"{prefix}{dia}"

    return mark_str


def get_unit_weight(bar_mark: Union[str, float, int]) -> float:
    """Returns rebar nominal unit weight in kg/m."""
    norm_mark = normalize_bar_mark(bar_mark)
    if norm_mark in REBAR_WEIGHTS:
        return REBAR_WEIGHTS[norm_mark]

    # Theoretical weight formula: W = (d_mm^2) / 162
    dia_m = get_bar_diameter(bar_mark)
    dia_mm = dia_m * 1000.0
    return round((dia_mm**2) / 162.0, 3)


def get_bar_diameter(bar_mark: Union[str, float, int]) -> float:
    """Returns rebar diameter in meters."""
    if isinstance(bar_mark, (int, float)):
        return bar_mark if bar_mark < 0.1 else bar_mark / 1000.0

    norm_mark = normalize_bar_mark(bar_mark)
    if norm_mark in REBAR_DIAMETERS:
        return REBAR_DIAMETERS[norm_mark]

    match = re.search(r"\d+", str(bar_mark))
    if match:
        return float(match.group(0)) / 1000.0

    return 0.012  # Default DB12


def calculate_hook_allowance(hook_type: str, diameter_m: float) -> float:
    """
    Calculates standard hook allowance (in meters) for rebar shapes according to
    ว.ส.ท. (EIT Standard 1007-34).
    - 90 deg hook: max(12 * db, 0.065m)
    - 135 deg stirrup hook: max(6 * db, 0.075m)
    - 180 deg standard hook: max(16 * db, 0.065m)
    """
    ht = str(hook_type).strip().lower()
    if "135" in ht:
        return max(6.0 * diameter_m, 0.075)
    elif "180" in ht:
        return max(16.0 * diameter_m, 0.065)
    else:  # Default 90 degree
        return max(12.0 * diameter_m, 0.065)


def calculate_cut_length(
    shape_code: str,
    dimensions: Dict[str, float],
    diameter_m: float = 0.012,
) -> float:
    """
    Calculates cut length in meters for standard rebar shape codes per EIT 1007-34:
    - Shape 00: Straight bar
    - Shape 21: U-bent bar (length + hook_start + hook_end)
    - Shape 41 / 51: Rectangular closed stirrup (2*(width+depth) + 2*hook_length)
    - Shape 99: Column vertical with dowel bend (height + dowel_length)
    """
    code = str(shape_code).strip().zfill(2)

    if code == "00":
        base_len = dimensions.get("length", 0.0)
        h_start = dimensions.get("hook_start", 0.0)
        h_end = dimensions.get("hook_end", 0.0)
        return round(base_len + h_start + h_end, 3)

    elif code == "21":
        base_len = dimensions.get("length", 0.0)
        h_start = dimensions.get("hook_start", calculate_hook_allowance("90", diameter_m))
        h_end = dimensions.get("hook_end", calculate_hook_allowance("90", diameter_m))
        return round(base_len + h_start + h_end, 3)

    elif code in ("41", "51"):
        w = dimensions.get("width", 0.0)
        d = dimensions.get("depth", 0.0)
        h_len = dimensions.get("hook_length", calculate_hook_allowance("135", diameter_m))
        return round(2.0 * (w + d) + 2.0 * h_len, 3)

    elif code == "99":
        h = dimensions.get("height", 0.0)
        dowel = dimensions.get("dowel_length", 0.30)
        h_top = dimensions.get("hook_top", 0.0)
        return round(h + dowel + h_top, 3)

    else:
        # Generic length sum if unknown shape
        return round(sum(dimensions.values()), 3)


def parse_rebar_spec(spec_str: str) -> Dict[str, Any]:
    """
    Parses rebar specification strings (e.g. '2DB12', 'RB6@0.175', 'RB6@0.10/0.20', '4DB16', 'WM4@0.20').
    Returns dict with count/spacing (or spacing_end/spacing_mid), bar_mark, diameter_m.
    """
    spec = str(spec_str).strip().upper()

    # Pattern for count and mark: e.g. "2DB12", "8DB16"
    m_count = re.match(r"^(\d+)\s*([A-Z]+\d+)$", spec)
    if m_count:
        cnt = int(m_count.group(1))
        mark = normalize_bar_mark(m_count.group(2))
        return {"count": cnt, "bar_mark": mark, "diameter_m": get_bar_diameter(mark)}

    # Pattern for two-zone spacing: e.g. "RB6@0.10/0.20" or "RB6@0.10,0.20"
    m_two_zone = re.match(r"^([A-Z]+\d+)\s*@\s*([\d\.]+)\s*[\/,]\s*([\d\.]+)$", spec)
    if m_two_zone:
        mark = normalize_bar_mark(m_two_zone.group(1))
        s_end = float(m_two_zone.group(2))
        s_mid = float(m_two_zone.group(3))
        return {
            "spacing": s_mid,
            "spacing_end": s_end,
            "spacing_mid": s_mid,
            "bar_mark": mark,
            "diameter_m": get_bar_diameter(mark),
        }

    # Pattern for mark and single spacing: e.g. "RB6@0.175", "RB9@0.15"
    m_spacing = re.match(r"^([A-Z]+\d+)\s*@\s*([\d\.]+)$", spec)
    if m_spacing:
        mark = normalize_bar_mark(m_spacing.group(1))
        spacing = float(m_spacing.group(2))
        return {"spacing": spacing, "bar_mark": mark, "diameter_m": get_bar_diameter(mark)}

    # Fallback default
    mark = normalize_bar_mark(spec)
    return {"count": 1, "bar_mark": mark, "diameter_m": get_bar_diameter(mark)}


@dataclass
class RebarItem:
    member_id: str
    member_name: str = ""
    bar_mark: str = "DB12"
    shape_code: str = "00"
    num_members: int = 1
    bars_per_member: int = 1
    cut_length: float = 0.0  # meters
    description: str = ""

    def __post_init__(self):
        self.bar_mark = normalize_bar_mark(self.bar_mark)

    @property
    def total_count(self) -> int:
        return self.num_members * self.bars_per_member

    @property
    def total_length(self) -> float:
        return round(self.total_count * self.cut_length, 3)

    @property
    def unit_weight(self) -> float:
        return get_unit_weight(self.bar_mark)

    @property
    def total_weight(self) -> float:
        return round(self.total_length * self.unit_weight, 3)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "member_id": self.member_id,
            "member_name": self.member_name,
            "bar_mark": self.bar_mark,
            "shape_code": self.shape_code,
            "num_members": self.num_members,
            "bars_per_member": self.bars_per_member,
            "total_count": self.total_count,
            "cut_length_m": round(self.cut_length, 3),
            "total_length_m": self.total_length,
            "unit_weight_kg_m": self.unit_weight,
            "total_weight_kg": self.total_weight,
            "description": self.description,
        }


class BarBendingSchedule:
    """
    Bar Bending Schedule (BBS) container and aggregation class.
    """

    def __init__(self, title: str = "Bar Bending Schedule"):
        self.title = title
        self.items: List[RebarItem] = []

    def add_item(self, item: RebarItem) -> None:
        self.items.append(item)

    def add_items(self, items: List[RebarItem]) -> None:
        self.items.extend(items)

    @classmethod
    def from_elements(cls, elements: List[Any], title: str = "Bar Bending Schedule") -> "BarBendingSchedule":
        """
        Generates a BarBendingSchedule directly from a list of structural RC objects
        (Footing, Column, Beam, Slab).
        """
        bbs = cls(title=title)

        for elem in elements:
            elem_class = elem.__class__.__name__

            if elem_class == "Footing":
                f_id = elem.id
                f_name = elem.name or f"Footing {f_id}"
                cov = getattr(elem, "covering", 0.07)
                hook_len = max(elem.thickness - 2.0 * cov, 0.15)

                # X rebar
                cut_x = calculate_cut_length(
                    "21",
                    {"length": elem.width - 2.0 * cov, "hook_start": hook_len, "hook_end": hook_len},
                    elem.rebar_x_dia,
                )
                bbs.add_item(
                    RebarItem(
                        member_id=f_id,
                        member_name=f_name,
                        bar_mark=normalize_bar_mark(elem.rebar_x_dia),
                        shape_code="21",
                        num_members=1,
                        bars_per_member=elem.rebar_x_count,
                        cut_length=cut_x,
                        description="Bottom Rebar X-Dir",
                    )
                )

                # Y rebar
                cut_y = calculate_cut_length(
                    "21",
                    {"length": elem.length - 2.0 * cov, "hook_start": hook_len, "hook_end": hook_len},
                    elem.rebar_y_dia,
                )
                bbs.add_item(
                    RebarItem(
                        member_id=f_id,
                        member_name=f_name,
                        bar_mark=normalize_bar_mark(elem.rebar_y_dia),
                        shape_code="21",
                        num_members=1,
                        bars_per_member=elem.rebar_y_count,
                        cut_length=cut_y,
                        description="Bottom Rebar Y-Dir",
                    )
                )

            elif elem_class == "Column":
                c_id = elem.id
                c_name = elem.name or f"Column {c_id}"
                cov = getattr(elem, "covering", 0.03)

                # Main vertical bars
                cut_main = calculate_cut_length(
                    "99",
                    {
                        "height": elem.height + getattr(elem, "ext_top", 0.0),
                        "dowel_length": getattr(elem, "ext_bottom", 0.30),
                    },
                    elem.main_bar_dia,
                )
                bbs.add_item(
                    RebarItem(
                        member_id=c_id,
                        member_name=c_name,
                        bar_mark=normalize_bar_mark(elem.main_bar_dia),
                        shape_code="99",
                        num_members=1,
                        bars_per_member=elem.main_bar_count,
                        cut_length=cut_main,
                        description="Main Longitudinal Bars",
                    )
                )

                # Stirrups
                n_stirrups = int(math.ceil(elem.height / elem.stirrup_spacing)) + 1
                stirrup_w = max(elem.width - 2.0 * cov, 0.05)
                stirrup_d = max(elem.depth - 2.0 * cov, 0.05)
                cut_stirrup = calculate_cut_length(
                    "41",
                    {"width": stirrup_w, "depth": stirrup_d},
                    elem.stirrup_dia,
                )
                bbs.add_item(
                    RebarItem(
                        member_id=c_id,
                        member_name=c_name,
                        bar_mark=normalize_bar_mark(elem.stirrup_dia),
                        shape_code="41",
                        num_members=1,
                        bars_per_member=n_stirrups,
                        cut_length=cut_stirrup,
                        description=f"Column Stirrups @ {elem.stirrup_spacing*1000:.0f}mm",
                    )
                )

            elif elem_class == "Beam":
                b_id = elem.id
                b_name = elem.name or f"Beam {b_id}"
                cov = getattr(elem, "covering", 0.025)
                span = elem.length
                hook_h = max(elem.depth - 2.0 * cov, 0.15)

                # Top bars
                top_spec = parse_rebar_spec(elem.top_bar_spec)
                cut_top = calculate_cut_length(
                    "21",
                    {"length": span, "hook_start": hook_h, "hook_end": hook_h},
                    top_spec["diameter_m"],
                )
                bbs.add_item(
                    RebarItem(
                        member_id=b_id,
                        member_name=b_name,
                        bar_mark=top_spec["bar_mark"],
                        shape_code="21",
                        num_members=1,
                        bars_per_member=top_spec.get("count", 2),
                        cut_length=cut_top,
                        description="Top Longitudinal Bars",
                    )
                )

                # Bottom bars
                bot_spec = parse_rebar_spec(elem.bot_bar_spec)
                cut_bot = calculate_cut_length(
                    "21",
                    {"length": span, "hook_start": hook_h, "hook_end": hook_h},
                    bot_spec["diameter_m"],
                )
                bbs.add_item(
                    RebarItem(
                        member_id=b_id,
                        member_name=b_name,
                        bar_mark=bot_spec["bar_mark"],
                        shape_code="21",
                        num_members=1,
                        bars_per_member=bot_spec.get("count", 2),
                        cut_length=cut_bot,
                        description="Bottom Longitudinal Bars",
                    )
                )

                # Stirrups
                st_spec = parse_rebar_spec(elem.stirrup_spec)
                s_end = getattr(elem, "stirrup_spacing_end", None) or st_spec.get("spacing_end")
                s_mid = getattr(elem, "stirrup_spacing_mid", None) or st_spec.get("spacing_mid")

                stirrup_w = max(elem.width - 2.0 * cov, 0.05)
                stirrup_d = max(elem.depth - 2.0 * cov, 0.05)
                cut_stirrup = calculate_cut_length(
                    "41",
                    {"width": stirrup_w, "depth": stirrup_d},
                    st_spec["diameter_m"],
                )

                if s_end and s_mid and s_end > 0 and s_mid > 0:
                    from chakkree_tools.rc.stirrup_pattern import StirrupPattern
                    sp = StirrupPattern(
                        diameter=st_spec["diameter_m"],
                        width=stirrup_w,
                        depth=stirrup_d,
                        length=span,
                        n_spacing=[[1, s_end], [1, s_mid], [1, s_end]],
                    )
                    sp.adjust_offset_for_length(span, offset=(0.05, 0.05), sub_length=(span / 4.0, span / 4.0))
                    n_stirrups = sp.count_stirrups()
                    desc = f"Beam Stirrups (2-Zone L/4) @ {s_end*1000:.0f}mm / {s_mid*1000:.0f}mm"
                else:
                    spacing = st_spec.get("spacing", 0.15)
                    n_stirrups = int(math.ceil(span / spacing)) + 1
                    desc = f"Beam Stirrups @ {spacing*1000:.0f}mm"

                bbs.add_item(
                    RebarItem(
                        member_id=b_id,
                        member_name=b_name,
                        bar_mark=st_spec["bar_mark"],
                        shape_code="41",
                        num_members=1,
                        bars_per_member=n_stirrups,
                        cut_length=cut_stirrup,
                        description=desc,
                    )
                )

            elif elem_class == "Slab":
                s_id = elem.id
                s_name = elem.name or f"Slab {s_id}"
                spec = parse_rebar_spec(getattr(elem, "rebar_spec", "RB9@0.15"))
                area = elem.area
                side = math.sqrt(area) if area > 0 else 1.0
                spacing = spec.get("spacing", 0.15)
                n_bars = int(math.ceil(side / spacing)) * 2  # Both directions
                cut_s = calculate_cut_length("00", {"length": side}, spec["diameter_m"])
                bbs.add_item(
                    RebarItem(
                        member_id=s_id,
                        member_name=s_name,
                        bar_mark=spec["bar_mark"],
                        shape_code="00",
                        num_members=1,
                        bars_per_member=n_bars,
                        cut_length=cut_s,
                        description="Slab Reinforcement Grid",
                    )
                )

        return bbs

    def get_summary_by_bar_type(self) -> Dict[str, Dict[str, float]]:
        """
        Aggregates length (m) and weight (kg) by rebar designation (RB6, RB9, DB12, ...).
        """
        summary: Dict[str, Dict[str, float]] = {
            mark: {"total_length_m": 0.0, "total_weight_kg": 0.0, "count": 0}
            for mark in REBAR_WEIGHTS
        }

        for item in self.items:
            mark = item.bar_mark
            if mark not in summary:
                summary[mark] = {"total_length_m": 0.0, "total_weight_kg": 0.0, "count": 0}

            summary[mark]["total_length_m"] = round(
                summary[mark]["total_length_m"] + item.total_length, 3
            )
            summary[mark]["total_weight_kg"] = round(
                summary[mark]["total_weight_kg"] + item.total_weight, 3
            )
            summary[mark]["count"] += item.total_count

        return summary

    @property
    def total_weight_kg(self) -> float:
        """Grand total steel weight in kg."""
        return round(sum(item.total_weight for item in self.items), 3)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "total_weight_kg": self.total_weight_kg,
            "summary_by_bar_type": self.get_summary_by_bar_type(),
            "items": [item.to_dict() for item in self.items],
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    def to_markdown(self) -> str:
        """Exports Bar Bending Schedule to Markdown report string."""
        lines = [
            f"# {self.title}",
            "",
            f"**Grand Total Steel Weight:** {self.total_weight_kg:,.2f} kg",
            "",
            "## Summary by Rebar Diameter",
            "",
            "| Bar Mark | Unit Weight (kg/m) | Total Count | Total Length (m) | Total Weight (kg) |",
            "| :--- | :---: | :---: | :---: | :---: |",
        ]

        summary = self.get_summary_by_bar_type()
        for mark in sorted(summary.keys()):
            data = summary[mark]
            if data["count"] > 0 or data["total_length_m"] > 0:
                uw = get_unit_weight(mark)
                lines.append(
                    f"| {mark} | {uw:.3f} | {data['count']:,} | {data['total_length_m']:,.2f} | {data['total_weight_kg']:,.2f} |"
                )

        lines.extend([
            "",
            "## Rebar Cut Schedule Details",
            "",
            "| Member ID | Name | Bar Mark | Shape | Members | Qty/Mem | Cut Len (m) | Total Len (m) | Total Wt (kg) | Description |",
            "| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |",
        ])

        for item in self.items:
            lines.append(
                f"| {item.member_id} | {item.member_name} | {item.bar_mark} | Shape {item.shape_code} | "
                f"{item.num_members} | {item.bars_per_member} | {item.cut_length:.3f} | "
                f"{item.total_length:.2f} | {item.total_weight:.2f} | {item.description} |"
            )

        return "\n".join(lines)

    def to_csv(self) -> str:
        """Exports Bar Bending Schedule to CSV table string."""
        lines = [
            "Member ID,Member Name,Bar Mark,Shape Code,Num Members,Bars Per Member,Total Count,Cut Length (m),Total Length (m),Unit Weight (kg/m),Total Weight (kg),Description"
        ]
        for item in self.items:
            desc = item.description.replace('"', '""')
            m_id = item.member_id.replace('"', '""')
            m_name = item.member_name.replace('"', '""')
            lines.append(
                f'"{m_id}","{m_name}","{item.bar_mark}","{item.shape_code}",'
                f'{item.num_members},{item.bars_per_member},{item.total_count},'
                f'{item.cut_length:.3f},{item.total_length:.3f},{item.unit_weight:.3f},{item.total_weight:.3f},"{desc}"'
            )
        return "\n".join(lines)

    def to_excel_bytes(self) -> bytes:
        """
        Exports Bar Bending Schedule directly to Excel (.xlsx) file bytes using
        a standard OpenXML zip packager (no external dependencies required).
        """
        rows = [
            ["Member ID", "Member Name", "Bar Mark", "Shape Code", "Num Members", "Bars Per Member", "Total Count", "Cut Length (m)", "Total Length (m)", "Unit Weight (kg/m)", "Total Weight (kg)", "Description"]
        ]
        for item in self.items:
            rows.append([
                item.member_id,
                item.member_name,
                item.bar_mark,
                item.shape_code,
                item.num_members,
                item.bars_per_member,
                item.total_count,
                round(item.cut_length, 3),
                round(item.total_length, 3),
                round(item.unit_weight, 3),
                round(item.total_weight, 3),
                item.description,
            ])

        # Create OpenXML structure
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            # [Content_Types].xml
            zf.writestr(
                "[Content_Types].xml",
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                '<Default Extension="xml" ContentType="application/xml"/>'
                '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
                '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
                '</Types>',
            )

            # _rels/.rels
            zf.writestr(
                "_rels/.rels",
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
                '</Relationships>',
            )

            # xl/_rels/workbook.xml.rels
            zf.writestr(
                "xl/_rels/workbook.xml.rels",
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
                '</Relationships>',
            )

            # xl/workbook.xml
            zf.writestr(
                "xl/workbook.xml",
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
                '<sheets><sheet name="Bar Cut Schedule" sheetId="1" r:id="rId1"/></sheets>'
                '</workbook>',
            )

            # xl/worksheets/sheet1.xml
            sheet_rows = []
            for r_idx, row in enumerate(rows, 1):
                cells = []
                for c_idx, val in enumerate(row, 1):
                    col_letter = chr(64 + c_idx)
                    cell_ref = f"{col_letter}{r_idx}"
                    if isinstance(val, (int, float)):
                        cells.append(f'<c r="{cell_ref}"><v>{val}</v></c>')
                    else:
                        val_str = str(val).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
                        cells.append(f'<c r="{cell_ref}" t="inlineStr"><is><t>{val_str}</t></is></c>')
                sheet_rows.append(f'<row r="{r_idx}">{"".join(cells)}</row>')

            sheet_xml = (
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                f'<sheetData>{"".join(sheet_rows)}</sheetData>'
                '</worksheet>'
            )
            zf.writestr("xl/worksheets/sheet1.xml", sheet_xml)

        return buffer.getvalue()

    def export_excel(self, filepath: str) -> None:
        """Saves Bar Bending Schedule to an Excel file (.xlsx)."""
        content = self.to_excel_bytes()
        with open(filepath, "wb") as f:
            f.write(content)


def export_bbs_to_markdown(schedule: BarBendingSchedule) -> str:
    return schedule.to_markdown()


def export_bbs_to_csv(schedule: BarBendingSchedule) -> str:
    return schedule.to_csv()


def export_bbs_to_excel(schedule: BarBendingSchedule, filepath: str) -> None:
    schedule.export_excel(filepath)


def export_bbs_to_json(schedule: BarBendingSchedule) -> str:
    return schedule.to_json()
