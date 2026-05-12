from django_components.component import Component
from django_components.attributes import format_attributes, merge_attributes
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
    "format_attributes",
    "merge_attributes",
    "register",
    "registry",
    "RegistrySettings",
]
