import pytest
from django.conf import settings
from django.template import Context, Template

from django_components import Component, djc_test, register, registry, setup_test_config


class TestDjcTestDecoratorFunction:
    def test_registry_isolated_between_tests_1(self):
        @djc_test
        def inner():
            @register("isolated_comp_1")
            class IsolatedComp1(Component):
                template = "<p>1</p>"

            assert registry.has("isolated_comp_1")

        inner()
        assert not registry.has("isolated_comp_1")

    def test_registry_isolated_between_tests_2(self):
        @djc_test
        def inner():
            assert not registry.has("isolated_comp_1")

        inner()

    def test_decorator_without_parens(self):
        @djc_test
        def inner():
            @register("no_parens_comp")
            class NoParensComp(Component):
                template = "<b>x</b>"

            assert registry.has("no_parens_comp")

        inner()
        assert not registry.has("no_parens_comp")

    def test_decorator_with_parens(self):
        @djc_test()
        def inner():
            @register("with_parens_comp")
            class WithParensComp(Component):
                template = "<i>y</i>"

            assert registry.has("with_parens_comp")

        inner()
        assert not registry.has("with_parens_comp")


class TestDjcTestDecoratorClass:
    def test_class_decorator_wraps_test_methods(self):
        @djc_test
        class FakeTests:
            def test_register(self):
                @register("class_comp")
                class ClassComp(Component):
                    template = "<div>class</div>"

                assert registry.has("class_comp")

        t = FakeTests()
        t.test_register()
        assert not registry.has("class_comp")

    def test_class_decorator_nested_class(self):
        @djc_test
        class FakeTests:
            class Nested:
                def test_nested(self):
                    @register("nested_comp")
                    class NestedComp(Component):
                        template = "<span>n</span>"

                    assert registry.has("nested_comp")

        t = FakeTests.Nested()
        t.test_nested()
        assert not registry.has("nested_comp")

    def test_class_decorator_non_test_methods_untouched(self):
        @djc_test
        class FakeTests:
            def helper(self):
                return "untouched"

            def test_something(self):
                pass

        t = FakeTests()
        assert t.helper() == "untouched"


class TestDjcTestSettingsOverride:
    def test_django_settings_override(self):
        @djc_test(django_settings={"SECRET_KEY": "overridden-key"})
        def inner():
            assert settings.SECRET_KEY == "overridden-key"

        inner()
        assert settings.SECRET_KEY == "test-secret-key"

    def test_components_settings_override(self):
        @djc_test(components_settings={"context_behavior": "isolated"})
        def inner():
            from django_components.app_settings import app_settings
            assert app_settings.CONTEXT_BEHAVIOR == "isolated"

        inner()

    def test_settings_merge(self):
        @djc_test(
            django_settings={"COMPONENTS": {"autodiscover": False}},
            components_settings={"context_behavior": "isolated"},
        )
        def inner():
            from django_components.app_settings import app_settings
            assert app_settings.AUTODISCOVER is False
            assert app_settings.CONTEXT_BEHAVIOR == "isolated"

        inner()


class TestDjcTestParametrize:
    def test_parametrize_basic(self):
        results = []

        @djc_test(
            parametrize=(
                ["components_settings"],
                [
                    [{"context_behavior": "django"}],
                    [{"context_behavior": "isolated"}],
                ],
                ["django", "isolated"],
            )
        )
        def inner(components_settings):
            from django_components.app_settings import app_settings
            results.append(app_settings.CONTEXT_BEHAVIOR)

        inner(components_settings={"context_behavior": "django"})
        inner(components_settings={"context_behavior": "isolated"})

        assert results == ["django", "isolated"]


class TestDjcTestPreservesExistingState:
    def setup_method(self):
        registry.clear()

    def teardown_method(self):
        registry.clear()

    def test_pre_existing_components_preserved(self):
        @register("pre_existing")
        class PreExisting(Component):
            template = "<div>pre</div>"

        @djc_test
        def inner():
            @register("new_comp")
            class NewComp(Component):
                template = "<div>new</div>"

            assert registry.has("pre_existing")
            assert registry.has("new_comp")

        inner()
        assert registry.has("pre_existing")
        assert not registry.has("new_comp")


class TestDjcTestContextBehaviorIntegration:
    def setup_method(self):
        registry.clear()

    def teardown_method(self):
        registry.clear()

    def test_django_mode_in_test(self):
        @djc_test(components_settings={"context_behavior": "django"})
        def inner():
            @register("dj_mode_comp")
            class DjModeComp(Component):
                template = '{% slot "main" %}{% endslot %}'

                def get_template_data(self, args, kwargs, slots, context):
                    return {"val": "visible"}

            tmpl = Template("""
                {% component "dj_mode_comp" %}
                    {% fill "main" %}{{ val }}{% endfill %}
                {% endcomponent %}
            """)
            rendered = tmpl.render(Context())
            assert "visible" in rendered

        inner()

    def test_isolated_mode_in_test(self):
        @djc_test(components_settings={"context_behavior": "isolated"})
        def inner():
            @register("iso_mode_comp")
            class IsoModeComp(Component):
                template = '{% slot "main" %}{% endslot %}'

                def get_template_data(self, args, kwargs, slots, context):
                    return {"val": "hidden"}

            tmpl = Template("""
                {% component "iso_mode_comp" %}
                    {% fill "main" %}[{{ val }}]{% endfill %}
                {% endcomponent %}
            """)
            rendered = tmpl.render(Context())
            assert "hidden" not in rendered

        inner()


class TestSetupTestConfig:
    def test_already_configured_is_noop(self):
        setup_test_config()
        assert settings.configured

    def test_function_exists_and_callable(self):
        assert callable(setup_test_config)


class TestDjcTestGcCollect:
    def test_gc_collect_false(self):
        @djc_test(gc_collect=False)
        def inner():
            @register("gc_comp")
            class GcComp(Component):
                template = "<p>gc</p>"

            assert registry.has("gc_comp")

        inner()
        assert not registry.has("gc_comp")
