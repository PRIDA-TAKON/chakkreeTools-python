"""
Installer script to deploy chakkree_tools extension into local IngeTrazo plugins directory.
"""

import os
import shutil
import sys
from pathlib import Path


def install():
    repo_root = Path(__file__).resolve().parent.parent
    src_pkg = repo_root / "chakkree_tools"

    appdata = os.environ.get("APPDATA")
    if not appdata:
        print("Error: APPDATA environment variable not found.")
        sys.exit(1)

    plugins_dir = Path(appdata) / "ingetrazo" / "plugins"
    dest_dir = plugins_dir / "chakkree_tools"

    print(f"Installing chakkree_tools extension to: {dest_dir}")
    if dest_dir.exists():
        shutil.rmtree(dest_dir)

    dest_dir.mkdir(parents=True, exist_ok=True)

    # Copy entire chakkree_tools package into destination
    shutil.copytree(src_pkg, dest_dir / "chakkree_tools", dirs_exist_ok=True)

    # Copy metadata.json and plugin.py to root of plugin directory for IngeTrazo discovery
    meta_src = src_pkg / "ingetrazo_plugin" / "metadata.json"
    plugin_src = src_pkg / "ingetrazo_plugin" / "plugin.py"

    shutil.copy2(meta_src, dest_dir / "metadata.json")

    # Create root plugin.py that exports Plugin
    root_plugin_code = """\"\"\"
IngeTrazo Plugin Entry Point for chakkree_tools.
\"\"\"
import sys
from pathlib import Path

# Ensure plugin directory is on path
plugin_dir = Path(__file__).resolve().parent
if str(plugin_dir) not in sys.path:
    sys.path.insert(0, str(plugin_dir))

from chakkree_tools.ingetrazo_plugin.plugin import ChakkreeToolsPlugin

# IngeTrazo plugin factory
Plugin = ChakkreeToolsPlugin
"""
    (dest_dir / "plugin.py").write_text(root_plugin_code, encoding="utf-8")
    (dest_dir / "__init__.py").write_text("", encoding="utf-8")

    # Copy icons
    icons_src = src_pkg / "ingetrazo_plugin" / "resources"
    if icons_src.exists():
        shutil.copytree(icons_src, dest_dir / "resources", dirs_exist_ok=True)

    print("chakkree_tools successfully installed into IngeTrazo plugins!")


if __name__ == "__main__":
    install()
