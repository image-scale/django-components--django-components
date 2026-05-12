import pytest
from django.template import Context, Template

from django_components import Component, register, registry


class TestProvideInject:
    def setup_method(self):
        registry.clear()

    def teardown_method(self):
        registry.clear()

    def test_basic_provide_inject(self):
        @register("injector")
        class InjectorComp(Component):
            template = "<div>{{ data_repr }}</div>"

            def get_template_data(self, args, kwargs, slots, context):
                provided = self.inject("my_data")
                return {"data_repr": str(provided)}

        tmpl = Template("""
            {% provide "my_data" key="hello" value=42 %}
                {% component "injector" %}{% endcomponent %}
            {% endprovide %}
        """)
        rendered = tmpl.render(Context())
        assert "hello" in rendered
        assert "42" in rendered

    def test_inject_access_individual_keys(self):
        @register("keyed")
        class KeyedComp(Component):
            template = "<p>{{ k }}-{{ v }}</p>"

            def get_template_data(self, args, kwargs, slots, context):
                data = self.inject("config")
                return {"k": data.key, "v": data.value}

        tmpl = Template("""
            {% provide "config" key="alpha" value="beta" %}
                {% component "keyed" %}{% endcomponent %}
            {% endprovide %}
        """)
        rendered = tmpl.render(Context())
        assert "alpha-beta" in rendered

    def test_inject_default_when_no_provider(self):
        @register("no_provider")
        class NoProviderComp(Component):
            template = "<span>{{ result }}</span>"

            def get_template_data(self, args, kwargs, slots, context):
                data = self.inject("nonexistent", "fallback_value")
                return {"result": data}

        tmpl = Template('{% component "no_provider" %}{% endcomponent %}')
        rendered = tmpl.render(Context())
        assert "fallback_value" in rendered

    def test_provide_scoped_to_block(self):
        @register("scoped_check")
        class ScopedComp(Component):
            template = "<span>{{ result }}</span>"

            def get_template_data(self, args, kwargs, slots, context):
                data = self.inject("scoped_data", "MISSING")
                return {"result": str(data)}

        tmpl = Template("""
            {% provide "scoped_data" val="inside" %}
                {% component "scoped_check" %}{% endcomponent %}
            {% endprovide %}
            {% component "scoped_check" %}{% endcomponent %}
        """)
        rendered = tmpl.render(Context())
        assert "inside" in rendered
        assert "MISSING" in rendered

    def test_multiple_providers_different_names(self):
        @register("multi_inject")
        class MultiComp(Component):
            template = "<div>{{ a }}-{{ b }}</div>"

            def get_template_data(self, args, kwargs, slots, context):
                data_a = self.inject("prov_a")
                data_b = self.inject("prov_b")
                return {"a": data_a.val, "b": data_b.val}

        tmpl = Template("""
            {% provide "prov_a" val="X" %}
                {% provide "prov_b" val="Y" %}
                    {% component "multi_inject" %}{% endcomponent %}
                {% endprovide %}
            {% endprovide %}
        """)
        rendered = tmpl.render(Context())
        assert "X-Y" in rendered

    def test_nested_providers_same_name_inner_wins(self):
        @register("nested_inject")
        class NestedComp(Component):
            template = "<span>{{ result }}</span>"

            def get_template_data(self, args, kwargs, slots, context):
                data = self.inject("theme")
                return {"result": data.color}

        tmpl = Template("""
            {% provide "theme" color="red" %}
                {% provide "theme" color="blue" %}
                    {% component "nested_inject" %}{% endcomponent %}
                {% endprovide %}
            {% endprovide %}
        """)
        rendered = tmpl.render(Context())
        assert "blue" in rendered
        assert "red" not in rendered.split("blue")[0].split("<span>")[-1]

    def test_self_closing_provide(self):
        tmpl = Template("""
            <div>
                {% provide "my_data" key="hi" / %}
                content
            </div>
        """)
        rendered = tmpl.render(Context())
        assert "content" in rendered

    def test_provide_with_context_variable(self):
        @register("ctx_inject")
        class CtxComp(Component):
            template = "<span>{{ injected_val }}</span>"

            def get_template_data(self, args, kwargs, slots, context):
                data = self.inject("dynamic")
                return {"injected_val": data.val}

        tmpl = Template("""
            {% provide "dynamic" val=my_var %}
                {% component "ctx_inject" %}{% endcomponent %}
            {% endprovide %}
        """)
        rendered = tmpl.render(Context({"my_var": "from_context"}))
        assert "from_context" in rendered
