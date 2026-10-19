"""
Pure-Python lightweight YAML serializer with zero external dependencies.
Ensures .debim manifests can be serialized inside embedded environments (like IngeTrazo)
where PyYAML may not be installed.
"""

from typing import Any, Dict, List, Union


def _format_scalar(val: Any) -> str:
    if val is None:
        return "null"
    if isinstance(val, bool):
        return "true" if val else "false"
    if isinstance(val, (int, float)):
        return str(val)
    if isinstance(val, str):
        # Quote if empty, contains special YAML characters, or looks like keyword
        special_chars = set(":#{}[]|,>&*?%@`-\n\'\"")
        lower = val.lower()
        if (
            not val
            or any(c in special_chars for c in val)
            or lower in ("true", "false", "null", "yes", "no", "on", "off")
            or val.startswith(" ")
            or val.endswith(" ")
        ):
            escaped = val.replace("\\", "\\\\").replace('"', '\\"')
            return f'"{escaped}"'
        return val
    return str(val)


def _is_short_scalar_list(items: List[Any]) -> bool:
    """Returns True if list is compact (e.g. coordinates or grid keys [0.0, 0.0])."""
    if not items or len(items) > 6:
        return False
    return all(
        isinstance(x, (int, float, str, bool)) and len(str(x)) < 25
        for x in items
    )


def dump_yaml(data: Any, indent: int = 0) -> str:
    """
    Serializes Python data structures to clean YAML string.
    """
    spaces = "  " * indent

    if data is None:
        return "null"
    if isinstance(data, (bool, int, float, str)):
        return _format_scalar(data)

    if isinstance(data, list):
        if not data:
            return "[]"
        if _is_short_scalar_list(data):
            formatted = ", ".join(_format_scalar(x) for x in data)
            return f"[{formatted}]"

        lines = []
        for item in data:
            if isinstance(item, dict) and item:
                dict_content = dump_yaml(item, indent + 1)
                dict_lines = dict_content.splitlines()
                first = dict_lines[0].lstrip()
                lines.append(f"{spaces}- {first}")
                for rem in dict_lines[1:]:
                    lines.append(rem)
            elif isinstance(item, list) and _is_short_scalar_list(item):
                lines.append(f"{spaces}- {dump_yaml(item)}")
            else:
                item_content = dump_yaml(item, indent + 1)
                lines.append(f"{spaces}- {item_content}")
        return "\n".join(lines)

    if isinstance(data, dict):
        if not data:
            return "{}"
        lines = []
        for key, value in data.items():
            k_str = _format_scalar(key)
            if isinstance(value, (dict, list)) and value:
                if isinstance(value, list) and _is_short_scalar_list(value):
                    lines.append(f"{spaces}{k_str}: {dump_yaml(value)}")
                elif isinstance(value, dict) and not value:
                    lines.append(f"{spaces}{k_str}: {{}}")
                else:
                    lines.append(f"{spaces}{k_str}:")
                    lines.append(dump_yaml(value, indent + 1))
            else:
                lines.append(f"{spaces}{k_str}: {dump_yaml(value)}")
        return "\n".join(lines)

    return _format_scalar(data)


def safe_dump(data: Any, sort_keys: bool = False, allow_unicode: bool = True) -> str:
    """Drop-in compatible replacement for yaml.safe_dump / yaml.dump."""
    return dump_yaml(data, indent=0)
