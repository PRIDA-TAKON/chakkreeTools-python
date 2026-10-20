"""
Tests for live IngeTrazo plugin loading contract.
Verifies directly against %APPDATA%/ingetrazo/plugins/chakkree_tools/
"""

import sys
from pathlib import Path
import os
import pytest

APPDATA_PLUGINS = Path(os.environ["APPDATA"]) / "ingetrazo" / "plugins"

class MockMenu:
    def __init__(self, name: str):
        self.name = name
        self.actions = []

    def addAction(self, label, func):
        self.actions.append(label)

    def addSeparator(self):
        self.actions.append("---")


class MockApp:
    def __init__(self):
        self.menus = []

    def add_menu(self, name: str):
        m = MockMenu(name)
        self.menus.append(m)
        return m


def test_installed_ingetrazo_plugin_structure_and_loading():
    """
    Directly tests IngeTrazo's real plugin directory to guarantee
    IngeTrazo loader finds <plugin_name>/plugin.py and setup(app) without failing.
    """
    plugin_dir = APPDATA_PLUGINS / "chakkree_tools"
    assert plugin_dir.exists(), "chakkree_tools plugin directory must exist in %APPDATA%/ingetrazo/plugins"

    plugin_file = plugin_dir / "plugin.py"
    assert plugin_file.exists(), "plugin.py must be located at the root of chakkree_tools for IngeTrazo loader"

    metadata_file = plugin_dir / "metadata.json"
    assert metadata_file.exists(), "metadata.json must be present in plugin directory"

    if str(APPDATA_PLUGINS) not in sys.path:
        sys.path.insert(0, str(APPDATA_PLUGINS))

    import chakkree_tools.plugin as installed_plugin
    assert hasattr(installed_plugin, "setup"), "Installed plugin must implement setup(app)"

    app = MockApp()
    instance = installed_plugin.setup(app)
    assert instance is not None
    assert len(app.menus) == 1
    assert app.menus[0].name == "Chakkree Tools"

    actions = app.menus[0].actions
    # Verify menu item 4 is removed
    assert "Quick Create Sample Beam (4m)..." not in actions

    # Verify other required menu actions are present
    assert "Create Pile Cap (1-9 Piles)..." in actions
    assert "Create RC Column (4-16 Bars)..." in actions
    assert "Create RC Beam..." in actions
    assert "Create Slab (PS Plank / RC)..." in actions
    assert "Rebar Tools & Details..." in actions
    assert "Grid Lines..." in actions
    assert "Rebar Color Config..." in actions
    assert "QTO Take-off Report..." in actions
    assert "Export Model to .debim..." in actions
    assert "About Chakkree Tools..." in actions
