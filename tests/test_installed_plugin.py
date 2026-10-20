"""
Tests for live IngeTrazo plugin loading contract.
Verifies directly against %APPDATA%/ingetrazo/plugins/chakkree_tools/
"""

import sys
from pathlib import Path
import os
import pytest
import importlib.util

appdata_val = os.environ.get("APPDATA")
APPDATA_PLUGINS = (Path(appdata_val) / "ingetrazo" / "plugins") if appdata_val else None


class MockMenu:
    def __init__(self, name: str):
        self.name = name
        self.actions = []

    def addAction(self, label, func=None):
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

    def window(self):
        return None

    def flash_status(self, msg: str):
        pass


@pytest.mark.skipif(not APPDATA_PLUGINS or not APPDATA_PLUGINS.exists(), reason="Requires %APPDATA%/ingetrazo/plugins")
def test_installed_ingetrazo_plugin_structure_and_loading():
    """
    Directly tests IngeTrazo's real plugin directory to guarantee
    IngeTrazo loader finds <plugin_name>/plugin.py, __init__.py, and setup(app) without failing.
    """
    plugin_dir = APPDATA_PLUGINS / "chakkree_tools"
    assert plugin_dir.exists(), "chakkree_tools plugin directory must exist in %APPDATA%/ingetrazo/plugins"

    plugin_file = plugin_dir / "plugin.py"
    assert plugin_file.exists(), "plugin.py must be located at the root of chakkree_tools for IngeTrazo loader"

    init_file = plugin_dir / "__init__.py"
    assert init_file.exists(), "__init__.py must be present in plugin directory"

    metadata_file = plugin_dir / "metadata.json"
    assert metadata_file.exists(), "metadata.json must be present in plugin directory"

    # Test loading via root plugin.py
    spec = importlib.util.spec_from_file_location("chakkree_installed_plugin", str(plugin_file))
    assert spec and spec.loader
    installed_plugin = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(installed_plugin)

    assert hasattr(installed_plugin, "setup"), "Installed plugin must implement setup(app)"
    assert hasattr(installed_plugin, "register_plugin"), "Installed plugin must implement register_plugin(app)"

    app = MockApp()
    instance = installed_plugin.setup(app)
    assert instance is not None
    assert len(app.menus) == 1
    assert app.menus[0].name == "Chakkree Tools"

    actions = app.menus[0].actions
    assert "Create Pile Cap (1-9 Piles)..." in actions
    assert "Create RC Column (4-16 Bars)..." in actions
    assert "Create RC Beam..." in actions
    assert "Create Slab (PS Plank / RC)..." in actions
    assert "Show/Hide 3D Rebar Meshes" in actions
    assert "Rebar Tools & Details..." in actions
    assert "Grid Lines..." in actions
    assert "Rebar Color Config..." in actions
    assert "QTO Take-off Report..." in actions
    assert "Export Model to .debim..." in actions
    assert "About Chakkree Tools..." in actions


@pytest.mark.skipif(not APPDATA_PLUGINS or not APPDATA_PLUGINS.exists(), reason="Requires %APPDATA%/ingetrazo/plugins")
def test_installed_ingetrazo_package_discovery_simulation():
    """
    Simulates core.extensions.discover_plugins loading the installed package as a module directory.
    """
    plugin_dir = APPDATA_PLUGINS / "chakkree_tools"
    init_file = plugin_dir / "__init__.py"

    mod_name = "ingetrazo_plugin_chakkree_tools_test"
    spec = importlib.util.spec_from_file_location(
        mod_name,
        str(init_file),
        submodule_search_locations=[str(plugin_dir)],
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)

    assert hasattr(mod, "setup")
    app = MockApp()
    inst = mod.setup(app)
    assert inst is not None
    assert len(app.menus) == 1
    assert "Chakkree Tools" == app.menus[0].name
