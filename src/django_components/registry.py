from typing import Any, Optional


class AlreadyRegistered(Exception):
    pass


class NotRegistered(Exception):
    pass


class RegistrySettings:
    def __init__(
        self,
        context_behavior: str = "django",
        tag_formatter: Any = None,
    ):
        self.context_behavior = context_behavior
        self.tag_formatter = tag_formatter


class ComponentRegistry:
    def __init__(
        self,
        library: Any = None,
        settings: Optional[RegistrySettings] = None,
    ):
        self._components: dict[str, type] = {}
        self.library = library
        self.settings = settings or RegistrySettings()

    def register(self, name: str, component: type) -> None:
        if name in self._components:
            existing = self._components[name]
            if existing is component:
                return
            raise AlreadyRegistered(
                f"A component with the name '{name}' is already registered "
                f"(existing: {existing}, new: {component})."
            )
        self._components[name] = component
        component._registered_name = name
        component._registry = self

    def unregister(self, name: str) -> None:
        if name not in self._components:
            raise NotRegistered(
                f"No component registered with the name '{name}'."
            )
        comp = self._components.pop(name)
        if getattr(comp, '_registered_name', None) == name:
            comp._registered_name = None
            comp._registry = None

    def get(self, name: str) -> type:
        if name not in self._components:
            raise NotRegistered(
                f"No component registered with the name '{name}'."
            )
        return self._components[name]

    def has(self, name: str) -> bool:
        return name in self._components

    def all(self) -> dict[str, type]:
        return dict(self._components)

    def clear(self) -> None:
        for name in list(self._components.keys()):
            comp = self._components[name]
            if getattr(comp, '_registered_name', None) == name:
                comp._registered_name = None
                comp._registry = None
        self._components.clear()


registry = ComponentRegistry()


def register(name: str, registry: Optional[ComponentRegistry] = None):
    target_registry = registry or globals()["registry"]

    def decorator(component_cls):
        target_registry.register(name, component_cls)
        return component_cls

    return decorator
