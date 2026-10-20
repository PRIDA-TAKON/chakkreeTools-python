"""
chakkree_tools (Python Edition)
Port of Chakkree Tools SketchUp Extension for IngeTrazo and .debim Building-as-Code.
Original Architecture & Parametric RC Models by Chakkree Tiyawongsuwan.
"""

import sys
from pathlib import Path

# Ensure the plugins directory is present in sys.path so package-relative and
# absolute imports work cleanly when loaded by IngeTrazo's dynamic extension loader.
_parent_dir = str(Path(__file__).resolve().parent.parent)
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

_pkg_dir = str(Path(__file__).resolve().parent)
if _pkg_dir not in sys.path:
    sys.path.insert(0, _pkg_dir)

from chakkree_tools.ingetrazo_plugin.plugin import (
    ChakkreeToolsPlugin,
    register_plugin,
    setup,
)

__version__ = "0.1.0"
__author__ = "Chakkree Tiyawongsuwan & PRIDA-TAKON"

__all__ = ["ChakkreeToolsPlugin", "register_plugin", "setup", "__version__", "__author__"]
