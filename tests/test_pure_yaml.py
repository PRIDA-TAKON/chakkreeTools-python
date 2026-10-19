"""
Unit tests for pure_yaml serializer.
"""

from chakkree_tools.exporter.pure_yaml import dump_yaml, safe_dump


def test_pure_yaml_primitives():
    assert dump_yaml(None) == "null"
    assert dump_yaml(True) == "true"
    assert dump_yaml(False) == "false"
    assert dump_yaml(42) == "42"
    assert dump_yaml(3.14) == "3.14"
    assert dump_yaml("hello") == "hello"
    assert dump_yaml("hello: world") == '"hello: world"'


def test_pure_yaml_lists_and_dicts():
    d = {
        "project": {"name": "Villa", "units": "m"},
        "coords": [0.0, 3.5],
        "elements": [
            {"id": "C1", "section": [0.3, 0.3]},
            {"id": "C2", "section": [0.4, 0.4]},
        ],
    }
    yaml_str = safe_dump(d)
    assert "project:" in yaml_str
    assert "Villa" in yaml_str
    assert "coords: [0.0, 3.5]" in yaml_str
    assert "- id: C1" in yaml_str
    assert "- id: C2" in yaml_str
