from dataclasses import dataclass, field
from typing import Any, Callable, Optional, Protocol, runtime_checkable, Union

from django.utils.safestring import SafeString


@dataclass(frozen=True)
class SlotContext:
    data: Any = None
    fallback: Any = None
    context: Any = None


@runtime_checkable
class SlotFunc(Protocol):
    def __call__(self, ctx: SlotContext) -> str: ...


@dataclass
class Slot:
    content_func: Optional[Callable] = None
    _raw_content: Any = None
    name: Optional[str] = None
    extra: dict = field(default_factory=dict)

    def __call__(
        self,
        data: Any = None,
        fallback: Any = None,
        context: Any = None,
    ) -> str:
        ctx = SlotContext(data=data, fallback=fallback, context=context)
        if self.content_func is not None:
            return self.content_func(ctx)
        if self._raw_content is not None:
            return str(self._raw_content)
        return ""


def _make_slot(value: Any) -> Slot:
    if isinstance(value, Slot):
        return value
    if callable(value):
        return Slot(content_func=value)
    return Slot(_raw_content=value)


def normalize_slot_map(raw_slots: dict) -> dict:
    return {name: _make_slot(val) for name, val in raw_slots.items()}
