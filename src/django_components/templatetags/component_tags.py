import re
from typing import Any, Optional

import django.template
from django.template import Context, Node, NodeList, TemplateSyntaxError
from django.utils.safestring import mark_safe

from django_components.registry import registry

register = django.template.Library()

_FILL_CONTEXT_KEY = "__component_fills__"
_COMPONENT_CONTEXT_KEY = "__component_instance__"


def _strip_quotes(val):
    if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
        return val[1:-1]
    return None


class ComponentNode(Node):
    def __init__(self, component_name, kwargs_expr, nodelist, self_closing=False):
        self.component_name = component_name
        self.kwargs_expr = kwargs_expr
        self.nodelist = nodelist
        self.self_closing = self_closing

    def render(self, context: Context) -> str:
        comp_name = self.component_name.resolve(context) if hasattr(self.component_name, 'resolve') else self.component_name

        comp_cls = registry.get(comp_name)

        resolved_kwargs = {}
        for key, val in self.kwargs_expr.items():
            if hasattr(val, 'resolve'):
                resolved_kwargs[key] = val.resolve(context)
            else:
                resolved_kwargs[key] = val

        fills = {}
        if not self.self_closing and self.nodelist:
            for node in self.nodelist:
                if isinstance(node, FillNode):
                    fill_name = node.slot_name
                    fills[fill_name] = node
                elif isinstance(node, django.template.base.TextNode):
                    stripped = node.s.strip()
                    if stripped:
                        if "default" not in fills:
                            fills["default"] = _TextFillNode(node.s)
                        else:
                            existing = fills["default"]
                            if isinstance(existing, _TextFillNode):
                                existing.text += node.s
                            else:
                                fills["default"] = _TextFillNode(node.s)

        instance = comp_cls(registered_name=comp_cls._registered_name or comp_name)
        instance.args = []
        instance.kwargs = dict(resolved_kwargs)

        from django_components.slots import normalize_slot_map
        instance.slots = {}

        tmpl = instance._resolve_template()

        template_data = instance.get_template_data(
            instance.args,
            instance.kwargs,
            instance.slots,
            context,
        )

        context.push()
        context.update(template_data or {})
        context[_COMPONENT_CONTEXT_KEY] = instance
        context[_FILL_CONTEXT_KEY] = fills

        try:
            rendered = tmpl.render(context)
        finally:
            context.pop()

        return mark_safe(rendered.strip())


class _TextFillNode:
    def __init__(self, text):
        self.text = text
        self.data_var = None
        self.fallback_var = None

    def render_fill(self, context, slot_data=None, slot_fallback=None):
        return self.text


class FillNode(Node):
    def __init__(self, slot_name, nodelist, data_var=None, fallback_var=None):
        self.slot_name = slot_name
        self.nodelist = nodelist
        self.data_var = data_var
        self.fallback_var = fallback_var

    def render(self, context: Context) -> str:
        return ""

    def render_fill(self, context: Context, slot_data=None, slot_fallback=None) -> str:
        context.push()
        try:
            if self.data_var and slot_data is not None:
                context[self.data_var] = slot_data
            if self.fallback_var and slot_fallback is not None:
                context[self.fallback_var] = slot_fallback
            return self.nodelist.render(context)
        finally:
            context.pop()


class _SlotData:
    def __init__(self, data_dict):
        self._data = data_dict
        for k, v in data_dict.items():
            setattr(self, k, v)

    def __repr__(self):
        items = ", ".join(f"{k}={v!r}" for k, v in self._data.items())
        return f"SlotData({items})"


class SlotNode(Node):
    def __init__(self, slot_name, nodelist, is_required=False, is_default=False, slot_kwargs_expr=None):
        self.slot_name = slot_name
        self.nodelist = nodelist
        self.is_required = is_required
        self.is_default = is_default
        self.slot_kwargs_expr = slot_kwargs_expr or {}

    def render(self, context: Context) -> str:
        fills = context.get(_FILL_CONTEXT_KEY, {})

        slot_name = self.slot_name
        if hasattr(slot_name, 'resolve'):
            slot_name = slot_name.resolve(context)

        fill_node = fills.get(slot_name)

        if self.is_default and fill_node is None:
            fill_node = fills.get("default")

        slot_data = {}
        for key, val_expr in self.slot_kwargs_expr.items():
            if hasattr(val_expr, 'resolve'):
                slot_data[key] = val_expr.resolve(context)
            else:
                slot_data[key] = val_expr

        slot_fallback = None
        if self.nodelist:
            slot_fallback = self.nodelist.render(context)

        if fill_node is not None:
            if hasattr(fill_node, 'render_fill'):
                data_obj = _SlotData(slot_data) if slot_data else None
                return fill_node.render_fill(context, slot_data=data_obj, slot_fallback=slot_fallback)
            return str(fill_node)

        if self.is_required:
            raise TemplateSyntaxError(
                f"Slot '{slot_name}' is required but was not filled."
            )

        if slot_fallback is not None:
            return slot_fallback

        return ""


@register.tag("component")
def do_component(parser, token):
    bits = token.split_contents()
    tag_name = bits[0]

    self_closing = False
    if bits and bits[-1] == "/":
        self_closing = True
        bits = bits[:-1]

    if len(bits) < 2:
        raise TemplateSyntaxError(f"'{tag_name}' tag requires at least one argument (the component name).")

    comp_name_raw = bits[1]
    unquoted = _strip_quotes(comp_name_raw)
    if unquoted is not None:
        comp_name = unquoted
    else:
        comp_name = parser.compile_filter(comp_name_raw)

    kwargs_expr = {}
    for bit in bits[2:]:
        if "=" in bit:
            key, val_str = bit.split("=", 1)
            kwargs_expr[key] = parser.compile_filter(val_str)
        else:
            kwargs_expr[bit] = parser.compile_filter(bit)

    if self_closing:
        nodelist = NodeList()
    else:
        nodelist = parser.parse(("endcomponent",))
        parser.delete_first_token()

    return ComponentNode(comp_name, kwargs_expr, nodelist, self_closing=self_closing)


@register.tag("slot")
def do_slot(parser, token):
    bits = token.split_contents()
    tag_name = bits[0]

    self_closing = False
    if bits and bits[-1] == "/":
        self_closing = True
        bits = bits[:-1]

    if len(bits) < 2:
        raise TemplateSyntaxError(f"'{tag_name}' tag requires at least one argument (the slot name).")

    slot_name_raw = bits[1]
    unquoted = _strip_quotes(slot_name_raw)
    if unquoted is not None:
        slot_name = unquoted
    else:
        slot_name = parser.compile_filter(slot_name_raw)

    is_required = False
    is_default = False
    slot_kwargs_expr = {}

    for bit in bits[2:]:
        if bit == "required":
            is_required = True
        elif bit == "default":
            is_default = True
        elif "=" in bit:
            key, val_str = bit.split("=", 1)
            slot_kwargs_expr[key] = parser.compile_filter(val_str)

    if self_closing:
        nodelist = NodeList()
    else:
        nodelist = parser.parse(("endslot",))
        parser.delete_first_token()

    return SlotNode(slot_name, nodelist, is_required=is_required, is_default=is_default, slot_kwargs_expr=slot_kwargs_expr)


@register.tag("fill")
def do_fill(parser, token):
    bits = token.split_contents()
    tag_name = bits[0]

    self_closing = False
    if bits and bits[-1] == "/":
        self_closing = True
        bits = bits[:-1]

    if len(bits) < 2:
        raise TemplateSyntaxError(f"'{tag_name}' tag requires at least one argument (the slot name).")

    slot_name_raw = bits[1]
    unquoted = _strip_quotes(slot_name_raw)
    if unquoted is not None:
        slot_name = unquoted
    else:
        slot_name = slot_name_raw

    data_var = None
    fallback_var = None

    for bit in bits[2:]:
        if "=" in bit:
            key, val_str = bit.split("=", 1)
            val_unquoted = _strip_quotes(val_str)
            val = val_unquoted if val_unquoted is not None else val_str
            if key == "data":
                data_var = val
            elif key == "fallback":
                fallback_var = val

    if self_closing:
        nodelist = NodeList()
    else:
        nodelist = parser.parse(("endfill",))
        parser.delete_first_token()

    return FillNode(slot_name, nodelist, data_var=data_var, fallback_var=fallback_var)


class HtmlAttrsNode(Node):
    def __init__(self, positional_exprs, kwargs_exprs, defaults_exprs):
        self.positional_exprs = positional_exprs
        self.kwargs_exprs = kwargs_exprs
        self.defaults_exprs = defaults_exprs

    def render(self, context: Context) -> str:
        from django_components.attributes import format_attributes, merge_attributes

        defaults_dict = {}
        for key, val_expr in self.defaults_exprs.items():
            if hasattr(val_expr, 'resolve'):
                defaults_dict[key] = val_expr.resolve(context)
            else:
                defaults_dict[key] = val_expr

        attr_dicts = []
        if defaults_dict:
            attr_dicts.append(defaults_dict)

        for expr in self.positional_exprs:
            if hasattr(expr, 'resolve'):
                resolved = expr.resolve(context)
            else:
                resolved = expr
            if isinstance(resolved, dict):
                attr_dicts.append(resolved)

        extra_kwargs = {}
        for key, val_expr in self.kwargs_exprs.items():
            if hasattr(val_expr, 'resolve'):
                extra_kwargs[key] = val_expr.resolve(context)
            else:
                extra_kwargs[key] = val_expr
        if extra_kwargs:
            attr_dicts.append(extra_kwargs)

        if attr_dicts:
            merged = merge_attributes(*attr_dicts)
        else:
            merged = {}

        return format_attributes(merged)


@register.tag("html_attrs")
def do_html_attrs(parser, token):
    bits = token.split_contents()
    tag_name = bits[0]

    positional_exprs = []
    kwargs_exprs = {}
    defaults_exprs = {}

    for bit in bits[1:]:
        if bit.startswith("defaults:"):
            rest = bit[len("defaults:"):]
            if "=" in rest:
                key, val_str = rest.split("=", 1)
                defaults_exprs[key] = parser.compile_filter(val_str)
            else:
                defaults_exprs[rest] = parser.compile_filter(rest)
        elif "=" in bit:
            key, val_str = bit.split("=", 1)
            kwargs_exprs[key] = parser.compile_filter(val_str)
        else:
            positional_exprs.append(parser.compile_filter(bit))

    return HtmlAttrsNode(positional_exprs, kwargs_exprs, defaults_exprs)
