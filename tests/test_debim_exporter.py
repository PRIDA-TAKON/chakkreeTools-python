"""
Unit tests for DebimExporter
"""

import yaml
from chakkree_tools.exporter.debim_exporter import DebimExporter, export_to_debim
from chakkree_tools.rc.footing import PileCap
from chakkree_tools.rc.column import Column
from chakkree_tools.rc.beam import Beam
from chakkree_tools.rc.slab import Slab


def test_debim_export_roundtrip(tmp_path):
    exporter = DebimExporter(project_name="Test Villa RC")
    exporter.set_grids(axes_x={"1": 0.0, "2": 4.0}, axes_y={"A": 0.0, "B": 5.0})

    f1 = PileCap.create_n_piles(id_str="F1", pile_count=2)
    c1 = Column(id="C1", width=0.3, depth=0.3, height=3.5, grid_ref=("1", "A"))
    b1 = Beam(id="B1", width=0.2, depth=0.4, from_grid=("1", "A"), to_grid=("2", "A"))
    s1 = Slab(id="S1", boundary=[(0, 0), (4, 0), (4, 5), (0, 5)])

    exporter.add_element(f1)
    exporter.add_element(c1)
    exporter.add_element(b1)
    exporter.add_element(s1)

    out_file = tmp_path / "model.debim.yaml"
    exporter.save(out_file)

    assert out_file.exists()
    content = out_file.read_text(encoding="utf-8")
    data = yaml.safe_load(content)

    assert data["schema"] == "IFC4-Minimal"
    assert data["project"]["name"] == "Test Villa RC"
    assert "grids" in data
    assert len(data["elements"]) == 4

    classes = [e["class"] for e in data["elements"]]
    assert "IfcFooting" in classes
    assert "IfcColumn" in classes
    assert "IfcBeam" in classes
    assert "IfcSlab" in classes
