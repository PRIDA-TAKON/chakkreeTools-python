"""
CRS Parser (Chakkree Rebar Script Parser)
Interprets .crs parametric scripts into 3D geometric entities and rebar specifications.
"""

import math
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union


@dataclass
class CRSEntity:
    name: str
    translation: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    rotation: Tuple[Tuple[float, float, float], Tuple[float, float, float], float] = (
        (0.0, 0.0, 0.0),
        (0.0, 0.0, 1.0),
        0.0,
    )


@dataclass
class CRSBox(CRSEntity):
    dimensions: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    material: str = "concrete"
    color: str = "Bisque"
    opacity: float = 1.0


@dataclass
class CRSRebar(CRSEntity):
    diameter: float = 0.012  # in meters
    shape_code: int = 21
    dimensions: List[float] = field(default_factory=list)
    spacing: float = 0.0
    count: int = 1


class CRSParser:
    """
    Parser and execution engine for Chakkree Rebar Script (.crs).
    Converts dimensions into SI standard meters (m).
    """

    def __init__(self, unit: str = "m"):
        self.unit = unit
        self.variables: Dict[str, float] = {
            "factor_Db": 4.0,
            "factor_Lh": 6.0,
            "factor_edge": 1.5,
        }
        self.entities: Dict[str, CRSEntity] = {}
        self.ordered_entities: List[CRSEntity] = []

    def _eval_expr(self, expr_str: str) -> float:
        """Evaluates mathematical expression with variables and units."""
        s = expr_str.strip()
        if not s:
            return 0.0

        # Replace Ruby-style string interpolation or symbols
        s = s.replace("'", "").replace('"', "")
        if s.endswith(".to_l"):
            s = s[:-5]

        # Convert units to meters
        # e.g., 4000.mm -> 4.0, 4.m -> 4.0, 10.cm -> 0.1
        def unit_repl(match):
            val = float(match.group(1))
            u = match.group(2).lower()
            if u == "mm":
                return str(val * 0.001)
            elif u == "cm":
                return str(val * 0.01)
            elif u == "m":
                return str(val)
            return str(val)

        s = re.sub(r'(\d+(?:\.\d+)?)\.(mm|cm|m)', unit_repl, s)

        # Replace variables: $var or var
        # Sort variables by length descending to prevent substring collisions
        sorted_vars = sorted(self.variables.keys(), key=len, reverse=True)
        for var_name in sorted_vars:
            val = self.variables[var_name]
            # Replace $var_name
            s = re.sub(r'\$' + re.escape(var_name) + r'\b', str(val), s)
            # Replace standalone var_name (if not preceded by letter or $)
            s = re.sub(r'(?<![A-Za-z0-9_])' + re.escape(var_name) + r'\b', str(val), s)

        # Remove any leftover invalid tokens for safe eval
        # Only allow numbers, math operators, parens, decimal points
        clean = re.sub(r'[^0-9\.\+\-\*\/\(\)\s]', '', s)
        try:
            return float(eval(clean, {"__builtins__": None, "math": math}, {}))
        except Exception:
            return 0.0

    def parse_vector3(self, s: str) -> Tuple[float, float, float]:
        """Parses a [x, y, z] or (x, y, z) vector."""
        s = s.strip().lstrip("[").rstrip("]").lstrip("(").rstrip(")")
        parts = [p.strip() for p in s.split(",") if p.strip()]
        if len(parts) >= 3:
            return (self._eval_expr(parts[0]), self._eval_expr(parts[1]), self._eval_expr(parts[2]))
        elif len(parts) == 2:
            return (self._eval_expr(parts[0]), self._eval_expr(parts[1]), 0.0)
        elif len(parts) == 1:
            return (self._eval_expr(parts[0]), 0.0, 0.0)
        return (0.0, 0.0, 0.0)

    def parse_script(self, script_text: str, initial_vars: Optional[Dict[str, float]] = None) -> List[CRSEntity]:
        """
        Parses a .crs script and executes its instructions.
        """
        if initial_vars:
            self.variables.update(initial_vars)

        lines = script_text.splitlines()
        for raw_line in lines:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue

            # Variable assignment: var x = ... or set x = ...
            m_var = re.match(r'^(?:var|set)\s+([A-Za-z0-9_]+)\s*=\s*(.+)$', line, re.IGNORECASE)
            if m_var:
                vname = m_var.group(1)
                vexpr = m_var.group(2)
                self.variables[vname] = self._eval_expr(vexpr)
                continue

            # Box command: Box 'name', [dx, dy, dz], ['material', 'color', alpha]
            m_box = re.match(r'^(?:Box|box)\s+[\'"]?([^\'"]+)[\'"]?\s*,\s*\[([^\]]+)\](?:\s*,\s*\[([^\]]*)\])?', line, re.IGNORECASE)
            if m_box:
                name = m_box.group(1).strip()
                dim_str = m_box.group(2)
                props_str = m_box.group(3) or ""

                dims = self.parse_vector3(dim_str)
                mat, col, alpha = "concrete", "Bisque", 1.0
                if props_str:
                    prop_items = [p.strip().strip("'\"") for p in props_str.split(",")]
                    if len(prop_items) >= 1 and prop_items[0]:
                        mat = prop_items[0]
                    if len(prop_items) >= 2 and prop_items[1]:
                        col = prop_items[1]
                    if len(prop_items) >= 3 and prop_items[2]:
                        try:
                            alpha = float(prop_items[2])
                        except ValueError:
                            pass

                box = CRSBox(name=name, dimensions=dims, material=mat, color=col, opacity=alpha)
                self.entities[name] = box
                self.ordered_entities.append(box)
                continue

            # Rebar command: rebar 'name', dia, shape_code, [dims...], default, [S, count, s]
            m_rebar = re.match(r'^(?:rebar|Rebar)\s+[\'"]?([^\'"]+)[\'"]?\s*,\s*([^,]+)\s*,\s*([^,]+)\s*,\s*\[([^\]]+)\](?:\s*,\s*(.+))?', line, re.IGNORECASE)
            if m_rebar:
                name = m_rebar.group(1).strip()
                dia_str = m_rebar.group(2)
                shape_str = m_rebar.group(3)
                dims_str = m_rebar.group(4)
                extra_str = m_rebar.group(5) or ""

                dia = self._eval_expr(dia_str)
                try:
                    shape_code = int(self._eval_expr(shape_str))
                except (ValueError, TypeError):
                    shape_code = 21

                rebar_dims = [self._eval_expr(p) for p in dims_str.split(",") if p.strip()]

                count = 1
                spacing = 0.0
                if extra_str:
                    # extra parameters e.g., default , S , $n1 , $s
                    parts = [p.strip() for p in extra_str.split(",")]
                    for i, p in enumerate(parts):
                        if p.upper() == "S" and i + 2 < len(parts):
                            count = int(self._eval_expr(parts[i + 1]))
                            spacing = self._eval_expr(parts[i + 2])

                rebar = CRSRebar(
                    name=name,
                    diameter=dia,
                    shape_code=shape_code,
                    dimensions=rebar_dims,
                    count=count,
                    spacing=spacing,
                )
                self.entities[name] = rebar
                self.ordered_entities.append(rebar)
                continue

            # Translate: tran 'name', [dx, dy, dz] or Translate 'name', [dx, dy, dz]
            m_tran = re.match(r'^(?:tran|Translate)\s+[\'"]?([^\'"]+)[\'"]?\s*,\s*\[([^\]]+)\]', line, re.IGNORECASE)
            if m_tran:
                name = m_tran.group(1).strip()
                vec = self.parse_vector3(m_tran.group(2))
                if name in self.entities:
                    cur = self.entities[name].translation
                    self.entities[name].translation = (
                        round(cur[0] + vec[0], 6),
                        round(cur[1] + vec[1], 6),
                        round(cur[2] + vec[2], 6),
                    )
                continue

            # Rotate: rot 'name', [ox, oy, oz], [ax, ay, az], angle
            m_rot = re.match(r'^(?:rot|Rotate)\s+[\'"]?([^\'"]+)[\'"]?\s*,\s*\[([^\]]+)\]\s*,\s*\[([^\]]+)\]\s*,\s*(.+)', line, re.IGNORECASE)
            if m_rot:
                name = m_rot.group(1).strip()
                orig = self.parse_vector3(m_rot.group(2))
                axis = self.parse_vector3(m_rot.group(3))
                angle = self._eval_expr(m_rot.group(4))
                if name in self.entities:
                    self.entities[name].rotation = (orig, axis, angle)
                continue

            # Copy: copy 'name', count, [dx, dy, dz]
            m_copy = re.match(r'^(?:copy|Copy)\s+[\'"]?([^\'"]+)[\'"]?\s*,\s*(\d+)\s*,\s*\[([^\]]+)\]', line, re.IGNORECASE)
            if m_copy:
                name = m_copy.group(1).strip()
                count = int(m_copy.group(2))
                vec = self.parse_vector3(m_copy.group(3))
                if name in self.entities:
                    base_ent = self.entities[name]
                    for c_idx in range(1, count + 1):
                        clone_name = f"{name}_copy_{c_idx}"
                        cur_t = base_ent.translation
                        new_t = (
                            round(cur_t[0] + vec[0] * c_idx, 6),
                            round(cur_t[1] + vec[1] * c_idx, 6),
                            round(cur_t[2] + vec[2] * c_idx, 6),
                        )
                        if isinstance(base_ent, CRSBox):
                            c_ent = CRSBox(
                                name=clone_name,
                                translation=new_t,
                                rotation=base_ent.rotation,
                                dimensions=base_ent.dimensions,
                                material=base_ent.material,
                                color=base_ent.color,
                                opacity=base_ent.opacity,
                            )
                        elif isinstance(base_ent, CRSRebar):
                            c_ent = CRSRebar(
                                name=clone_name,
                                translation=new_t,
                                rotation=base_ent.rotation,
                                diameter=base_ent.diameter,
                                shape_code=base_ent.shape_code,
                                dimensions=list(base_ent.dimensions),
                                spacing=base_ent.spacing,
                                count=base_ent.count,
                            )
                        else:
                            continue
                        self.entities[clone_name] = c_ent
                        self.ordered_entities.append(c_ent)
                continue

        return self.ordered_entities
