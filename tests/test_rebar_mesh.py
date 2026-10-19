"""
Unit tests for 3D Rebar Polyline and Tubular Mesh Generator
"""

import math
import pytest
from chakkree_tools.rc import (
    generate_shape_00,
    generate_shape_21,
    generate_shape_41,
    generate_shape_99,
    generate_tubular_mesh,
)


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


def test_generate_tubular_mesh_structure():
    polyline = generate_shape_00(length=2.0)
    mesh = generate_tubular_mesh(polyline, diameter=0.016, radial_segments=8, close_caps=True)

    assert "vertices" in mesh
    assert "indices" in mesh
    assert "line_indices" in mesh
    assert "polyline" in mesh

    # 2 polyline points * 8 radial segments + 2 end caps = 18 vertices
    assert len(mesh["vertices"]) == 18

    # 1 segment (8 quads = 16 triangles) + 2 end caps (8 triangles each = 16) = 32 triangles
    assert len(mesh["indices"]) == 32

    # Wireframe lines
    assert len(mesh["line_indices"]) > 0


def test_generate_tubular_mesh_short_polyline():
    mesh = generate_tubular_mesh([(0.0, 0.0, 0.0)], diameter=0.012)
    assert mesh["vertices"] == []
    assert mesh["indices"] == []
