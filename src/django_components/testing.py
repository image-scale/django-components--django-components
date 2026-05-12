import functools
import gc
import inspect
from typing import Any, Callable, Optional, TypeVar

from django.conf import settings
from django.test.utils import override_settings

from django_components.registry import ComponentRegistry, registry

TCallable = TypeVar("TCallable", bound=Callable)


def _save_registry_state(reg: ComponentRegistry) -> dict[str, type]:
    return dict(reg._components)


def _restore_registry_state(reg: ComponentRegistry, saved: dict[str, type]) -> None:
    current_names = set(reg._components.keys())
    saved_names = set(saved.keys())

    for name in current_names - saved_names:
        comp = reg._components.pop(name)
        if getattr(comp, '_registered_name', None) == name:
            comp._registered_name = None
            comp._registry = None

    for name in saved_names - current_names:
        reg._components[name] = saved[name]
        saved[name]._registered_name = name
        saved[name]._registry = reg


def _build_settings_override(
    django_settings: Optional[dict] = None,
    components_settings: Optional[dict] = None,
) -> dict:
    overrides = dict(django_settings or {})

    if components_settings:
        base_components = overrides.get("COMPONENTS", {})
        if base_components is None:
            base_components = {}
        merged = {**base_components, **components_settings}
        overrides["COMPONENTS"] = merged

    return overrides


def _wrap_function(
    func: Callable,
    django_settings: Optional[dict] = None,
    components_settings: Optional[dict] = None,
    gc_collect: bool = True,
) -> Callable:
    overrides = _build_settings_override(django_settings, components_settings)

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        merged_overrides = dict(overrides)
        sig = inspect.signature(func)
        param_names = set(sig.parameters.keys())

        extra_dj = None
        extra_comp = None
        if "django_settings" in kwargs:
            extra_dj = kwargs.pop("django_settings") or {}
            merged_overrides.update(extra_dj)
        if "components_settings" in kwargs:
            extra_comp = kwargs.pop("components_settings") or {}
            existing_comp = merged_overrides.get("COMPONENTS", {})
            merged_overrides["COMPONENTS"] = {**existing_comp, **extra_comp}

        if "django_settings" in param_names and extra_dj is not None:
            kwargs["django_settings"] = extra_dj
        if "components_settings" in param_names and extra_comp is not None:
            kwargs["components_settings"] = extra_comp

        saved = _save_registry_state(registry)

        ctx = override_settings(**merged_overrides) if merged_overrides else None
        if ctx:
            ctx.__enter__()

        try:
            result = func(*args, **kwargs)
            return result
        finally:
            _restore_registry_state(registry, saved)

            for engine in getattr(settings, '_engines', {}).values() if hasattr(settings, '_engines') else []:
                if hasattr(engine, 'template_loaders'):
                    for loader in engine.template_loaders:
                        loader.reset()

            if gc_collect:
                gc.collect()

            if ctx:
                ctx.__exit__(None, None, None)

    return wrapper


def _wrap_class(
    cls: type,
    django_settings: Optional[dict] = None,
    components_settings: Optional[dict] = None,
    parametrize: Optional[tuple] = None,
    gc_collect: bool = True,
) -> type:
    for attr_name in list(vars(cls)):
        attr = getattr(cls, attr_name)
        if attr_name.startswith("test_") and callable(attr):
            wrapped = _wrap_function(
                attr,
                django_settings=django_settings,
                components_settings=components_settings,
                gc_collect=gc_collect,
            )
            if parametrize is not None:
                import pytest
                if len(parametrize) == 3:
                    names, values, ids = parametrize
                    wrapped = pytest.mark.parametrize(names, values, ids=ids)(wrapped)
                else:
                    names, values = parametrize
                    wrapped = pytest.mark.parametrize(names, values)(wrapped)
            setattr(cls, attr_name, wrapped)

        elif isinstance(attr, type):
            _wrap_class(
                attr,
                django_settings=django_settings,
                components_settings=components_settings,
                gc_collect=gc_collect,
            )

    return cls


def djc_test(
    _func_or_cls: Any = None,
    *,
    django_settings: Optional[dict] = None,
    components_settings: Optional[dict] = None,
    parametrize: Optional[tuple] = None,
    gc_collect: bool = True,
) -> Any:
    """
    Decorator for test functions and classes that manages django-components
    global state, ensuring test isolation.

    Can be used as:
      @djc_test
      @djc_test()
      @djc_test(django_settings={...})
      @djc_test(components_settings={...})
      @djc_test(parametrize=(names, values))
      @djc_test(parametrize=(names, values, ids))
    """
    def decorator(func_or_cls):
        if isinstance(func_or_cls, type):
            return _wrap_class(
                func_or_cls,
                django_settings=django_settings,
                components_settings=components_settings,
                parametrize=parametrize,
                gc_collect=gc_collect,
            )
        else:
            wrapped = _wrap_function(
                func_or_cls,
                django_settings=django_settings,
                components_settings=components_settings,
                gc_collect=gc_collect,
            )
            if parametrize is not None:
                import pytest
                if len(parametrize) == 3:
                    names, values, ids = parametrize
                    wrapped = pytest.mark.parametrize(names, values, ids=ids)(wrapped)
                else:
                    names, values = parametrize
                    wrapped = pytest.mark.parametrize(names, values)(wrapped)
            return wrapped

    if _func_or_cls is not None:
        return decorator(_func_or_cls)

    return decorator


def setup_test_config(
    components: Optional[dict] = None,
    extra_settings: Optional[dict] = None,
) -> None:
    """
    Configure Django settings for test environments.
    Only configures if settings are not already configured.
    """
    from pathlib import Path

    if settings.configured:
        return

    import django

    default_settings = {
        "BASE_DIR": Path(__file__).resolve().parent.parent,
        "INSTALLED_APPS": ["django.contrib.contenttypes"],
        "TEMPLATES": [
            {
                "BACKEND": "django.template.backends.django.DjangoTemplates",
                "DIRS": [],
                "OPTIONS": {
                    "builtins": [
                        "django_components.templatetags.component_tags",
                    ],
                    "loaders": [
                        "django.template.loaders.filesystem.Loader",
                        "django.template.loaders.app_directories.Loader",
                    ],
                },
            },
        ],
        "DATABASES": {
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": ":memory:",
            },
        },
        "SECRET_KEY": "test-secret-key",
        "COMPONENTS": components or {},
    }

    if extra_settings:
        default_settings.update(extra_settings)

    settings.configure(**default_settings)
    django.setup()
