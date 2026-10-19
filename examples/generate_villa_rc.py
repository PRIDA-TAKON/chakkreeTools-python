import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from chakkree_tools.rc.footing import PileCap
from chakkree_tools.rc.column import Column
from chakkree_tools.rc.beam import Beam
from chakkree_tools.rc.slab import Slab
from chakkree_tools.exporter.debim_exporter import DebimExporter


def main():
    print("Building Structural RC Villa using Chakkree Tools...")

    exporter = DebimExporter(project_name="Modern Villa RC - Chakkree Tools")
    exporter.set_grids(
        axes_x={"1": 0.0, "2": 4.0, "3": 8.0},
        axes_y={"A": 0.0, "B": 5.0},
    )

    # 1. Pile Caps F1 (2 Piles) under columns
    f1 = PileCap.create_n_piles("F1_1A", pile_count=2, elevation=-0.70)
    f2 = PileCap.create_n_piles("F1_2A", pile_count=2, elevation=-0.70)
    f3 = PileCap.create_n_piles("F1_3A", pile_count=2, elevation=-0.70)
    f4 = PileCap.create_n_piles("F1_1B", pile_count=2, elevation=-0.70)
    f5 = PileCap.create_n_piles("F1_2B", pile_count=2, elevation=-0.70)
    f6 = PileCap.create_n_piles("F1_3B", pile_count=2, elevation=-0.70)

    for f in [f1, f2, f3, f4, f5, f6]:
        exporter.add_element(f)

    # 2. RC Columns C1 (8-DB16)
    c1 = Column(id="C1_1A", grid_ref=("1", "A"), width=0.3, depth=0.3, height=3.5)
    c2 = Column(id="C1_2A", grid_ref=("2", "A"), width=0.3, depth=0.3, height=3.5)
    c3 = Column(id="C1_3A", grid_ref=("3", "A"), width=0.3, depth=0.3, height=3.5)
    c4 = Column(id="C1_1B", grid_ref=("1", "B"), width=0.3, depth=0.3, height=3.5)
    c5 = Column(id="C1_2B", grid_ref=("2", "B"), width=0.3, depth=0.3, height=3.5)
    c6 = Column(id="C1_3B", grid_ref=("3", "B"), width=0.3, depth=0.3, height=3.5)

    for c in [c1, c2, c3, c4, c5, c6]:
        exporter.add_element(c)

    # 3. RC Beams B1
    b1 = Beam(id="B1_1A_2A", width=0.2, depth=0.4, from_grid=("1", "A"), to_grid=("2", "A"))
    b2 = Beam(id="B1_2A_3A", width=0.2, depth=0.4, from_grid=("2", "A"), to_grid=("3", "A"))
    b3 = Beam(id="B1_1B_2B", width=0.2, depth=0.4, from_grid=("1", "B"), to_grid=("2", "B"))
    b4 = Beam(id="B1_2B_3B", width=0.2, depth=0.4, from_grid=("2", "B"), to_grid=("3", "B"))
    b5 = Beam(id="B1_1A_1B", width=0.2, depth=0.4, from_grid=("1", "A"), to_grid=("1", "B"))
    b6 = Beam(id="B1_2A_2B", width=0.2, depth=0.4, from_grid=("2", "A"), to_grid=("2", "B"))
    b7 = Beam(id="B1_3A_3B", width=0.2, depth=0.4, from_grid=("3", "A"), to_grid=("3", "B"))

    for b in [b1, b2, b3, b4, b5, b6, b7]:
        exporter.add_element(b)

    # 4. Slabs (PS Precast Plank Slabs)
    s1 = Slab(id="S1_ROOM1", slab_type="PS", boundary=[(0, 0), (4, 0), (4, 5), (0, 5)])
    s2 = Slab(id="S1_ROOM2", slab_type="PS", boundary=[(4, 0), (8, 0), (8, 5), (4, 5)])

    exporter.add_element(s1)
    exporter.add_element(s2)

    output_path = Path("examples/villa_rc_model.debim.yaml")
    exporter.save(output_path)
    print(f"Exported .debim manifest successfully to: {output_path}")


if __name__ == "__main__":
    main()
