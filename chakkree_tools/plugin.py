"""
IngeTrazo Plugin Entry Point for Chakkree Tools
Direct bridge to chakkree_tools.ingetrazo_plugin.plugin
"""
import sys
from pathlib import Path

# Ensure the plugins directory is in sys.path so 'chakkree_tools' package imports resolve
_parent_dir = str(Path(__file__).resolve().parent.parent)
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

_pkg_dir = str(Path(__file__).resolve().parent)
if _pkg_dir not in sys.path:
    sys.path.insert(0, _pkg_dir)

from chakkree_tools.ingetrazo_plugin.plugin import (
    ChakkreeToolsPlugin,
    setup,
    register_plugin,
)

__all__ = ["ChakkreeToolsPlugin", "setup", "register_plugin"]
