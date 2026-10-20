"""
Tests for Chakkree Tools CLI commands and IngeTrazo Plugin Element Generation.
Verifies creating 3 different parametric variations for each structural element type.
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
    # Test help without exiting
    assert main([]) == 0
    assert main(["standards"]) == 0
    assert main(["colors"]) == 0
    assert main(["about"]) == 0


def test_cli_footing_three_variations():
    # 1. Isolated footing
    rc1 = main(["footing", "--id", "F1", "--width", "1.0", "--length", "1.0", "--thickness", "0.30", "--qto"])
    assert rc1 == 0

    # 2. 2-Pile Cap
    rc2 = main(["footing", "--id", "F2", "--piles", "2", "--pile-size", "0.22", "--thickness", "0.50"])
    assert rc2 == 0

    # 3. 4-Pile Cap
    rc3 = main(["footing", "--id", "F3", "--piles", "4", "--pile-size", "0.26", "--thickness", "0.70"])
    assert rc3 == 0


def test_cli_column_three_variations():
    # 1. Small column (0.2x0.2m, 4 bars)
    rc1 = main(["column", "--id", "C1", "--width", "0.20", "--depth", "0.20", "--height", "3.0", "--bars", "4"])
    assert rc1 == 0

    # 2. Standard column (0.3x0.3m, 8 bars)
    rc2 = main(["column", "--id", "C2", "--width", "0.30", "--depth", "0.30", "--height", "3.5", "--bars", "8"])
    assert rc2 == 0

    # 3. Circular column (Dia 0.4m, 10 bars)
    rc3 = main(["column", "--id", "C3", "--profile", "circular", "--width", "0.40", "--height", "4.0", "--bars", "10"])
    assert rc3 == 0


def test_cli_beam_three_variations():
    # 1. Short beam (0.15x0.30m, L=2.5m)
    rc1 = main(["beam", "--id", "B1", "--width", "0.15", "--depth", "0.30", "--length", "2.5", "--top-bar", "2DB12", "--bot-bar", "2DB12"])
    assert rc1 == 0

    # 2. Main girder (0.20x0.45m, L=4.0m)
    rc2 = main(["beam", "--id", "B2", "--width", "0.20", "--depth", "0.45", "--length", "4.0", "--top-bar", "2DB16", "--bot-bar", "3DB16"])
    assert rc2 == 0

    # 3. Long span beam (0.25x0.60m, L=6.0m)
    rc3 = main(["beam", "--id", "B3", "--width", "0.25", "--depth", "0.60", "--length", "6.0", "--top-bar", "3DB20", "--bot-bar", "4DB20"])
    assert rc3 == 0


def test_cli_slab_three_variations():
    # 1. PS Plank Slab (3x3m)
    rc1 = main(["slab", "--id", "S1", "--type", "ps", "--span-x", "3.0", "--span-y", "3.0"])
    assert rc1 == 0

    # 2. RC Cast-in-place Slab (4x5m)
    rc2 = main(["slab", "--id", "S2", "--type", "rc", "--span-x", "4.0", "--span-y", "5.0", "--thickness", "0.12"])
    assert rc2 == 0

    # 3. Balcony / Cantilever Slab (1.5x4m)
    rc3 = main(["slab", "--id", "S3", "--type", "rc", "--span-x", "1.5", "--span-y", "4.0", "--thickness", "0.10"])
    assert rc3 == 0


def test_ingetrazo_plugin_3d_generation_and_debim_export(tmp_path):
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
    # Verify 3D mesh faces were added to the scene
    assert len(app._scene.mesh.faces) > 0

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
