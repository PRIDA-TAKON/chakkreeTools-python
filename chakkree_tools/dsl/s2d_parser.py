"""
S2D Parser (Structure 2D Parser)
Parses .s2d parametric 2D cross section and geometry scripts.
"""

import json
import math
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union


@dataclass
class InputBoxField:
    var_name: str
    label: str
    default_value: Any
    choices: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "var_name": self.var_name,
            "label": self.label,
            "default": self.default_value,
            "choices": self.choices,
        }


@dataclass
class S2DEntity:
    type: str
    properties: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "properties": self.properties,
        }


@dataclass
class S2DParseResult:
    title: str = ""
    break_if_not: str = ""
    variables: Dict[str, Any] = field(default_factory=dict)
    inputs: List[InputBoxField] = field(default_factory=list)
    attributes: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    entities: List[S2DEntity] = field(default_factory=list)
    bounding_box: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "break_if_not": self.break_if_not,
            "variables": self.variables,
            "inputs": [field.to_dict() for field in self.inputs],
            "attributes": self.attributes,
            "entities": [entity.to_dict() for entity in self.entities],
            "bounding_box": self.bounding_box,
        }


def parse_unit_value(val: Any) -> Any:
    """Parses string with unit suffixes (e.g. '220mm', '0.5m') to float meters."""
    if isinstance(val, (int, float)):
        return float(val)
    if not isinstance(val, str):
        return val

    s = val.strip().strip("'\"")
    # Check if number with unit
    m = re.match(r'^([+-]?\d+(?:\.\d+)?)\s*(mm|cm|m)?$', s, re.IGNORECASE)
    if m:
        num = float(m.group(1))
        unit = (m.group(2) or "").lower()
        if unit == "mm":
            return num * 0.001
        elif unit == "cm":
            return num * 0.01
        elif unit == "m":
            return num
        return num
    return s


class S2DParser:
    """
    Parser and interpreter for Structure 2D (.s2d) scripts.
    Converts dimensions into standard SI meters (m).
    """

    def __init__(self, unit: str = "m"):
        self.unit = unit
        self.variables: Dict[str, Any] = {}
        self.attributes: Dict[str, Dict[str, Any]] = {}
        self.inputs: List[InputBoxField] = []
        self.entities: List[S2DEntity] = []
        self.title: str = ""
        self.break_if_not: str = ""

    def _parse_unit_repl(self, match: re.Match) -> str:
        val = float(match.group(1))
        u = match.group(2).lower()
        if u == "mm":
            return str(val * 0.001)
        elif u == "cm":
            return str(val * 0.01)
        elif u == "m":
            return str(val)
        return str(val)

    def _eval_expr(self, expr_str: Any) -> Any:
        """Evaluates mathematical expression, unit suffixes, and variable references."""
        if not isinstance(expr_str, str):
            return expr_str

        s = expr_str.strip()
        if not s:
            return ""

        # Check boolean literals
        if s.lower() == "true":
            return True
        if s.lower() == "false":
            return False

        # Check if list expression [ ... ]
        if s.startswith("[") and s.endswith("]"):
            inner = s[1:-1].strip()
            if not inner:
                return []
            items = self._split_top_level_args(inner)
            return [self._eval_expr(item) for item in items]

        # Replace .degrees e.g. 90.degrees -> 90
        s = re.sub(r'(\d+(?:\.\d+)?)\.degrees', r'\1', s, flags=re.IGNORECASE)

        # Handle .to_mm.round and .to_mm on variable/paren expressions
        def repl_to_mm_round(m):
            inner = m.group(1).strip("()")
            val = self._eval_expr(inner)
            num = parse_unit_value(val)
            if isinstance(num, (int, float)):
                return str(int(round(num * 1000.0)))
            return str(val)

        s = re.sub(r'(\([^\)]+\)|\$?[A-Za-z0-9_]+)\.to_mm\.round', repl_to_mm_round, s)

        def repl_to_mm(m):
            inner = m.group(1).strip("()")
            val = self._eval_expr(inner)
            num = parse_unit_value(val)
            if isinstance(num, (int, float)):
                return str(num * 1000.0)
            return str(val)

        s = re.sub(r'(\([^\)]+\)|\$?[A-Za-z0-9_]+)\.to_mm', repl_to_mm, s)

        # Units conversion e.g. 500.mm -> 0.5
        s = re.sub(r'(\d+(?:\.\d+)?)\.(mm|cm|m)', self._parse_unit_repl, s, flags=re.IGNORECASE)

        # Replace .to_l
        if s.endswith(".to_l"):
            base_val = self._eval_expr(s[:-5])
            if isinstance(base_val, str):
                return parse_unit_value(base_val)
            elif isinstance(base_val, (int, float)):
                return float(base_val)
            return base_val

        # Handle sprintf % formatting: "%dmm" % expr or "R%d" % expr
        m_fmt = re.match(r'^["\']([^"\']+)["\']\s*%\s*\((.+)\)$', s)
        if not m_fmt:
            m_fmt = re.match(r'^["\']([^"\']+)["\']\s*%\s*(.+)$', s)
        if m_fmt:
            fmt_str = m_fmt.group(1)
            fmt_arg_expr = m_fmt.group(2)
            fmt_arg = self._eval_expr(fmt_arg_expr)
            try:
                if isinstance(fmt_arg, list):
                    return fmt_str % tuple(fmt_arg)
                return fmt_str % (fmt_arg,)
            except Exception:
                return fmt_str

        # Handle string concatenation '+' e.g. "8-DB" + expr + "มม"
        if "+" in s and ("\"" in s or "'" in s or ".to_s" in s):
            parts = s.split("+")
            eval_parts = []
            is_string_concat = False
            for p in parts:
                p_eval = self._eval_expr(p)
                if isinstance(p_eval, str):
                    is_string_concat = True
                eval_parts.append(p_eval)
            if is_string_concat:
                return "".join(str(p) for p in eval_parts)

        # Replace variables: $var or var
        sorted_vars = sorted(self.variables.keys(), key=len, reverse=True)

        # Handle .to_mm.round on variable e.g. $Dp.to_mm.round or Dp.to_mm.round
        for vname in sorted_vars:
            val = self.variables[vname]
            num_val = parse_unit_value(val) if isinstance(val, str) else val
            if isinstance(num_val, (int, float)):
                # $var.to_mm.round or var.to_mm.round
                s = re.sub(
                    r'(\$?' + re.escape(vname) + r')\.to_mm\.round',
                    str(int(round(num_val * 1000.0))),
                    s
                )
                # $var.to_mm or var.to_mm
                s = re.sub(
                    r'(\$?' + re.escape(vname) + r')\.to_mm',
                    str(num_val * 1000.0),
                    s
                )
                # $var.to_s or var.to_s
                s = re.sub(
                    r'(\$?' + re.escape(vname) + r')\.to_s',
                    str(num_val),
                    s
                )
                # $var.abs or var.abs
                s = re.sub(
                    r'(\$?' + re.escape(vname) + r')\.abs',
                    str(abs(num_val)),
                    s
                )
            elif isinstance(val, str):
                s = re.sub(
                    r'(\$?' + re.escape(vname) + r')\.to_s',
                    val,
                    s
                )

        # General variable replacement
        for vname in sorted_vars:
            val = self.variables[vname]
            val_rep = str(val) if not isinstance(val, str) else val
            # Replace $vname
            s = re.sub(r'\$' + re.escape(vname) + r'\b', str(val), s)
            # Replace standalone vname if not inside quotes or part of identifier
            s = re.sub(r'(?<![A-Za-z0-9_\'"])' + re.escape(vname) + r'(?![A-Za-z0-9_\'"])', str(val), s)

        # Evaluate .abs on numeric expressions e.g. ($y4 - $y1).abs or (expr).abs
        m_abs = re.search(r'\(([^\)]+)\)\.abs', s)
        if m_abs:
            inner_val = self._eval_expr(m_abs.group(1))
            if isinstance(inner_val, (int, float)):
                s = s[:m_abs.start()] + str(abs(inner_val)) + s[m_abs.end():]

        # Check if single quoted or double quoted string literal
        s_clean = s.strip()
        if (s_clean.startswith("'") and s_clean.endswith("'")) or (s_clean.startswith('"') and s_clean.endswith('"')):
            return s_clean[1:-1]

        # Safe evaluation of mathematical expressions
        try:
            # Allow basic math operations
            clean = re.sub(r'[^0-9\.\+\-\*\/\(\)\s]', '', s)
            if clean.strip():
                res = float(eval(clean, {"__builtins__": None, "math": math}, {}))
                return int(res) if res.is_integer() else res
        except Exception:
            pass

        return s_clean.strip("'\"")

    def _split_top_level_args(self, s: str) -> List[str]:
        """Splits comma-separated arguments while respecting quotes and brackets."""
        args = []
        current = []
        depth = 0
        in_quote = None
        i = 0
        while i < len(s):
            char = s[i]
            if in_quote:
                current.append(char)
                if char == in_quote and (i == 0 or s[i - 1] != '\\'):
                    in_quote = None
            else:
                if char in ("'", '"'):
                    in_quote = char
                    current.append(char)
                elif char in ('[', '(', '{'):
                    depth += 1
                    current.append(char)
                elif char in (']', ')', '}'):
                    depth -= 1
                    current.append(char)
                elif char == ',' and depth == 0:
                    args.append("".join(current).strip())
                    current = []
                else:
                    current.append(char)
            i += 1
        if current:
            args.append("".join(current).strip())
        return args

    def parse_script(
        self,
        script_text: str,
        initial_vars: Optional[Dict[str, Any]] = None,
        attributes: Optional[Dict[str, Dict[str, Any]]] = None,
        inputs: Optional[Dict[str, Any]] = None,
    ) -> S2DParseResult:
        """
        Parses an .s2d script and executes its instructions.
        """
        self.variables = {}
        if initial_vars:
            for k, v in initial_vars.items():
                self.variables[k] = parse_unit_value(v)

        self.attributes = attributes or {}
        self.inputs = []
        self.entities = []
        self.title = ""
        self.break_if_not = ""

        # Pre-process lines to combine multiline statements ended with '\' and strip inline comments
        raw_lines = script_text.splitlines()
        lines = []
        buf = ""
        for line in raw_lines:
            stripped = self._strip_inline_comment(line.strip())
            if not stripped:
                continue
            if stripped.endswith("\\"):
                buf += stripped[:-1] + " "
            else:
                buf += stripped
                lines.append(buf.strip())
                buf = ""
        if buf.strip():
            lines.append(buf.strip())

        self._execute_block(lines, inputs=inputs or {})
        bbox = self.compute_bounding_box()

        return S2DParseResult(
            title=self.title,
            break_if_not=self.break_if_not,
            variables=dict(self.variables),
            inputs=list(self.inputs),
            attributes=dict(self.attributes),
            entities=list(self.entities),
            bounding_box=bbox,
        )

    def _strip_inline_comment(self, line: str) -> str:
        """Strips inline '#' comment unless '#' is inside quotes."""
        in_quote = None
        for i, char in enumerate(line):
            if in_quote:
                if char == in_quote and (i == 0 or line[i - 1] != '\\'):
                    in_quote = None
            else:
                if char in ("'", '"'):
                    in_quote = char
                elif char == '#':
                    return line[:i].rstrip()
        return line.strip()

    def _execute_block(self, lines: List[str], inputs: Dict[str, Any]) -> None:
        idx = 0
        while idx < len(lines):
            line = self._strip_inline_comment(lines[idx].strip())
            idx += 1

            if not line:
                continue

            # Command: break_IfNOT "text"
            m_break = re.match(r'^break_IfNOT\s+["\']?([^"\']+)["\']?$', line, re.IGNORECASE)
            if m_break:
                self.break_if_not = m_break.group(1).strip()
                continue

            # Variable assignment: var x = ... or set x = ...
            m_var = re.match(r'^(?:var|set)\s+([A-Za-z0-9_]+)\s*=\s*(.+)$', line, re.IGNORECASE)
            if m_var:
                vname = m_var.group(1)
                vexpr = m_var.group(2)
                eval_val = self._eval_expr(vexpr)
                self.variables[vname] = parse_unit_value(eval_val)
                continue

            # Command: get_attribute "dict_name", "attr_name", "type"
            m_get_attr = re.match(r'^get_attribute\s+["\']?([^"\']+)["\']?\s*,\s*["\']?([^"\']+)["\']?\s*,\s*["\']?([^"\']+)["\']?$', line, re.IGNORECASE)
            if m_get_attr:
                dict_name = m_get_attr.group(1).strip()
                attr_name = m_get_attr.group(2).strip()
                attr_val = self.attributes.get(dict_name, {}).get(attr_name)
                if attr_val is not None:
                    self.variables[attr_name] = attr_val
                    if attr_name == "data":
                        # If JSON data object, load properties into variables
                        data_dict = {}
                        if isinstance(attr_val, str):
                            try:
                                data_dict = json.loads(attr_val)
                            except Exception:
                                pass
                        elif isinstance(attr_val, dict):
                            data_dict = attr_val
                        for k, v in data_dict.items():
                            self.variables[k] = parse_unit_value(v)
                continue

            # Command: set_attribute "dict_name", "attr_name", "type", expr
            m_set_attr = re.match(r'^set_attribute\s+["\']?([^"\']+)["\']?\s*,\s*["\']?([^"\']+)["\']?\s*,\s*["\']?([^"\']+)["\']?\s*,\s*(.+)$', line, re.IGNORECASE)
            if m_set_attr:
                dict_name = m_set_attr.group(1).strip()
                attr_name = m_set_attr.group(2).strip()
                attr_type = m_set_attr.group(3).strip()
                attr_expr = m_set_attr.group(4).strip()
                eval_val = self._eval_expr(attr_expr)

                if dict_name not in self.attributes:
                    self.attributes[dict_name] = {}
                self.attributes[dict_name][attr_name] = eval_val
                continue

            # Command: inputbox 'title', [labels], [initial_values], [choices], [var_names]
            if line.lower().startswith("inputbox"):
                args_str = line[8:].strip()
                args = self._split_top_level_args(args_str)
                if len(args) >= 5:
                    self.title = str(self._eval_expr(args[0]))
                    labels = self._eval_expr(args[1])
                    initial_vals = self._eval_expr(args[2])
                    choices = self._eval_expr(args[3])
                    var_names = self._eval_expr(args[4])

                    if isinstance(var_names, list):
                        for i, vname in enumerate(var_names):
                            lbl = labels[i] if isinstance(labels, list) and i < len(labels) else ""
                            init_val = initial_vals[i] if isinstance(initial_vals, list) and i < len(initial_vals) else ""
                            choice_raw = choices[i] if isinstance(choices, list) and i < len(choices) else ""
                            choice_list = [c.strip() for c in str(choice_raw).split("|") if c.strip()] if choice_raw else []

                            # Record prompt field
                            field = InputBoxField(
                                var_name=str(vname),
                                label=str(lbl),
                                default_value=init_val,
                                choices=choice_list,
                            )
                            self.inputs.append(field)

                            # If user supplied input override, set variable
                            if str(vname) in inputs:
                                user_val = inputs[str(vname)]
                                self.variables[str(vname)] = parse_unit_value(user_val)
                            else:
                                self.variables[str(vname)] = parse_unit_value(init_val)
                continue

            # Command: if <condition>
            m_if = re.match(r'^if\s+(.+)$', line, re.IGNORECASE)
            if m_if:
                cond_expr = m_if.group(1).strip()
                # Find matching end / else
                if_block = []
                else_block = []
                current_target = if_block
                nesting = 1
                while idx < len(lines):
                    next_line = lines[idx].strip()
                    idx += 1
                    if re.match(r'^if\s+', next_line, re.IGNORECASE):
                        nesting += 1
                        current_target.append(next_line)
                    elif re.match(r'^end\b', next_line, re.IGNORECASE):
                        nesting -= 1
                        if nesting == 0:
                            break
                        current_target.append(next_line)
                    elif re.match(r'^else\b', next_line, re.IGNORECASE) and nesting == 1:
                        current_target = else_block
                    else:
                        current_target.append(next_line)

                # Evaluate condition
                cond_result = self._eval_condition(cond_expr)
                if cond_result:
                    self._execute_block(if_block, inputs)
                else:
                    self._execute_block(else_block, inputs)
                continue

            # Command: Repeat <count>
            m_repeat = re.match(r'^repeat\s+(.+)$', line, re.IGNORECASE)
            if m_repeat:
                count_expr = m_repeat.group(1).strip()
                count_val = int(self._eval_expr(count_expr))
                repeat_block = []
                nesting = 1
                while idx < len(lines):
                    next_line = lines[idx].strip()
                    idx += 1
                    if re.match(r'^repeat\s+', next_line, re.IGNORECASE):
                        nesting += 1
                        repeat_block.append(next_line)
                    elif re.match(r'^end\b', next_line, re.IGNORECASE):
                        nesting -= 1
                        if nesting == 0:
                            break
                        repeat_block.append(next_line)
                    else:
                        repeat_block.append(next_line)

                for _ in range(count_val):
                    self._execute_block(repeat_block, inputs)
                continue

            # 2D Geometry drawing entities parsing:
            self._parse_entity_line(line)

    def _eval_condition(self, cond_expr: str) -> bool:
        """Evaluates condition expression for if statements."""
        # Handle equality check "str1" == "str2" or var == var
        m_eq = re.match(r'^(.*?)\s*(==|!=|>|<|>=|<=)\s*(.*)$', cond_expr)
        if m_eq:
            left_str = m_eq.group(1).strip()
            op = m_eq.group(2)
            right_str = m_eq.group(3).strip()

            left_val = self._eval_expr(left_str)
            right_val = self._eval_expr(right_str)

            if isinstance(left_val, str):
                left_val = left_val.strip("'\"")
            if isinstance(right_val, str):
                right_val = right_val.strip("'\"")

            if op == "==":
                return left_val == right_val
            elif op == "!=":
                return left_val != right_val
            elif op == ">":
                return left_val > right_val
            elif op == "<":
                return left_val < right_val
            elif op == ">=":
                return left_val >= right_val
            elif op == "<=":
                return left_val <= right_val

        val = self._eval_expr(cond_expr)
        return bool(val)

    def _parse_entity_line(self, line: str) -> None:
        """Parses 2D geometry drawing primitive commands."""
        parts = self._split_top_level_args(line)
        if not parts:
            return

        cmd = parts[0].split()[0].lower() if parts[0] else ""

        if cmd == "rect":
            m = re.match(r'^rect\s+(.+)$', line, re.IGNORECASE)
            if m:
                args = [self._eval_expr(a) for a in self._split_top_level_args(m.group(1))]
                if len(args) >= 4:
                    self.entities.append(
                        S2DEntity(
                            type="rect",
                            properties={
                                "x": float(parse_unit_value(args[0])),
                                "y": float(parse_unit_value(args[1])),
                                "width": float(parse_unit_value(args[2])),
                                "height": float(parse_unit_value(args[3])),
                                "color": args[4] if len(args) > 4 else "black",
                            },
                        )
                    )

        elif cmd == "roundrect":
            m = re.match(r'^roundrect\s+(.+)$', line, re.IGNORECASE)
            if m:
                args = [self._eval_expr(a) for a in self._split_top_level_args(m.group(1))]
                if len(args) >= 5:
                    self.entities.append(
                        S2DEntity(
                            type="roundrect",
                            properties={
                                "x": float(parse_unit_value(args[0])),
                                "y": float(parse_unit_value(args[1])),
                                "width": float(parse_unit_value(args[2])),
                                "height": float(parse_unit_value(args[3])),
                                "radius": float(parse_unit_value(args[4])),
                            },
                        )
                    )

        elif cmd in ("line", "cline"):
            m = re.match(r'^(?:line|cline)\s+(.+)$', line, re.IGNORECASE)
            if m:
                args = [self._eval_expr(a) for a in self._split_top_level_args(m.group(1))]
                if len(args) >= 4:
                    self.entities.append(
                        S2DEntity(
                            type=cmd,
                            properties={
                                "x1": float(parse_unit_value(args[0])),
                                "y1": float(parse_unit_value(args[1])),
                                "x2": float(parse_unit_value(args[2])),
                                "y2": float(parse_unit_value(args[3])),
                            },
                        )
                    )

        elif cmd == "circle":
            m = re.match(r'^circle\s+(.+)$', line, re.IGNORECASE)
            if m:
                args = [self._eval_expr(a) for a in self._split_top_level_args(m.group(1))]
                if len(args) >= 3:
                    self.entities.append(
                        S2DEntity(
                            type="circle",
                            properties={
                                "cx": float(parse_unit_value(args[0])),
                                "cy": float(parse_unit_value(args[1])),
                                "radius": float(parse_unit_value(args[2])),
                                "color": args[3] if len(args) > 3 else "black",
                            },
                        )
                    )

        elif cmd in ("dim", "dimdash"):
            m = re.match(r'^(?:dim|dimdash)\s+(.+)$', line, re.IGNORECASE)
            if m:
                args = [self._eval_expr(a) for a in self._split_top_level_args(m.group(1))]
                if len(args) >= 5:
                    self.entities.append(
                        S2DEntity(
                            type="dim",
                            properties={
                                "x": float(parse_unit_value(args[0])),
                                "y": float(parse_unit_value(args[1])),
                                "length": float(parse_unit_value(args[2])),
                                "offset": float(parse_unit_value(args[3])),
                                "text": str(args[4]),
                                "font_size": float(parse_unit_value(args[5])) if len(args) > 5 else 0.05,
                                "angle": float(parse_unit_value(args[6])) if len(args) > 6 else 0.0,
                            },
                        )
                    )

        elif cmd == "pilesection":
            m = re.match(r'^pilesection\s+(.+)$', line, re.IGNORECASE)
            if m:
                args = [self._eval_expr(a) for a in self._split_top_level_args(m.group(1))]
                if len(args) >= 3:
                    self.entities.append(
                        S2DEntity(
                            type="pilesection",
                            properties={
                                "x": float(parse_unit_value(args[0])),
                                "y": float(parse_unit_value(args[1])),
                                "label": str(args[2]),
                            },
                        )
                    )

        elif cmd == "rebar":
            m = re.match(r'^rebar\s+(.+)$', line, re.IGNORECASE)
            if m:
                args = [self._eval_expr(a) for a in self._split_top_level_args(m.group(1))]
                if len(args) >= 4:
                    self.entities.append(
                        S2DEntity(
                            type="rebar",
                            properties={
                                "x": float(parse_unit_value(args[0])),
                                "y": float(parse_unit_value(args[1])),
                                "shape_code": str(args[2]),
                                "dims": args[3] if isinstance(args[3], list) else [args[3]],
                                "diameter": float(parse_unit_value(args[4])) if len(args) > 4 else 0.012,
                            },
                        )
                    )

        elif cmd == "grid":
            m = re.match(r'^grid\s+(.+)$', line, re.IGNORECASE)
            if m:
                args = [self._eval_expr(a) for a in self._split_top_level_args(m.group(1))]
                if len(args) >= 7:
                    self.entities.append(
                        S2DEntity(
                            type="grid",
                            properties={
                                "x": float(parse_unit_value(args[0])),
                                "y": float(parse_unit_value(args[1])),
                                "label": str(args[2]),
                                "bubble_size": float(parse_unit_value(args[3])),
                                "direction": str(args[5]),
                                "length": float(parse_unit_value(args[6])),
                            },
                        )
                    )

        elif cmd in ("text", "name", "layer"):
            m = re.match(r'^(?:text|name|layer)\s+(.+)$', line, re.IGNORECASE)
            if m:
                args = [self._eval_expr(a) for a in self._split_top_level_args(m.group(1))]
                if args:
                    self.entities.append(
                        S2DEntity(
                            type=cmd,
                            properties={"text": str(args[0])},
                        )
                    )

    def compute_bounding_box(self) -> Dict[str, float]:
        """Computes parametric 2D bounding box from entities or variables."""
        min_x, min_y = float("inf"), float("inf")
        max_x, max_y = float("-inf"), float("-inf")

        for ent in self.entities:
            p = ent.properties
            if ent.type in ("rect", "roundrect"):
                x, y, w, h = p["x"], p["y"], p["width"], p["height"]
                min_x = min(min_x, x, x + w)
                max_x = max(max_x, x, x + w)
                min_y = min(min_y, y, y + h)
                max_y = max(max_y, y, y + h)
            elif ent.type in ("line", "cline"):
                min_x = min(min_x, p["x1"], p["x2"])
                max_x = max(max_x, p["x1"], p["x2"])
                min_y = min(min_y, p["y1"], p["y2"])
                max_y = max(max_y, p["y1"], p["y2"])
            elif ent.type == "circle":
                cx, cy, r = p["cx"], p["cy"], p["radius"]
                min_x = min(min_x, cx - r)
                max_x = max(max_x, cx + r)
                min_y = min(min_y, cy - r)
                max_y = max(max_y, cy + r)

        if math.isinf(min_x) or math.isinf(min_y):
            # Fallback to variables B, L, b, t, w
            w_val = self.variables.get("B") or self.variables.get("b") or self.variables.get("w") or 0.0
            h_val = self.variables.get("L") or self.variables.get("t") or 0.0
            w_float = float(parse_unit_value(w_val))
            h_float = float(parse_unit_value(h_val))
            return {
                "min_x": -w_float / 2.0,
                "min_y": -h_float / 2.0,
                "max_x": w_float / 2.0,
                "max_y": h_float / 2.0,
                "width": round(w_float, 6),
                "height": round(h_float, 6),
            }

        return {
            "min_x": round(min_x, 6),
            "min_y": round(min_y, 6),
            "max_x": round(max_x, 6),
            "max_y": round(max_y, 6),
            "width": round(max_x - min_x, 6),
            "height": round(max_y - min_y, 6),
        }

    def export_parameters(self) -> Dict[str, Any]:
        """Exports extracted parameters and state as a structured dictionary."""
        return {
            "title": self.title,
            "break_if_not": self.break_if_not,
            "variables": dict(self.variables),
            "inputs": [f.to_dict() for f in self.inputs],
            "attributes": dict(self.attributes),
            "entities": [e.to_dict() for e in self.entities],
            "bounding_box": self.compute_bounding_box(),
        }
