import pytest
from django.template import Context, Template, TemplateSyntaxError

from django_components import Component, register, registry


class TestComponentTag:
    def setup_method(self):
        registry.clear()

    def teardown_method(self):
        registry.clear()

    def test_render_component_from_template(self):
        @register("greeting")
        class GreetingComp(Component):
            template = "<p>Hello {{ name }}</p>"

            def get_template_data(self, args, kwargs, slots, context):
                return {"name": kwargs.get("name", "world")}

        tmpl = Template('{% component "greeting" name="Alice" %}{% endcomponent %}')
        rendered = tmpl.render(Context())
        assert "Hello Alice" in rendered

    def test_component_tag_with_variable(self):
        @register("echo")
        class EchoComp(Component):
            template = "<span>{{ text }}</span>"

            def get_template_data(self, args, kwargs, slots, context):
                return {"text": kwargs.get("text", "")}

        tmpl = Template('{% component "echo" text=my_var %}{% endcomponent %}')
        rendered = tmpl.render(Context({"my_var": "dynamic"}))
        assert "dynamic" in rendered

    def test_component_tag_multiple_kwargs(self):
        @register("box")
        class BoxComp(Component):
            template = "<div class='{{ cls }}'>{{ content }}</div>"

            def get_template_data(self, args, kwargs, slots, context):
                return {"cls": kwargs.get("cls", ""), "content": kwargs.get("content", "")}

        tmpl = Template('{% component "box" cls="red" content="stuff" %}{% endcomponent %}')
        rendered = tmpl.render(Context())
        assert "red" in rendered
        assert "stuff" in rendered

    def test_component_not_registered_raises(self):
        tmpl = Template('{% component "nonexistent" %}{% endcomponent %}')
        with pytest.raises(Exception):
            tmpl.render(Context())


class TestSlotTag:
    def setup_method(self):
        registry.clear()

    def teardown_method(self):
        registry.clear()

    def test_slot_with_default_content(self):
        @register("card")
        class CardComp(Component):
            template = '<div>{% slot "header" %}Default Header{% endslot %}</div>'

        tmpl = Template('{% component "card" %}{% endcomponent %}')
        rendered = tmpl.render(Context())
        assert "Default Header" in rendered

    def test_slot_filled_replaces_default(self):
        @register("card")
        class CardComp(Component):
            template = '<div>{% slot "header" %}Default Header{% endslot %}</div>'

        tmpl = Template('{% component "card" %}{% fill "header" %}Custom Header{% endfill %}{% endcomponent %}')
        rendered = tmpl.render(Context())
        assert "Custom Header" in rendered
        assert "Default Header" not in rendered

    def test_multiple_named_slots(self):
        @register("layout")
        class LayoutComp(Component):
            template = """
                <header>{% slot "head" %}Default head{% endslot %}</header>
                <main>{% slot "body" %}Default body{% endslot %}</main>
                <footer>{% slot "foot" %}Default foot{% endslot %}</footer>
            """

        tmpl = Template("""
            {% component "layout" %}
                {% fill "head" %}My Head{% endfill %}
                {% fill "body" %}My Body{% endfill %}
            {% endcomponent %}
        """)
        rendered = tmpl.render(Context())
        assert "My Head" in rendered
        assert "My Body" in rendered
        assert "Default foot" in rendered
        assert "Default head" not in rendered
        assert "Default body" not in rendered

    def test_slot_empty_when_filled_with_empty_content(self):
        @register("wrapper")
        class WrapperComp(Component):
            template = '<div>{% slot "content" %}Fallback{% endslot %}</div>'

        tmpl = Template('{% component "wrapper" %}{% fill "content" %}{% endfill %}{% endcomponent %}')
        rendered = tmpl.render(Context())
        assert "Fallback" not in rendered

    def test_self_closing_fill(self):
        @register("wrapper")
        class WrapperComp(Component):
            template = '<div>{% slot "content" %}Fallback{% endslot %}</div>'

        tmpl = Template('{% component "wrapper" %}{% fill "content" / %}{% endcomponent %}')
        rendered = tmpl.render(Context())
        assert "Fallback" not in rendered


class TestNestedComponents:
    def setup_method(self):
        registry.clear()

    def teardown_method(self):
        registry.clear()

    def test_nested_component_rendering(self):
        @register("inner")
        class InnerComp(Component):
            template = "<span>{{ label }}</span>"

            def get_template_data(self, args, kwargs, slots, context):
                return {"label": kwargs.get("label", "")}

        @register("outer")
        class OuterComp(Component):
            template = '<div>{% component "inner" label="nested" %}{% endcomponent %}</div>'

        tmpl = Template('{% component "outer" %}{% endcomponent %}')
        rendered = tmpl.render(Context())
        assert "<span>nested</span>" in rendered


class TestContextInFills:
    def setup_method(self):
        registry.clear()

    def teardown_method(self):
        registry.clear()

    def test_fill_can_access_parent_context(self):
        @register("panel")
        class PanelComp(Component):
            template = '<div>{% slot "content" %}empty{% endslot %}</div>'

        tmpl = Template("""
            {% with greeting="Hello from parent" %}
            {% component "panel" %}
                {% fill "content" %}{{ greeting }}{% endfill %}
            {% endcomponent %}
            {% endwith %}
        """)
        rendered = tmpl.render(Context())
        assert "Hello from parent" in rendered

    def test_fill_can_access_outer_context_variables(self):
        @register("box")
        class BoxComp(Component):
            template = '<div>{% slot "main" %}{% endslot %}</div>'

        tmpl = Template("""
            {% component "box" %}
                {% fill "main" %}Value is {{ ctx_val }}{% endfill %}
            {% endcomponent %}
        """)
        rendered = tmpl.render(Context({"ctx_val": "42"}))
        assert "Value is 42" in rendered


class TestSelfClosingComponentTag:
    def setup_method(self):
        registry.clear()

    def teardown_method(self):
        registry.clear()

    def test_self_closing_component(self):
        @register("icon")
        class IconComp(Component):
            template = "<i>{{ name }}</i>"

            def get_template_data(self, args, kwargs, slots, context):
                return {"name": kwargs.get("name", "?")}

        tmpl = Template('{% component "icon" name="star" / %}')
        rendered = tmpl.render(Context())
        assert "<i>star</i>" in rendered
