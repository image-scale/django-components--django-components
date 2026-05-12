from collections import namedtuple
from typing import Any, Optional

from django.template import Context

_PROVIDE_CONTEXT_PREFIX = "__provide_"


class ProvideData:
    def __init__(self, **kwargs):
        self._data = kwargs
        for key, val in kwargs.items():
            setattr(self, key, val)

    def __repr__(self):
        items = ", ".join(f"{k}={v!r}" for k, v in self._data.items())
        return f"DepInject({items})"

    def __str__(self):
        return self.__repr__()


def set_provided_data(context: Context, name: str, data: ProvideData) -> None:
    context[_PROVIDE_CONTEXT_PREFIX + name] = data


def get_provided_data(context: Context, name: str, default: Any = None) -> Any:
    key = _PROVIDE_CONTEXT_PREFIX + name
    value = context.get(key)
    if value is not None:
        return value
    return default
