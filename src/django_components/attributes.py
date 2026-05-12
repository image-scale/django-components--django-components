import re
from typing import Any, Mapping, Union

from django.utils.html import conditional_escape
from django.utils.safestring import SafeString, mark_safe


def format_attributes(attrs: Mapping[str, Any]) -> str:
    parts = []
    for key, value in attrs.items():
        if value is None or value is False:
            continue
        if value is True:
            parts.append(str(key))
        else:
            if isinstance(value, SafeString):
                escaped = value
            else:
                escaped = conditional_escape(str(value))
            parts.append(f'{key}="{escaped}"')
    return mark_safe(" ".join(parts))


def _normalize_class_value(value: Any) -> list[str]:
    if isinstance(value, str):
        return value.split()
    if isinstance(value, dict):
        return [k for k, v in value.items() if v]
    if isinstance(value, (list, tuple)):
        result = []
        for item in value:
            result.extend(_normalize_class_value(item))
        return result
    return [str(value)] if value else []


def _apply_class_overrides(items: list) -> str:
    class_state = {}
    for item in items:
        if isinstance(item, str):
            for cls_name in item.split():
                class_state[cls_name] = True
        elif isinstance(item, dict):
            for cls_name, enabled in item.items():
                if enabled:
                    class_state[cls_name] = True
                else:
                    class_state[cls_name] = False
        elif isinstance(item, (list, tuple)):
            sub_result = _apply_class_overrides(list(item))
            for cls_name in sub_result.split():
                class_state[cls_name] = True
    return " ".join(k for k, v in class_state.items() if v)


def _parse_style_string(style_str: str) -> dict:
    result = {}
    if not style_str or not style_str.strip():
        return result
    for part in style_str.split(";"):
        part = part.strip()
        if ":" in part:
            prop, val = part.split(":", 1)
            prop = prop.strip()
            val = val.strip()
            if prop:
                result[prop] = val
    return result


def _apply_style_overrides(items: list) -> str:
    style_state = {}
    for item in items:
        if isinstance(item, str):
            parsed = _parse_style_string(item)
            for prop, val in parsed.items():
                style_state[prop] = val
        elif isinstance(item, dict):
            for prop, val in item.items():
                if val is False:
                    style_state.pop(prop, None)
                elif val is None:
                    pass
                else:
                    style_state[prop] = val
        elif isinstance(item, (list, tuple)):
            sub_result = _apply_style_overrides(list(item))
            parsed = _parse_style_string(sub_result)
            for prop, val in parsed.items():
                style_state[prop] = val
    if not style_state:
        return ""
    parts = [f"{prop}: {val}" for prop, val in style_state.items()]
    return "; ".join(parts) + ";"


def merge_attributes(*attr_dicts: dict) -> dict:
    merged: dict[str, Any] = {}

    all_class_items: list = []
    all_style_items: list = []
    has_class = False
    has_style = False

    for attrs in attr_dicts:
        for key, value in attrs.items():
            if key == "class":
                has_class = True
                if isinstance(value, (list, tuple)):
                    all_class_items.extend(value)
                else:
                    all_class_items.append(value)
            elif key == "style":
                has_style = True
                if isinstance(value, (list, tuple)):
                    all_style_items.extend(value)
                else:
                    all_style_items.append(value)
            else:
                if key in merged:
                    merged[key] = f"{merged[key]} {value}"
                else:
                    merged[key] = value

    if has_class:
        merged["class"] = _apply_class_overrides(all_class_items)

    if has_style:
        merged["style"] = _apply_style_overrides(all_style_items)

    return merged
