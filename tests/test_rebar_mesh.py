"""
Unit tests for 3D Rebar Polyline, Diameter Color Mapping, and Tubular Mesh Face Generation
"""

import math
import pytest
from chakkree_tools.rc import (
    DEFAULT_REBAR_COLORS,
    get_rebar_color,
    generate_shape_00,
    generate_shape_21,
    generate_shape_41,
    generate_shape_99,
    generate_tubular_mesh,
    generate_column_rebar_cage,
    generate_beam_rebar_cage,
    generate_footing_rebar_cage,
    generate_rebar_cage,
    Column,
    Beam,
    Footing,
)
from chakkree_tools.ingetrazo_plugin.plugin import ChakkreeToolsPlugin
from chakkree_tools.exporter.debim_exporter import DebimExporter


def test_shape_00_straight_bar():
    polyline = generate_shape_00(length=4.0, origin=(1.0, 2.0, 3.0), direction=(1.0, 0.0, 0.0))
    assert len(polyline) == 2
    assert polyline[0] == (1.0, 2.0, 3.0)
    assert polyline[1] == (5.0, 2.0, 3.0)


def test_shape_21_u_bent_bar():
    polyline = generate_shape_21(
        length=3.0,
        hook_start=0.25,
        hook_end=0.25,
        origin=(0.0, 0.0, 0.0),
        direction=(1.0, 0.0, 0.0),
        hook_direction=(0.0, 0.0, 1.0),
    )
    assert len(polyline) == 4
    assert polyline[0] == (0.0, 0.0, 0.25)
    assert polyline[1] == (0.0, 0.0, 0.0)
    assert polyline[2] == (3.0, 0.0, 0.0)
    assert polyline[3] == (3.0, 0.0, 0.25)


def test_shape_41_rectangular_stirrup():
    polyline = generate_shape_41(
        width=0.20,
        depth=0.40,
        hook_length=0.075,
        origin=(0.0, 0.0, 0.0),
    )
    # Shape 41 has 7 points: hook1 -> c0 -> c1 -> c2 -> c3 -> c4(c0) -> hook2
    assert len(polyline) == 7
    # Corner 0
    assert polyline[1] == (0.0, 0.40, 0.0)
    # Corner 1
    assert polyline[2] == (0.20, 0.40, 0.0)
    # Corner 2
    assert polyline[3] == (0.20, 0.0, 0.0)
    # Corner 3
    assert polyline[4] == (0.0, 0.0, 0.0)
    # Corner 4 (closing corner)
    assert polyline[5] == (0.0, 0.40, 0.0)


def test_shape_99_column_dowel():
    polyline = generate_shape_99(
        height=3.5,
        dowel_length=0.40,
        origin=(0.0, 0.0, 0.0),
        dowel_direction=(-1.0, 0.0, 0.0),
    )
    assert len(polyline) == 3
    assert polyline[0] == (-0.40, 0.0, 0.0)
    assert polyline[1] == (0.0, 0.0, 0.0)
    assert polyline[2] == (0.0, 0.0, 3.5)


def test_rebar_diameter_color_mapping():
    """Verifies color mapping for standard rebar sizes (RB6 to DB32)."""
    expected = {
        "RB6": "#B0C4DE",
        "RB9": "#4682B4",
        "DB12": "#2E8B57",
        "DB16": "#FF8C00",
        "DB20": "#DC143C",
        "DB25": "#8B0000",
        "DB28": "#4B0082",
        "DB32": "#2F4F4F",
    }
    for sz, hex_c in expected.items():
        assert get_rebar_color(sz) == hex_c

    # Float diameters in meters
    assert get_rebar_color(0.006) == "#B0C4DE"
    assert get_rebar_color(0.009) == "#4682B4"
    assert get_rebar_color(0.012) == "#2E8B57"
    assert get_rebar_color(0.016) == "#FF8C00"
    assert get_rebar_color(0.020) == "#DC143C"
    assert get_rebar_color(0.025) == "#8B0000"
    assert get_rebar_color(0.028) == "#4B0082"
    assert get_rebar_color(0.032) == "#2F4F4F"

    # String specs like "2DB12" or "RB9@0.15"
    assert get_rebar_color("2DB12") == "#2E8B57"
    assert get_rebar_color("RB9@0.15") == "#4682B4"


def test_generate_tubular_mesh_faces_structure():
    """Verifies generated tubular mesh structure including 3D face loops."""
    polyline = generate_shape_00(length=2.0)
    mesh = generate_tubular_mesh(polyline, diameter=0.016, radial_segments=6, close_caps=True)

    assert "vertices" in mesh
    assert "indices" in mesh
    assert "faces" in mesh
    assert "line_indices" in mesh
    assert "polyline" in mesh

    # 2 polyline points * 6 radial segments + 2 end caps = 14 vertices
    assert len(mesh["vertices"]) == 14

    # 1 segment (6 quads = 12 triangles) + 2 end caps (6 triangles each = 12) = 24 triangles
    assert len(mesh["indices"]) == 24
    assert len(mesh["faces"]) == 24

    # Each face loop in 'faces' must be a list of 3 3D coordinate points [x, y, z]
    for face in mesh["faces"]:
        assert len(face) == 3
        for pt in face:
            assert len(pt) == 3
            assert isinstance(pt[0], float)
            assert isinstance(pt[1], float)
            assert isinstance(pt[2], float)


def test_generate_tubular_mesh_short_polyline():
    mesh = generate_tubular_mesh([(0.0, 0.0, 0.0)], diameter=0.012)
    assert mesh["vertices"] == []
    assert mesh["indices"] == []
    assert mesh["faces"] == []


def test_generate_column_rebar_cage():
    """Verifies generating 3D rebar cage (main bars and stirrups) for a Column."""
    col = Column(id="C1", width=0.30, depth=0.30, height=3.0, main_bar_count=8, main_bar_dia=0.016, stirrup_dia=0.009, stirrup_spacing=0.15)
    cage = generate_column_rebar_cage(col)

    assert len(cage) > 0
    main_bars = [item for item in cage if item["type"] == "main_bar"]
    stirrups = [item for item in cage if item["type"] == "stirrup"]

    assert len(main_bars) == 8
    assert len(stirrups) > 10

    # Verify color assignment and mesh face generation
    assert main_bars[0]["color"] == "#FF8C00"  # DB16
    assert stirrups[0]["color"] == "#4682B4"  # RB9
    assert len(main_bars[0]["faces"]) > 0
    assert len(stirrups[0]["faces"]) > 0


def test_generate_beam_rebar_cage():
    """Verifies generating 3D rebar cage for a Beam."""
    beam = Beam(id="B1", width=0.20, depth=0.40, top_bar_spec="2DB12", bot_bar_spec="3DB12", extra_bar_spec="1DB12", stirrup_spec="RB6@0.175")
    cage = generate_beam_rebar_cage(beam)

    assert len(cage) > 0
    top_bars = [item for item in cage if item["type"] == "top_main_bar"]
    bot_bars = [item for item in cage if item["type"] == "bot_main_bar"]
    extra_bars = [item for item in cage if item["type"] == "extra_bar"]
    stirrups = [item for item in cage if item["type"] == "stirrup"]

    assert len(top_bars) == 2
    assert len(bot_bars) == 3
    assert len(extra_bars) == 1
    assert len(stirrups) > 10

    assert top_bars[0]["color"] == "#2E8B57"  # DB12
    assert stirrups[0]["color"] == "#B0C4DE"  # RB6


def test_generate_footing_rebar_cage():
    """Verifies generating 3D rebar cage for a Footing."""
    f = Footing(id="F1", width=1.20, length=1.20, thickness=0.35, rebar_x_count=5, rebar_y_count=5, rebar_x_dia=0.012, rebar_y_dia=0.012)
    cage = generate_footing_rebar_cage(f)

    assert len(cage) == 10  # 5 in X + 5 in Y
    assert cage[0]["color"] == "#2E8B57"  # DB12
    assert len(cage[0]["faces"]) > 0


def test_generic_generate_rebar_cage_dispatcher():
    col = Column(id="C1", width=0.3, depth=0.3, height=3.0)
    cage = generate_rebar_cage(col)
    assert len(cage) > 0


def test_plugin_rebar_show_hide_toggle():
    """Verifies Show/Hide rebar toggle UI state in ChakkreeToolsPlugin."""
    plugin = ChakkreeToolsPlugin()
    assert plugin.show_rebars is False  # Defaults to False

    state1 = plugin.cmd_toggle_rebars()
    assert state1 is True
    assert plugin.show_rebars is True

    state2 = plugin.cmd_toggle_rebars()
    assert state2 is False
    assert plugin.show_rebars is False


def test_exporter_with_rebar_mesh():
    """Verifies exporting debim manifest with 3D rebar cage geometry."""
    exporter = DebimExporter(project_name="Rebar Mesh Test")
    col = Column(id="C1", width=0.3, depth=0.3, height=3.0)
    exporter.add_element(col)

    data_with_rebar = exporter.to_dict(include_rebar_mesh=True)
    elem = data_with_rebar["elements"][0]
    assert "rebar_mesh" in elem
    assert len(elem["rebar_mesh"]) > 0
    assert elem["rebar_mesh"][0]["color"] == "#FF8C00"
