"""
Tests for IngeTrazo Plugin Loader Contract.
Simulates exactly how IngeTrazo's core.extensions discovers and loads plugins
in an isolated Python environment (no pre-existing sys.path entries, private module names).
Runs reliably on both CI (Linux/Windows) and local environments.
"""

import importlib.util
import json
import sys
from pathlib import Path
try:
    import pytest
except ImportError:
    pytest = None


REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN_SRC_DIR = REPO_ROOT / "chakkree_tools"


class MockSubMenu:
    def __init__(self, title: str):
        self.title = title
        self.actions = []
        self.separators = 0

    def addAction(self, label: str, callback=None):
        self.actions.append(label)

    def addSeparator(self):
        self.separators += 1


class MockExtensionApp:
    """Simulates IngeTrazo's views.extension_api.ExtensionApp."""
    def __init__(self, key: str = "chakkree_tools"):
        self.key = key
        self.menus = {}
        self.menu_actions = []
        self.flashed_messages = []

    def window(self):
        return None

    def viewport(self):
        return None

    def scene(self):
        return None

    def add_menu(self, title: str):
        if title not in self.menus:
            self.menus[title] = MockSubMenu(title)
        return self.menus[title]

    def add_menu_action(self, text: str, fn=None, shortcut: str = "", tip: str = ""):
        self.menu_actions.append({"text": text, "fn": fn, "shortcut": shortcut, "tip": tip})

    def flash_status(self, msg: str):
        self.flashed_messages.append(msg)


def test_metadata_json_contract():
    """Verify metadata.json exists and conforms to IngeTrazo extension schema."""
    metadata_path = PLUGIN_SRC_DIR / "metadata.json"
    assert metadata_path.exists(), "metadata.json must exist in chakkree_tools root"

    with open(metadata_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    assert meta.get("id") == "chakkree_tools"
    assert "name" in meta and len(meta["name"]) > 0
    assert "version" in meta
    # min_ingetrazo_version must be <= 0.5.7 for compatibility with user installation
    min_ver = meta.get("min_ingetrazo_version", "999.0.0")
    parts = [int(p) for p in min_ver.split(".")]
    assert parts <= [0, 5, 7], f"min_ingetrazo_version {min_ver} must be <= 0.5.7"


def test_isolated_ingetrazo_package_loader_simulation():
    """
    Simulates IngeTrazo core.extensions._import_by_path loading the package
    using a private module name without pre-polluted sys.path.
    """
    init_file = PLUGIN_SRC_DIR / "__init__.py"
    assert init_file.exists(), "__init__.py must exist"

    private_mod_name = "ingetrazo_plugin_chakkree_tools"

    # Remove any cached modules related to chakkree_tools to guarantee clean test
    stashed_modules = {}
    for mod_name in list(sys.modules.keys()):
        if "chakkree" in mod_name:
            stashed_modules[mod_name] = sys.modules.pop(mod_name)

    # Temporarily remove plugin paths from sys.path to simulate isolated load
    orig_sys_path = list(sys.path)
    cleaned_path = [p for p in orig_sys_path if str(REPO_ROOT) not in p and str(PLUGIN_SRC_DIR) not in p]
    sys.path = cleaned_path

    try:
        spec = importlib.util.spec_from_file_location(
            private_mod_name,
            str(init_file),
            submodule_search_locations=[str(PLUGIN_SRC_DIR)],
        )
        assert spec is not None and spec.loader is not None

        mod = importlib.util.module_from_spec(spec)
        sys.modules[private_mod_name] = mod
        spec.loader.exec_module(mod)

        # 1. Module must implement setup and register_plugin
        assert hasattr(mod, "setup"), "Plugin module must export setup(app)"
        assert callable(getattr(mod, "setup"))
        assert hasattr(mod, "register_plugin"), "Plugin module must export register_plugin(app)"
        assert callable(getattr(mod, "register_plugin"))

        # 2. Test setup(app) invocation
        app = MockExtensionApp()
        plugin_instance = mod.setup(app)
        assert plugin_instance is not None

        # Verify menu registration
        assert "Chakkree Tools" in app.menus
        menu = app.menus["Chakkree Tools"]
        required_actions = [
            "Create Pile Cap (1-9 Piles)...",
            "Create RC Column (4-16 Bars)...",
            "Create RC Beam...",
            "Create Slab (PS Plank / RC)...",
            "Show/Hide 3D Rebar Meshes",
            "Rebar Tools & Details...",
            "Grid Lines...",
            "Rebar Color Config...",
            "QTO Take-off Report...",
            "Export Model to .debim...",
            "Live Stream to IngeTrazo (Port 8482)...",
            "About Chakkree Tools...",
        ]
        for act in required_actions:
            assert act in menu.actions, f"Action '{act}' missing from menu"

    finally:
        # Restore sys.path and sys.modules
        sys.path = orig_sys_path
        sys.modules.update(stashed_modules)


def test_isolated_ingetrazo_plugin_file_loader_simulation():
    """
    Simulates IngeTrazo loading plugin.py directly from root.
    """
    plugin_file = PLUGIN_SRC_DIR / "plugin.py"
    assert plugin_file.exists(), "plugin.py must exist in root"

    private_mod_name = "ingetrazo_plugin_file_test"

    spec = importlib.util.spec_from_file_location(
        private_mod_name,
        str(plugin_file),
    )
    assert spec is not None and spec.loader is not None

    mod = importlib.util.module_from_spec(spec)
    sys.modules[private_mod_name] = mod
    spec.loader.exec_module(mod)

    assert hasattr(mod, "setup")
    assert hasattr(mod, "register_plugin")

    app = MockExtensionApp()
    plugin_instance = mod.setup(app)
    assert plugin_instance is not None
    assert "Chakkree Tools" in app.menus


def test_all_toolbar_icons_exist_and_non_empty():
    """Verify that all SVG icon files referenced by toolbar actions exist and are valid."""
    icons_dir = PLUGIN_SRC_DIR / "resources" / "icons"
    assert icons_dir.exists() and icons_dir.is_dir()

    expected_icons = [
        "RebarTools.svg",
        "ToggleRebars.svg",
        "FootingTools.svg",
        "ColumnTools.svg",
        "BeamTools.svg",
        "SlabTools.svg",
        "GridLine.svg",
        "TakeOff.svg",
        "AnalysisTool.svg",
        "ConfigColorRebar.svg",
        "About.svg",
    ]

    for icon_name in expected_icons:
        icon_path = icons_dir / icon_name
        assert icon_path.exists(), f"Icon {icon_name} must exist in {icons_dir}"
        assert icon_path.stat().st_size > 0, f"Icon {icon_name} must not be empty"
