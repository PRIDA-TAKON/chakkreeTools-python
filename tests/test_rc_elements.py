"""
Unit tests for RC Elements and StirrupPattern
"""

from chakkree_tools.rc.stirrup_pattern import StirrupPattern
from chakkree_tools.rc.footing import PileCap, Footing
from chakkree_tools.rc.column import Column
from chakkree_tools.rc.beam import Beam
from chakkree_tools.rc.slab import Slab


def test_stirrup_pattern_single_zone():
    sp = StirrupPattern(
        diameter=0.006,
        width=0.150,
        depth=0.350,
        length=4.0,
        n_spacing=[[1, 0.150]],
    )
    sp.adjust_offset_for_length(4.0)
    assert sp.count_stirrups() > 20
    summary = sp.summary()
    assert summary["dia_mm"] == 6.0
    assert summary["width_mm"] == 150.0


def test_pile_cap_factory():
    # 2 Piles cap
    f2 = PileCap.create_n_piles(id_str="F2", pile_count=2, pile_size=0.22, thickness=0.60)
    assert f2.concrete_volume > 0.0
    assert f2.formwork_area > 0.0
    assert f2.pile_spec.count == 2

    # 4 Piles cap
    f4 = PileCap.create_n_piles(id_str="F4", pile_count=4, pile_size=0.22, thickness=0.60)
    assert f4.width == f4.length
    assert f4.pile_spec.count == 4


def test_column_and_beam():
    col = Column(id="C1", width=0.3, depth=0.3, height=3.5)
    assert round(col.concrete_volume, 3) == 0.315
    assert round(col.formwork_area, 2) == 4.20

    beam = Beam(id="B1", width=0.2, depth=0.4, start_point=(0, 0), end_point=(4, 0))
    assert round(beam.length, 2) == 4.00
    assert round(beam.concrete_volume, 3) == 0.320


def test_slab_shoelace():
    slab = Slab(
        id="S1",
        boundary=[(0.0, 0.0), (5.0, 0.0), (5.0, 4.0), (0.0, 4.0)],
        thickness=0.10,
    )
    assert round(slab.area, 1) == 20.0
