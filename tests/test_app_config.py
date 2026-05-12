import os
import tempfile

import pytest
from django.conf import settings
from django.template import Context, Template

from django_components import Component, ContextBehavior, register, registry
from django_components.app_settings import ComponentsSettings, app_settings
from django_components.finders import ComponentFinder
from django_components.template_loader import Loader


class TestComponentsConfig:
    def test_app_config_name(self):
        from django_components.apps import ComponentsConfig
        config = ComponentsConfig("django_components", __import__("django_components"))
        assert config.name == "django_components"


class TestContextBehavior:
    def test_enum_values(self):
        assert ContextBehavior.DJANGO.value == "django"
        assert ContextBehavior.ISOLATED.value == "isolated"

    def test_enum_members(self):
        assert hasattr(ContextBehavior, "DJANGO")
        assert hasattr(ContextBehavior, "ISOLATED")


class TestComponentsSettings:
    def test_default_autodiscover(self):
        s = ComponentsSettings()
        assert s.AUTODISCOVER is True

    def test_default_dirs(self):
        s = ComponentsSettings()
        assert s.DIRS == []

    def test_default_context_behavior(self):
        s = ComponentsSettings()
        assert s.CONTEXT_BEHAVIOR == "django"

    def test_default_multiline_tags(self):
        s = ComponentsSettings()
        assert s.MULTILINE_TAGS is True


class TestTemplateLoader:
    def test_loader_get_dirs(self):
        loader = Loader(engine=None)
        dirs = loader.get_dirs()
        assert isinstance(dirs, list)

    def test_loader_get_template_sources(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            original_components = getattr(settings, 'COMPONENTS', {})
            settings.COMPONENTS = {"dirs": [tmpdir]}
            try:
                loader = Loader(engine=None)
                sources = list(loader.get_template_sources("test.html"))
                assert len(sources) == 1
                assert "test.html" in sources[0].name
            finally:
                settings.COMPONENTS = original_components

    def test_loader_get_contents(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test.html")
            with open(filepath, "w") as f:
                f.write("<div>Test Template</div>")

            original_components = getattr(settings, 'COMPONENTS', {})
            settings.COMPONENTS = {"dirs": [tmpdir]}
            try:
                loader = Loader(engine=None)
                sources = list(loader.get_template_sources("test.html"))
                content = loader.get_contents(sources[0])
                assert content == "<div>Test Template</div>"
            finally:
                settings.COMPONENTS = original_components


class TestComponentFinder:
    def test_finder_finds_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "style.css")
            with open(filepath, "w") as f:
                f.write("body { color: red; }")

            original_components = getattr(settings, 'COMPONENTS', {})
            settings.COMPONENTS = {"dirs": [tmpdir]}
            try:
                finder = ComponentFinder()
                result = finder.find("style.css")
                assert result == filepath
            finally:
                settings.COMPONENTS = original_components

    def test_finder_returns_empty_for_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            original_components = getattr(settings, 'COMPONENTS', {})
            settings.COMPONENTS = {"dirs": [tmpdir]}
            try:
                finder = ComponentFinder()
                result = finder.find("nonexistent.css")
                assert result == ""
            finally:
                settings.COMPONENTS = original_components

    def test_finder_list_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "script.js")
            with open(filepath, "w") as f:
                f.write("console.log('hi');")

            original_components = getattr(settings, 'COMPONENTS', {})
            settings.COMPONENTS = {"dirs": [tmpdir]}
            try:
                finder = ComponentFinder()
                files = finder.list()
                names = [f[0] for f in files]
                assert "script.js" in names
            finally:
                settings.COMPONENTS = original_components


class TestContextBehaviorInSlots:
    def setup_method(self):
        registry.clear()

    def teardown_method(self):
        registry.clear()
        settings.COMPONENTS = getattr(settings, '_original_components', {})

    def test_django_mode_fill_sees_component_data(self):
        settings._original_components = getattr(settings, 'COMPONENTS', {})
        settings.COMPONENTS = {"context_behavior": "django"}

        @register("ctx_comp")
        class CtxComp(Component):
            template = '{% slot "main" %}{% endslot %}'

            def get_template_data(self, args, kwargs, slots, context):
                return {"internal_var": "from_component"}

        tmpl = Template("""
            {% component "ctx_comp" %}
                {% fill "main" %}{{ internal_var }}{% endfill %}
            {% endcomponent %}
        """)
        rendered = tmpl.render(Context())
        assert "from_component" in rendered

    def test_isolated_mode_fill_does_not_see_component_data(self):
        settings._original_components = getattr(settings, 'COMPONENTS', {})
        settings.COMPONENTS = {"context_behavior": "isolated"}

        @register("iso_comp")
        class IsoComp(Component):
            template = '{% slot "main" %}{% endslot %}'

            def get_template_data(self, args, kwargs, slots, context):
                return {"internal_var": "should_not_see"}

        tmpl = Template("""
            {% component "iso_comp" %}
                {% fill "main" %}[{{ internal_var }}]{% endfill %}
            {% endcomponent %}
        """)
        rendered = tmpl.render(Context())
        assert "should_not_see" not in rendered

    def test_isolated_mode_fill_sees_outer_context(self):
        settings._original_components = getattr(settings, 'COMPONENTS', {})
        settings.COMPONENTS = {"context_behavior": "isolated"}

        @register("iso_outer")
        class IsoOuter(Component):
            template = '{% slot "main" %}{% endslot %}'

            def get_template_data(self, args, kwargs, slots, context):
                return {"comp_only": "hidden"}

        tmpl = Template("""
            {% component "iso_outer" %}
                {% fill "main" %}{{ outer_var }}{% endfill %}
            {% endcomponent %}
        """)
        rendered = tmpl.render(Context({"outer_var": "visible"}))
        assert "visible" in rendered
