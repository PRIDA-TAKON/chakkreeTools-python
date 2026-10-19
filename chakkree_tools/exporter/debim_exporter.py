"""
debim Exporter
Exports Chakkree Tools RC elements, grids, and storeys into standard .debim OpenBIM manifests.
Fully compatible with project-debim (debim CLI and debim-ingetrazo).
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import yaml


class DebimExporter:
    """
    Constructs and serializes .debim YAML manifests following schema: "IFC4-Minimal".
    """

    def __init__(
        self,
        project_name: str = "Chakkree Tools Structural Model",
        units: str = "m",
    ):
        self.project_name = project_name
        self.units = units
        self.grids_x: Dict[str, float] = {}
        self.grids_y: Dict[str, float] = {}
        self.storeys: List[Dict[str, Any]] = [
            {
                "id": "ST_01",
                "name": "Level 1",
                "elevation": 0.0,
                "height": 3.5,
            }
        ]
        self.elements: List[Any] = []

    def set_grids(self, axes_x: Dict[str, float], axes_y: Dict[str, float]) -> None:
        """Sets grid coordinate system."""
        self.grids_x = {str(k): float(v) for k, v in axes_x.items()}
        self.grids_y = {str(k): float(v) for k, v in axes_y.items()}

    def add_element(self, element: Any) -> None:
        """Adds a Footing, Column, Beam, or Slab element."""
        self.elements.append(element)

    def to_dict(self) -> Dict[str, Any]:
        """Builds dictionary payload matching debim specification."""
        manifest: Dict[str, Any] = {
            "schema": "IFC4-Minimal",
            "project": {
                "name": self.project_name,
                "units": self.units,
            },
        }

        if self.grids_x or self.grids_y:
            manifest["grids"] = {
                "axes_x": self.grids_x,
                "axes_y": self.grids_y,
            }

        manifest["storeys"] = self.storeys

        serialized_elements: List[Dict[str, Any]] = []
        for elem in self.elements:
            if hasattr(elem, "to_debim_dict"):
                serialized_elements.append(elem.to_debim_dict(storey_id=self.storeys[0]["id"]))
            elif isinstance(elem, dict):
                serialized_elements.append(elem)

        manifest["elements"] = serialized_elements
        return manifest

    def to_yaml(self) -> str:
        """Serializes manifest to clean YAML formatted string."""
        data = self.to_dict()
        return yaml.dump(data, sort_keys=False, allow_unicode=True)

    def save(self, filepath: Union[str, Path]) -> Path:
        """Saves manifest to a .debim or .debim.yaml file."""
        p = Path(filepath)
        p.parent.mkdir(parents=True, exist_ok=True)
        content = self.to_yaml()
        p.write_text(content, encoding="utf-8")
        return p


def export_to_debim(
    elements: List[Any],
    output_path: Union[str, Path],
    project_name: str = "Chakkree Tools Export",
    grids_x: Optional[Dict[str, float]] = None,
    grids_y: Optional[Dict[str, float]] = None,
) -> Path:
    """Convenience helper to export elements directly into a .debim file."""
    exporter = DebimExporter(project_name=project_name)
    if grids_x and grids_y:
        exporter.set_grids(grids_x, grids_y)
    for elem in elements:
        exporter.add_element(elem)
    return exporter.save(output_path)
