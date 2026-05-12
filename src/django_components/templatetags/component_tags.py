import re
from typing import Any, Optional

import django.template
from django.template import Context, Node, NodeList, TemplateSyntaxError
from django.utils.safestring import mark_safe

from django_components.registry import registry

register = django.template.Library()

_FILL_CONTEXT_KEY = "__component_fills__"
_COMPONENT_CONTEXT_KEY = "__component_instance__"


def _parse_tag_kwargs(bits):
    kwargs = {}
    for bit in bits:
        if "=" in bit:
            key, val = bit.split("=", 1)
            if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                val = val[1:-1]
            kwargs[key] = val
        else:
            kwargs[bit] = bit
    return kwargs


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

    def render_fill(self, context):
        return self.text


class FillNode(Node):
    def __init__(self, slot_name, nodelist):
        self.slot_name = slot_name
        self.nodelist = nodelist

    def render(self, context: Context) -> str:
        return ""

    def render_fill(self, context: Context) -> str:
        return self.nodelist.render(context)


class SlotNode(Node):
    def __init__(self, slot_name, nodelist, is_required=False, is_default=False):
        self.slot_name = slot_name
        self.nodelist = nodelist
        self.is_required = is_required
        self.is_default = is_default

    def render(self, context: Context) -> str:
        fills = context.get(_FILL_CONTEXT_KEY, {})

        slot_name = self.slot_name
        if hasattr(slot_name, 'resolve'):
            slot_name = slot_name.resolve(context)

        fill_node = fills.get(slot_name)

        if self.is_default and fill_node is None:
            fill_node = fills.get("default")

        if fill_node is not None:
            if hasattr(fill_node, 'render_fill'):
                return fill_node.render_fill(context)
            return str(fill_node)

        if self.is_required:
            raise TemplateSyntaxError(
                f"Slot '{slot_name}' is required but was not filled."
            )

        if self.nodelist:
            return self.nodelist.render(context)

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
    if (comp_name_raw.startswith('"') and comp_name_raw.endswith('"')) or \
       (comp_name_raw.startswith("'") and comp_name_raw.endswith("'")):
        comp_name = comp_name_raw[1:-1]
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
    if (slot_name_raw.startswith('"') and slot_name_raw.endswith('"')) or \
       (slot_name_raw.startswith("'") and slot_name_raw.endswith("'")):
        slot_name = slot_name_raw[1:-1]
    else:
        slot_name = parser.compile_filter(slot_name_raw)

    is_required = "required" in bits[2:]
    is_default = "default" in bits[2:]

    if self_closing:
        nodelist = NodeList()
    else:
        nodelist = parser.parse(("endslot",))
        parser.delete_first_token()

    return SlotNode(slot_name, nodelist, is_required=is_required, is_default=is_default)


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
    if (slot_name_raw.startswith('"') and slot_name_raw.endswith('"')) or \
       (slot_name_raw.startswith("'") and slot_name_raw.endswith("'")):
        slot_name = slot_name_raw[1:-1]
    else:
        slot_name = slot_name_raw

    if self_closing:
        nodelist = NodeList()
    else:
        nodelist = parser.parse(("endfill",))
        parser.delete_first_token()

    return FillNode(slot_name, nodelist)
