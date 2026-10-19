"""
Unit tests for Bar Bending Schedule (BBS) and Material Take-off (QTO)
"""

import json
import pytest

from chakkree_tools.qto import (
    REBAR_WEIGHTS,
    BarBendingSchedule,
    MaterialTakeoff,
    RebarItem,
    calculate_cut_length,
    calculate_excavation_volume,
    calculate_hook_allowance,
    export_bbs_to_csv,
    export_bbs_to_json,
    export_bbs_to_markdown,
    export_takeoff_to_csv,
    export_takeoff_to_json,
    export_takeoff_to_markdown,
    get_bar_diameter,
    get_unit_weight,
    normalize_bar_mark,
    parse_rebar_spec,
)
from chakkree_tools.rc import Beam, Column, Footing, PileCap, Slab


def test_rebar_unit_weights_all_diameters():
    expected_weights = {
        "RB6": 0.222,
        "RB9": 0.499,
        "DB12": 0.888,
        "DB16": 1.578,
        "DB20": 2.466,
        "DB25": 3.853,
        "DB28": 4.834,
        "DB32": 6.313,
    }

    for mark, expected_wt in expected_weights.items():
        assert get_unit_weight(mark) == expected_wt, f"Mismatch for {mark}"

    # Check numeric diameter inputs
    assert get_unit_weight(0.006) == 0.222
    assert get_unit_weight(0.012) == 0.888
    assert get_unit_weight(16) == 1.578
    assert get_unit_weight("db25") == 3.853


def test_normalize_bar_mark_and_diameters():
    assert normalize_bar_mark("db12") == "DB12"
    assert normalize_bar_mark("rb6") == "RB6"
    assert normalize_bar_mark(0.020) == "DB20"
    assert normalize_bar_mark(9) == "RB9"

    assert get_bar_diameter("RB6") == 0.006
    assert get_bar_diameter("DB12") == 0.012
    assert get_bar_diameter("DB28") == 0.028
    assert get_bar_diameter("DB32") == 0.032


def test_hook_allowances():
    # 90 deg hook: 12 * db
    h90 = calculate_hook_allowance("90", 0.012)
    assert round(h90, 3) == 0.144

    # 135 deg hook: max(6 * db, 0.075)
    h135_small = calculate_hook_allowance("135", 0.006)  # 6*0.006 = 0.036 < 0.075
    assert h135_small == 0.075

    h135_large = calculate_hook_allowance("135", 0.020)  # 6*0.020 = 0.120
    assert round(h135_large, 3) == 0.120

    # 180 deg hook: 16 * db
    h180 = calculate_hook_allowance("180", 0.016)
    assert round(h180, 3) == 0.256


def test_cut_length_shapes():
    # Shape 00: Straight bar
    cut00 = calculate_cut_length("00", {"length": 5.0})
    assert cut00 == 5.0

    # Shape 21: U-bent bar
    cut21 = calculate_cut_length("21", {"length": 4.0, "hook_start": 0.2, "hook_end": 0.2})
    assert cut21 == 4.4

    # Shape 41: Stirrup
    cut41 = calculate_cut_length("41", {"width": 0.15, "depth": 0.35, "hook_length": 0.075})
    assert cut41 == 1.15  # 2*(0.15+0.35) + 2*0.075 = 1.0 + 0.15 = 1.15

    # Shape 99: Column vertical with dowel
    cut99 = calculate_cut_length("99", {"height": 3.5, "dowel_length": 0.3})
    assert cut99 == 3.8


def test_parse_rebar_spec():
    spec1 = parse_rebar_spec("2DB12")
    assert spec1["count"] == 2
    assert spec1["bar_mark"] == "DB12"
    assert spec1["diameter_m"] == 0.012

    spec2 = parse_rebar_spec("RB6@0.175")
    assert spec2["spacing"] == 0.175
    assert spec2["bar_mark"] == "RB6"
    assert spec2["diameter_m"] == 0.006


def test_bar_bending_schedule_aggregation():
    bbs = BarBendingSchedule(title="Project Foundation BBS")

    item1 = RebarItem(
        member_id="F1",
        member_name="Footing F1",
        bar_mark="DB12",
        shape_code="21",
        num_members=4,
        bars_per_member=10,
        cut_length=1.50,
        description="Footing main rebar",
    )
    # Total count = 40, Total len = 60m, Total weight = 60 * 0.888 = 53.28 kg

    item2 = RebarItem(
        member_id="C1",
        member_name="Column C1",
        bar_mark="RB6",
        shape_code="41",
        num_members=4,
        bars_per_member=20,
        cut_length=1.00,
        description="Column stirrups",
    )
    # Total count = 80, Total len = 80m, Total weight = 80 * 0.222 = 17.76 kg

    bbs.add_items([item1, item2])

    assert bbs.total_weight_kg == round(53.28 + 17.76, 3)

    summary = bbs.get_summary_by_bar_type()
    assert summary["DB12"]["total_length_m"] == 60.0
    assert summary["DB12"]["total_weight_kg"] == 53.28
    assert summary["RB6"]["total_length_m"] == 80.0
    assert summary["RB6"]["total_weight_kg"] == 17.76


def test_bbs_from_rc_elements():
    f1 = Footing(id="F1", width=1.0, length=1.0, thickness=0.35, rebar_x_count=5, rebar_x_dia=0.012)
    c1 = Column(id="C1", width=0.3, depth=0.3, height=3.5, main_bar_count=8, main_bar_dia=0.016, stirrup_dia=0.009)
    b1 = Beam(id="B1", width=0.2, depth=0.4, start_point=(0, 0), end_point=(4, 0), top_bar_spec="2DB12", bot_bar_spec="3DB12", stirrup_spec="RB6@0.15")
    s1 = Slab(id="S1", boundary=[(0, 0), (4, 0), (4, 4), (0, 4)], rebar_spec="RB9@0.15")

    bbs = BarBendingSchedule.from_elements([f1, c1, b1, s1])
    assert len(bbs.items) > 0
    assert bbs.total_weight_kg > 0.0

    summary = bbs.get_summary_by_bar_type()
    # Ensure DB12, DB16, RB6, RB9, etc. are accounted for
    assert summary["DB16"]["total_weight_kg"] > 0
    assert summary["RB6"]["total_weight_kg"] > 0


def test_material_takeoff_and_excavation():
    f1 = PileCap.create_n_piles(id_str="F1", pile_count=2, pile_size=0.22, thickness=0.60)
    c1 = Column(id="C1", width=0.3, depth=0.3, height=3.5)
    b1 = Beam(id="B1", width=0.2, depth=0.4, start_point=(0, 0), end_point=(4, 0))
    s1 = Slab(id="S1", boundary=[(0, 0), (4, 0), (4, 4), (0, 4)], thickness=0.10)

    elements = [f1, c1, b1, s1]
    qto = MaterialTakeoff(title="Building Material Takeoff", elements=elements)
    summary = qto.get_summary()

    assert summary["total_elements"] == 4
    assert summary["total_concrete_m3"] > 0.0
    assert summary["total_formwork_m2"] > 0.0
    assert summary["total_lean_concrete_m3"] > 0.0
    assert summary["total_sand_bedding_m3"] > 0.0
    assert summary["total_excavation_m3"] > 0.0
    assert summary["total_rebar_weight_kg"] > 0.0

    # Test excavation volume formula directly
    exc_vol = calculate_excavation_volume(f1, working_space_offset=0.30)
    assert exc_vol > 0.0


def test_exports_markdown_csv_json():
    f1 = Footing(id="F1", width=1.2, length=1.2, thickness=0.40)
    c1 = Column(id="C1", width=0.3, depth=0.3, height=3.0)
    elements = [f1, c1]

    bbs = BarBendingSchedule.from_elements(elements)
    mto = MaterialTakeoff(elements=elements)

    # BBS Exports
    bbs_md = export_bbs_to_markdown(bbs)
    assert "# Bar Bending Schedule" in bbs_md
    assert "| Member ID | Name |" in bbs_md

    bbs_csv = export_bbs_to_csv(bbs)
    assert "Member ID,Member Name,Bar Mark" in bbs_csv

    bbs_json = export_bbs_to_json(bbs)
    json_data = json.loads(bbs_json)
    assert "total_weight_kg" in json_data

    # MTO Exports
    mto_md = export_takeoff_to_markdown(mto)
    assert "# Material Take-off Report" in mto_md
    assert "Executive Quantity Summary" in mto_md

    mto_csv = export_takeoff_to_csv(mto)
    assert "Category,Item,Quantity,Unit" in mto_csv

    mto_json = export_takeoff_to_json(mto)
    mto_json_data = json.loads(mto_json)
    assert "total_concrete_m3" in mto_json_data
