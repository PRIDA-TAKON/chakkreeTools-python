"""
Unit tests for S2DParser (Structure 2D Parser)
"""

from pathlib import Path
import pytest
from chakkree_tools.dsl.s2d_parser import S2DParser, S2DParseResult, InputBoxField, S2DEntity, parse_unit_value


REFS_DIR = Path(__file__).parent.parent / "references" / "original_specs" / "chakkree_tools" / "Extensions"


def test_s2d_parser_basic_syntax():
    script = """
    # Simple Beam Section
    var b = 200.mm
    var h = 400.mm
    var cvr = 25.mm
    set b = 250.mm

    break_IfNOT "SimpleBeam"

    inputbox 'Beam Section Parameters' , \
        ['Width b=', 'Height h='], \
        [$b, $h], \
        ['200mm|250mm|300mm', '400mm|500mm'], \
        ['b', 'h']

    rect -$b/2, -$h/2, $b, $h
    """

    parser = S2DParser()
    res = parser.parse_script(script)

    assert isinstance(res, S2DParseResult)
    assert res.title == "Beam Section Parameters"
    assert res.break_if_not == "SimpleBeam"
    assert res.variables["b"] == 0.25
    assert res.variables["h"] == 0.4
    assert res.variables["cvr"] == 0.025
    assert len(res.inputs) == 2
    assert res.inputs[0].var_name == "b"
    assert res.inputs[0].choices == ["200mm", "250mm", "300mm"]

    assert len(res.entities) == 1
    rect_ent = res.entities[0]
    assert rect_ent.type == "rect"
    assert rect_ent.properties["width"] == 0.25
    assert rect_ent.properties["height"] == 0.4

    bbox = res.bounding_box
    assert bbox["width"] == 0.25
    assert bbox["height"] == 0.4


def test_s2d_parser_inputs_override():
    script = """
    var b = 200.mm
    var h = 400.mm

    inputbox 'Params' , \
        ['Width=', 'Height='], \
        [$b, $h], \
        ['', ''], \
        ['b', 'h']
    """

    parser = S2DParser()
    res = parser.parse_script(script, inputs={"b": "300mm", "h": "600mm"})

    assert res.variables["b"] == 0.3
    assert res.variables["h"] == 0.6


def test_s2d_parser_get_set_attributes():
    script = """
    var type_str = "DefaultType"
    get_attribute "chakkree_tools", "script_creater", "STRING"
    get_attribute "chakkree_tools", "data", "JSON"

    set_attribute "chakkree_tools", "type", "STRING", "Footing_2DTOP"
    set_attribute "chakkree_tools", "data", "JSON", '{"B": "600mm", "L": "1200mm"}'
    """

    initial_attrs = {
        "chakkree_tools": {
            "script_creater": "Footing_9Piles",
            "data": {"b": "300mm", "t": "500mm"},
        }
    }

    parser = S2DParser()
    res = parser.parse_script(script, attributes=initial_attrs)

    assert res.variables["script_creater"] == "Footing_9Piles"
    assert res.variables["b"] == 0.3
    assert res.variables["t"] == 0.5
    assert res.attributes["chakkree_tools"]["type"] == "Footing_2DTOP"
    assert res.attributes["chakkree_tools"]["data"] == '{"B": "600mm", "L": "1200mm"}'


def test_s2d_parser_topview_recpile():
    file_path = REFS_DIR / "PileFootings" / "9Piles" / "TopView_RecPile.s2d"
    assert file_path.exists()

    script = file_path.read_text(encoding="utf-8")
    parser = S2DParser()
    res = parser.parse_script(script)

    assert res.break_if_not == "ฐานรากเสาเข็ม9ต้น"
    assert res.title == "ป้อนข้อมูล PileCAP เสาเข็ม 9 ต้น"
    assert len(res.inputs) == 8
    assert res.inputs[2].var_name == "Dp"
    assert "220mm" in res.inputs[2].choices

    # Check extracted parameters dictionary export
    export_dict = res.to_dict()
    assert export_dict["title"] == "ป้อนข้อมูล PileCAP เสาเข็ม 9 ต้น"
    assert export_dict["break_if_not"] == "ฐานรากเสาเข็ม9ต้น"
    assert "variables" in export_dict
    assert "bounding_box" in export_dict
    assert export_dict["attributes"]["chakkree_tools"]["type"] == "Footing_2DTOP"


def test_s2d_parser_column_section():
    file_path = REFS_DIR / "Columns" / "Rect_8bar_01" / "Column_Section.s2d"
    assert file_path.exists()

    script = file_path.read_text(encoding="utf-8")
    parser = S2DParser()
    res = parser.parse_script(script)

    assert res.break_if_not == "หน้าตัดเสาสี่เหลี่ยมเหล็กยืน8แบบ1"
    assert res.title == "ป้อนค่าวาดหน้าตัดเสาสี่เหลี่ยม เหล็กยืน 8 เส้น"
    assert len(res.inputs) == 6
    assert res.variables["n1"] == 8
    assert res.attributes["chakkree_tools"]["type"] == "Column_2DTOP"


def test_s2d_parser_topview_ps():
    file_path = REFS_DIR / "Slabs" / "PS" / "TopView_PS.s2d"
    assert file_path.exists()

    script = file_path.read_text(encoding="utf-8")
    parser = S2DParser()
    res = parser.parse_script(script)

    assert res.break_if_not == "แผ่นพื้นสำเร็จรูป"
    assert res.title == "กำหนดข้อมูลแผ่นพื้นสำเร็จรูป"
    assert len(res.inputs) == 3
    assert res.variables["L"] == pytest.approx(4.0)
    assert res.variables["w"] == pytest.approx(0.35)
    assert res.variables["n"] == 4
    assert res.attributes["chakkree_tools"]["subtype"] == "PS"


def test_s2d_parser_grids():
    file_path = REFS_DIR / "MT_Family01" / "Grids" / "Grids.s2d"
    assert file_path.exists()

    script = file_path.read_text(encoding="utf-8")
    parser = S2DParser()
    res = parser.parse_script(script)

    assert res.attributes["chakkree_tools"]["subtype"] == "GridLine"
    assert any(ent.type == "grid" for ent in res.entities)
