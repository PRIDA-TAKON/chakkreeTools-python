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

    # Copy entire chakkree_tools package into destination
    shutil.copytree(src_pkg, dest_dir)

    # Write root __init__.py that ensures sys.path has plugins directory and exports setup
    init_code = '''"""
Chakkree Tools IngeTrazo Extension
Parametric RC Structural Tools & .debim Building-as-Code integration.
"""
import sys
from pathlib import Path

# Ensure plugin directory and parent plugins directory are on sys.path
_pkg_dir = Path(__file__).resolve().parent
_plugins_dir = _pkg_dir.parent
if str(_pkg_dir) not in sys.path:
    sys.path.insert(0, str(_pkg_dir))
if str(_plugins_dir) not in sys.path:
    sys.path.insert(0, str(_plugins_dir))

from chakkree_tools.ingetrazo_plugin.plugin import ChakkreeToolsPlugin, setup

__version__ = "0.1.0"
__author__ = "Chakkree Tiyawongsuwan & PRIDA-TAKON"

__all__ = ["ChakkreeToolsPlugin", "setup", "__version__", "__author__"]
'''
    (dest_dir / "__init__.py").write_text(init_code, encoding="utf-8")

    # Copy metadata.json to dest_dir root for IngeTrazo extension info
    meta_src = src_pkg / "ingetrazo_plugin" / "metadata.json"
    if meta_src.exists():
        shutil.copy2(meta_src, dest_dir / "metadata.json")

    # Also copy resources/icons directly to dest_dir/resources
    icons_src = src_pkg / "ingetrazo_plugin" / "resources"
    if icons_src.exists():
        shutil.copytree(icons_src, dest_dir / "resources", dirs_exist_ok=True)

    print("chakkree_tools successfully installed into IngeTrazo plugins!")


if __name__ == "__main__":
    install()

