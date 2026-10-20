"""
Helper script to package Chakkree Tools into a distributable .zip for IngeTrazo Extension Directory
and compute its SHA-256 hash.
"""

import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import zipfile


def package():
    repo_root = Path(__file__).resolve().parent.parent
    src_pkg = repo_root / "chakkree_tools"

    # Read version from metadata.json
    meta_file = src_pkg / "metadata.json"
    version = "0.1.0"
    if meta_file.exists():
        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                meta = json.load(f)
                version = meta.get("version", version)
        except Exception:
            pass

    dist_dir = repo_root / "dist"
    dist_dir.mkdir(exist_ok=True)
    zip_path = dist_dir / f"chakkree_tools-v{version}.zip"

    # Create staging directory to ensure clean root folder 'chakkree_tools'
    with tempfile.TemporaryDirectory() as tmp_dir:
        staging_root = Path(tmp_dir)
        stage_pkg = staging_root / "chakkree_tools"

        # Copy source package
        shutil.copytree(
            src_pkg,
            stage_pkg,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache", "*.git*"),
        )

        # Ensure root __init__.py has clean IngeTrazo loader setup
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

from chakkree_tools.ingetrazo_plugin.plugin import ChakkreeToolsPlugin, setup as _setup

def setup(app):
    return _setup(app)

__version__ = "''' + version + '''"
__author__ = "Chakkree Tiyawongsuwan & PRIDA-TAKON"

__all__ = ["ChakkreeToolsPlugin", "setup", "__version__", "__author__"]
'''
        (stage_pkg / "__init__.py").write_text(init_code, encoding="utf-8")

        # Copy icons to resources if available
        icons_src = src_pkg / "ingetrazo_plugin" / "resources"
        if icons_src.exists():
            shutil.copytree(icons_src, stage_pkg / "resources", dirs_exist_ok=True)

        # Build zip file
        if zip_path.exists():
            zip_path.unlink()

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, _, files in os.walk(stage_pkg):
                for f in files:
                    p = Path(root) / f
                    arcname = p.relative_to(staging_root)
                    zf.write(p, arcname)

    # Calculate SHA-256
    sha256 = hashlib.sha256()
    with open(zip_path, "rb") as f:
        while chunk := f.read(65536):
            sha256.update(chunk)
    hash_str = sha256.hexdigest()

    print("=" * 60)
    print("Package Created Successfully!")
    print(f"Path:    {zip_path}")
    print(f"Size:    {zip_path.stat().st_size:,} bytes")
    print(f"SHA-256: {hash_str}")
    print("=" * 60)
    return zip_path, hash_str, version


if __name__ == "__main__":
    package()
