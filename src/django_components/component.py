from typing import Any, ClassVar, Optional

from django.template import Context, Template
from django.utils.safestring import mark_safe


_render_counter = 0


def _next_render_id():
    global _render_counter
    _render_counter += 1
    return f"r{_render_counter:06x}"


class Component:
    template: ClassVar[Optional[str]] = None
    template_file: ClassVar[Optional[str]] = None

    _registered_name: Optional[str] = None
    _registry: Optional[Any] = None

    def __init__(self, registered_name: Optional[str] = None):
        self._instance_name = registered_name
        self.id: str = _next_render_id()
        self.args: list = []
        self.kwargs: dict = {}
        self.slots: dict = {}
        self.request = None
        self._context: Optional[Context] = None

    @property
    def name(self) -> str:
        if self._instance_name:
            return self._instance_name
        if self._registered_name:
            return self._registered_name
        return self.__class__.__name__

    def get_template_data(self, args, kwargs, slots, context) -> dict:
        return {}

    def _resolve_template(self) -> Template:
        if self.template is not None:
            return Template(self.template)
        if self.template_file is not None:
            from django.template.loader import get_template
            return get_template(self.template_file).template
        raise ValueError(
            f"Component '{self.name}' must define either 'template' or 'template_file'."
        )

    @classmethod
    def render(
        cls,
        args: Any = None,
        kwargs: Any = None,
        slots: Any = None,
        context: Any = None,
        registered_name: Optional[str] = None,
        request: Any = None,
    ) -> str:
        instance = cls(registered_name=registered_name or cls._registered_name)
        instance.args = list(args) if args else []
        instance.kwargs = dict(kwargs) if kwargs else {}
        instance.request = request

        raw_slots = dict(slots) if slots else {}

        from django_components.slots import normalize_slot_map
        instance.slots = normalize_slot_map(raw_slots)

        tmpl = instance._resolve_template()

        if context is not None:
            if isinstance(context, Context):
                render_context = context
            else:
                render_context = Context(context)
        else:
            render_context = Context()

        template_data = instance.get_template_data(
            instance.args,
            instance.kwargs,
            instance.slots,
            render_context,
        )

        render_context.push()
        render_context.update(template_data or {})
        render_context["_component_instance"] = instance
        render_context["_component_id"] = instance.id

        try:
            rendered = tmpl.render(render_context)
        finally:
            render_context.pop()

        return mark_safe(rendered.strip())

    @classmethod
    def render_to_response(cls, *a, **kw):
        from django.http import HttpResponse
        html = cls.render(*a, **kw)
        return HttpResponse(html)
