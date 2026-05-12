from django_components.component import Component
from django_components.attributes import format_attributes, merge_attributes
from django_components.dependencies import Script, Style, render_dependencies
from django_components.registry import (
    AlreadyRegistered,
    NotRegistered,
    ComponentRegistry,
    RegistrySettings,
    register,
    registry,
)

__all__ = [
    "AlreadyRegistered",
    "Component",
    "ComponentRegistry",
    "NotRegistered",
    "Script",
    "Style",
    "format_attributes",
    "merge_attributes",
    "register",
    "registry",
    "render_dependencies",
    "RegistrySettings",
]
