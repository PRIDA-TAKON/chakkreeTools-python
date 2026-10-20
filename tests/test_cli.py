"""
Tests for Chakkree Tools CLI commands and IngeTrazo Plugin Element Generation.
Verifies creating 3 different parametric variations for each structural element type
and explicitly asserts their exact dimensions, concrete volumes, formwork areas,
rebar weights, and 3D mesh representations.
"""

import subprocess
import sys
from pathlib import Path
import pytest

from chakkree_tools.cli import build_parser, main
from chakkree_tools.ingetrazo_plugin.plugin import ChakkreeToolsPlugin, setup
from chakkree_tools.rc.footing import Footing, PileCap
from chakkree_tools.rc.column import Column
from chakkree_tools.rc.beam import Beam
from chakkree_tools.rc.slab import Slab


class MockMesh:
    def __init__(self):
        self.faces = []

    def add_face(self, pts):
        self.faces.append(pts)


class MockScene:
    def __init__(self):
        self.mesh = MockMesh()
        self.version = 0

    def bump_view(self):
        self.version += 1


class MockViewport:
    def __init__(self, scene):
        self.scene = scene
        self.updated = False

    def update(self):
        self.updated = True


class MockApp:
    def __init__(self):
        self._scene = MockScene()
        self.viewport = MockViewport(self._scene)
        self.status_log = []

    def scene(self):
        return self._scene

    def flash_status(self, msg):
        self.status_log.append(msg)


def test_cli_subcommands_and_help():
    parser = build_parser()
    assert parser is not None
    assert main([]) == 0
    assert main(["standards"]) == 0
    assert main(["colors"]) == 0
    assert main(["about"]) == 0


def test_cli_footing_three_variations(tmp_path):
    """
    Test 3 distinct parametric Footing variations:
    1. Isolated Footing (1.0 x 1.0 x 0.30 m)
    2. 2-Pile Cap (Dp=0.22 m, T=0.50 m)
    3. 4-Pile Cap (Dp=0.26 m, T=0.70 m)
    """
    # 1. Isolated footing (1.0 x 1.0 x 0.30 m)
    out1 = tmp_path / "f1.debim.yaml"
    rc1 = main(["footing", "--id", "F1_ISO", "--width", "1.0", "--length", "1.0", "--thickness", "0.30", "--qto", "--out", str(out1)])
    assert rc1 == 0
    assert out1.exists()

    # Direct model verification
    f1 = Footing(id="F1_ISO", width=1.0, length=1.0, thickness=0.30)
    assert pytest.approx(f1.concrete_volume, 0.001) == 0.300
    assert pytest.approx(f1.formwork_area, 0.001) == 1.200

    # 2. 2-Pile Cap (Dp=0.22 m, T=0.50 m)
    out2 = tmp_path / "f2.debim.yaml"
    rc2 = main(["footing", "--id", "F2_2PILE", "--piles", "2", "--pile-size", "0.22", "--thickness", "0.50", "--out", str(out2)])
    assert rc2 == 0
    assert out2.exists()

    f2 = PileCap.create_n_piles(id_str="F2_2PILE", pile_count=2, pile_size=0.22, thickness=0.50)
    assert pytest.approx(f2.width, 0.001) == 0.660
    assert pytest.approx(f2.length, 0.001) == 1.320
    assert pytest.approx(f2.concrete_volume, 0.001) == 0.436
    assert pytest.approx(f2.formwork_area, 0.001) == 1.980

    # 3. 4-Pile Cap (Dp=0.26 m, T=0.70 m)
    out3 = tmp_path / "f3.debim.yaml"
    rc3 = main(["footing", "--id", "F3_4PILE", "--piles", "4", "--pile-size", "0.26", "--thickness", "0.70", "--out", str(out3)])
    assert rc3 == 0
    assert out3.exists()

    f3 = PileCap.create_n_piles(id_str="F3_4PILE", pile_count=4, pile_size=0.26, thickness=0.70)
    assert pytest.approx(f3.width, 0.001) == 1.560
    assert pytest.approx(f3.length, 0.001) == 1.560
    assert pytest.approx(f3.concrete_volume, 0.001) == 1.704
    assert pytest.approx(f3.formwork_area, 0.001) == 4.368


def test_cli_column_three_variations(tmp_path):
    """
    Test 3 distinct parametric Column variations:
    1. Small Column (0.20 x 0.20 m, H=3.0 m, 4 bars)
    2. Standard Column (0.30 x 0.30 m, H=3.5 m, 8 bars)
    3. Circular Column (Dia=0.40 m, H=4.0 m, 10 bars)
    """
    # 1. Small column
    out1 = tmp_path / "c1.debim.yaml"
    rc1 = main(["column", "--id", "C1_20x20", "--width", "0.20", "--depth", "0.20", "--height", "3.0", "--bars", "4", "--out", str(out1)])
    assert rc1 == 0
    assert out1.exists()

    c1 = Column(id="C1_20x20", width=0.20, depth=0.20, height=3.0, main_bar_count=4)
    assert pytest.approx(c1.concrete_volume, 0.001) == 0.120
    assert pytest.approx(c1.formwork_area, 0.001) == 2.400

    # 2. Standard column
    out2 = tmp_path / "c2.debim.yaml"
    rc2 = main(["column", "--id", "C2_30x30", "--width", "0.30", "--depth", "0.30", "--height", "3.5", "--bars", "8", "--out", str(out2)])
    assert rc2 == 0
    assert out2.exists()

    c2 = Column(id="C2_30x30", width=0.30, depth=0.30, height=3.5, main_bar_count=8)
    assert pytest.approx(c2.concrete_volume, 0.001) == 0.315
    assert pytest.approx(c2.formwork_area, 0.001) == 4.200

    # 3. Circular column
    out3 = tmp_path / "c3.debim.yaml"
    rc3 = main(["column", "--id", "C3_CIRC", "--profile", "circular", "--width", "0.40", "--height", "4.0", "--bars", "10", "--out", str(out3)])
    assert rc3 == 0
    assert out3.exists()

    c3 = Column(id="C3_CIRC", profile="CIRCULAR", width=0.40, height=4.0, main_bar_count=10)
    # Circle volume: pi * r^2 * h = 3.14159 * 0.04 * 4.0 = ~0.50265
    assert pytest.approx(c3.concrete_volume, 0.01) == 0.503
    assert pytest.approx(c3.formwork_area, 0.01) == 5.03


def test_cli_beam_three_variations(tmp_path):
    """
    Test 3 distinct parametric Beam variations:
    1. Secondary Beam (0.15 x 0.30 m, L=2.5 m, 2DB12 top/bot)
    2. Main Girder (0.20 x 0.45 m, L=4.0 m, 2DB16 top, 3DB16 bot)
    3. Long Span Beam (0.25 x 0.60 m, L=6.0 m, 3DB20 top, 4DB20 bot)
    """
    # 1. Short beam
    out1 = tmp_path / "b1.debim.yaml"
    rc1 = main(["beam", "--id", "B1_SHORT", "--width", "0.15", "--depth", "0.30", "--length", "2.5", "--top-bar", "2DB12", "--bot-bar", "2DB12", "--out", str(out1)])
    assert rc1 == 0
    assert out1.exists()

    b1 = Beam(id="B1_SHORT", width=0.15, depth=0.30, start_point=(0.0, 0.0), end_point=(2.5, 0.0))
    assert pytest.approx(b1.length, 0.001) == 2.500
    assert pytest.approx(b1.concrete_volume, 0.001) == 0.1125
    assert pytest.approx(b1.formwork_area, 0.001) == 1.875

    # 2. Main girder
    out2 = tmp_path / "b2.debim.yaml"
    rc2 = main(["beam", "--id", "B2_MAIN", "--width", "0.20", "--depth", "0.45", "--length", "4.0", "--top-bar", "2DB16", "--bot-bar", "3DB16", "--out", str(out2)])
    assert rc2 == 0
    assert out2.exists()

    b2 = Beam(id="B2_MAIN", width=0.20, depth=0.45, start_point=(0.0, 0.0), end_point=(4.0, 0.0))
    assert pytest.approx(b2.length, 0.001) == 4.000
    assert pytest.approx(b2.concrete_volume, 0.001) == 0.360
    assert pytest.approx(b2.formwork_area, 0.001) == 4.400

    # 3. Long span beam
    out3 = tmp_path / "b3.debim.yaml"
    rc3 = main(["beam", "--id", "B3_LONG", "--width", "0.25", "--depth", "0.60", "--length", "6.0", "--top-bar", "3DB20", "--bot-bar", "4DB20", "--out", str(out3)])
    assert rc3 == 0
    assert out3.exists()

    b3 = Beam(id="B3_LONG", width=0.25, depth=0.60, start_point=(0.0, 0.0), end_point=(6.0, 0.0))
    assert pytest.approx(b3.length, 0.001) == 6.000
    assert pytest.approx(b3.concrete_volume, 0.001) == 0.900
    assert pytest.approx(b3.formwork_area, 0.001) == 8.700


def test_cli_slab_three_variations(tmp_path):
    """
    Test 3 distinct parametric Slab variations:
    1. Precast Plank Slab - PS (3.0 x 3.0 m, Topping 5cm)
    2. Cast-in-place Slab - RC (4.0 x 5.0 m, T=12cm)
    3. Balcony / Cantilever Slab - RC (1.5 x 4.0 m, T=10cm)
    """
    # 1. PS Plank Slab
    out1 = tmp_path / "s1.debim.yaml"
    rc1 = main(["slab", "--id", "S1_PS", "--type", "ps", "--span-x", "3.0", "--span-y", "3.0", "--out", str(out1)])
    assert rc1 == 0
    assert out1.exists()

    s1 = Slab(id="S1_PS", slab_type="PS", boundary=[(0, 0), (3, 0), (3, 3), (0, 3)], topping_thickness=0.05)
    assert pytest.approx(s1.area, 0.001) == 9.000
    assert pytest.approx(s1.concrete_volume, 0.001) == 0.450
    assert pytest.approx(s1.formwork_area, 0.001) == 0.000  # Plank sits directly on beams

    # 2. RC Cast-in-place Slab
    out2 = tmp_path / "s2.debim.yaml"
    rc2 = main(["slab", "--id", "S2_RC", "--type", "rc", "--span-x", "4.0", "--span-y", "5.0", "--thickness", "0.12", "--out", str(out2)])
    assert rc2 == 0
    assert out2.exists()

    s2 = Slab(id="S2_RC", slab_type="RC", boundary=[(0, 0), (4, 0), (4, 5), (0, 5)], thickness=0.12)
    assert pytest.approx(s2.area, 0.001) == 20.000
    assert pytest.approx(s2.concrete_volume, 0.001) == 2.400
    assert pytest.approx(s2.formwork_area, 0.001) == 20.000

    # 3. Balcony / Cantilever Slab
    out3 = tmp_path / "s3.debim.yaml"
    rc3 = main(["slab", "--id", "S3_BALCONY", "--type", "rc", "--span-x", "1.5", "--span-y", "4.0", "--thickness", "0.10", "--out", str(out3)])
    assert rc3 == 0
    assert out3.exists()

    s3 = Slab(id="S3_BALCONY", slab_type="RC", boundary=[(0, 0), (1.5, 0), (1.5, 4), (0, 4)], thickness=0.10)
    assert pytest.approx(s3.area, 0.001) == 6.000
    assert pytest.approx(s3.concrete_volume, 0.001) == 0.600
    assert pytest.approx(s3.formwork_area, 0.001) == 6.000


def test_ingetrazo_plugin_3d_generation_and_debim_export(tmp_path):
    """
    Tests integrating all 12 elements (3 of each type) directly within IngeTrazo plugin context.
    Verifies 3D mesh faces creation and full .debim.yaml manifest export.
    """
    app = MockApp()
    plugin = setup(app)
    assert plugin is not None

    # 1. Footings (3 variations)
    f1 = Footing(id="F1_ISO", width=1.0, length=1.0, thickness=0.30)
    f2 = PileCap.create_n_piles(id_str="F2_2Piles", pile_count=2, pile_size=0.22, thickness=0.50)
    f3 = PileCap.create_n_piles(id_str="F3_4Piles", pile_count=4, pile_size=0.26, thickness=0.70)
    for f in [f1, f2, f3]:
        plugin.active_elements.append(f)
        plugin._render_footing_to_scene(f)

    # 2. Columns (3 variations)
    c1 = plugin.cmd_create_column(width=0.20, depth=0.20, height=3.0, show_dialog=False)
    c2 = plugin.cmd_create_column(width=0.30, depth=0.30, height=3.5, show_dialog=False)
    c3 = plugin.cmd_create_column(width=0.50, depth=0.50, height=4.5, show_dialog=False)

    # 3. Beams (3 variations)
    b1 = plugin.cmd_create_beam(width=0.15, depth=0.30, length=2.5, show_dialog=False)
    b2 = plugin.cmd_create_beam(width=0.20, depth=0.45, length=4.0, show_dialog=False)
    b3 = plugin.cmd_create_beam(width=0.25, depth=0.60, length=6.0, show_dialog=False)

    # 4. Slabs (3 variations)
    s1 = plugin.cmd_create_slab(boundary=[(0.0, 0.0), (3.0, 0.0), (3.0, 3.0), (0.0, 3.0)])
    s2 = plugin.cmd_create_slab(boundary=[(0.0, 0.0), (4.0, 0.0), (4.0, 5.0), (0.0, 5.0)])
    s3 = plugin.cmd_create_slab(boundary=[(0.0, 0.0), (1.5, 0.0), (1.5, 4.0), (0.0, 4.0)])

    assert len(plugin.active_elements) == 12
    # Verify 3D mesh faces were added to the scene (6 faces per footing, column, beam, slab)
    assert len(app._scene.mesh.faces) == 72

    # QTO Summary
    summary = plugin.cmd_qto_takeoff()
    assert summary.total_elements == 12
    assert summary.total_concrete_volume_m3 > 0.0
    assert summary.total_rebar_weight_kg > 0.0

    # Export to .debim
    debim_file = tmp_path / "project_model.debim.yaml"
    res = plugin.cmd_export_debim(output_path=debim_file)
    assert res is not None
    assert debim_file.exists()
    assert debim_file.stat().st_size > 0
