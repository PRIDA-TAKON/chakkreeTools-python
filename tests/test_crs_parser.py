"""
Unit tests for CRSParser (Chakkree Rebar Script Parser)
"""

from chakkree_tools.dsl.crs_parser import CRSParser, CRSBox, CRSRebar


def test_crs_parser_simple_script():
    script = """
    # Simple Beam Test
    var L = 4000.mm
    var b = 200.mm
    var h = 400.mm
    var cvr = 25.mm
    var diaTM = 12.mm

    box 'concrete' ,[$L, $b, $h], ['concrete', 'Bisque', 0.5]
    tran 'concrete', [2.0, 0, -0.2]

    rebar 'TopMain', $diaTM, 21, [0.3, 4.1, 0.3], default, S, 2, 0.15
    """

    parser = CRSParser()
    entities = parser.parse_script(script)

    assert len(entities) == 2
    box = entities[0]
    assert isinstance(box, CRSBox)
    assert box.name == "concrete"
    assert box.dimensions == (4.0, 0.2, 0.4)
    assert box.translation == (2.0, 0.0, -0.2)

    rebar = entities[1]
    assert isinstance(rebar, CRSRebar)
    assert rebar.name == "TopMain"
    assert round(rebar.diameter, 3) == 0.012
    assert rebar.shape_code == 21
    assert rebar.count == 2
    assert round(rebar.spacing, 2) == 0.15


def test_crs_parser_copy_instruction():
    script = """
    var b = 300.mm
    rebar 'Bar1', 16.mm, 0, [3.0]
    copy 'Bar1', 3, [0, 0.1, 0]
    """
    parser = CRSParser()
    entities = parser.parse_script(script)

    assert len(entities) == 4
    assert entities[0].name == "Bar1"
    assert entities[1].name == "Bar1_copy_1"
    assert entities[2].name == "Bar1_copy_2"
    assert entities[3].name == "Bar1_copy_3"
    assert entities[3].translation == (0.0, 0.3, 0.0)
