from abc import ABC, abstractmethod
from typing import Any, NamedTuple


class TagResult(NamedTuple):
    component_name: str
    tokens: list[str]


class TagFormatterABC(ABC):
    @abstractmethod
    def start_tag(self, name: str) -> str:
        ...

    @abstractmethod
    def end_tag(self, name: str) -> str:
        ...

    @abstractmethod
    def parse(self, tokens: list[str]) -> TagResult:
        ...


class ComponentFormatter(TagFormatterABC):
    def start_tag(self, name: str) -> str:
        return "component"

    def end_tag(self, name: str) -> str:
        return "endcomponent"

    def parse(self, tokens: list[str]) -> TagResult:
        if not tokens:
            raise ValueError("ComponentFormatter.parse requires at least one token (the component name).")
        component_name = tokens[0]
        if (component_name.startswith('"') and component_name.endswith('"')) or \
           (component_name.startswith("'") and component_name.endswith("'")):
            component_name = component_name[1:-1]
        return TagResult(component_name=component_name, tokens=tokens[1:])


class ShorthandComponentFormatter(TagFormatterABC):
    def start_tag(self, name: str) -> str:
        return name

    def end_tag(self, name: str) -> str:
        return f"end{name}"

    def parse(self, tokens: list[str]) -> TagResult:
        return TagResult(component_name="", tokens=tokens)


component_formatter = ComponentFormatter()
component_shorthand_formatter = ShorthandComponentFormatter()
