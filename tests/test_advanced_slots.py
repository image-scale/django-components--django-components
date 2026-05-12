import pytest
from django.template import Context, Template, TemplateSyntaxError

from django_components import Component, register, registry


class TestRequiredSlot:
    def setup_method(self):
        registry.clear()

    def teardown_method(self):
        registry.clear()

    def test_required_slot_raises_when_not_filled(self):
        @register("req_comp")
        class ReqComp(Component):
            template = '<div>{% slot "content" required %}{% endslot %}</div>'

        tmpl = Template('{% component "req_comp" %}{% endcomponent %}')
        with pytest.raises(TemplateSyntaxError, match="required"):
            tmpl.render(Context())

    def test_required_slot_does_not_raise_when_filled(self):
        @register("req_comp2")
        class ReqComp2(Component):
            template = '<div>{% slot "content" required %}{% endslot %}</div>'

        tmpl = Template('{% component "req_comp2" %}{% fill "content" %}Filled!{% endfill %}{% endcomponent %}')
        rendered = tmpl.render(Context())
        assert "Filled!" in rendered

    def test_required_slot_self_closing(self):
        @register("req_sc")
        class ReqSC(Component):
            template = '<div>{% slot "content" required / %}</div>'

        tmpl = Template('{% component "req_sc" %}{% endcomponent %}')
        with pytest.raises(TemplateSyntaxError, match="required"):
            tmpl.render(Context())


class TestDefaultSlot:
    def setup_method(self):
        registry.clear()

    def teardown_method(self):
        registry.clear()

    def test_default_slot_captures_implicit_content(self):
        @register("def_comp")
        class DefComp(Component):
            template = '<div>{% slot "main" default %}Fallback{% endslot %}</div>'

        tmpl = Template('{% component "def_comp" %}Implicit content{% endcomponent %}')
        rendered = tmpl.render(Context())
        assert "Implicit content" in rendered
        assert "Fallback" not in rendered

    def test_default_slot_uses_fallback_when_no_content(self):
        @register("def_comp2")
        class DefComp2(Component):
            template = '<div>{% slot "main" default %}Fallback{% endslot %}</div>'

        tmpl = Template('{% component "def_comp2" %}{% endcomponent %}')
        rendered = tmpl.render(Context())
        assert "Fallback" in rendered

    def test_default_slot_vs_explicit_fill(self):
        @register("def_comp3")
        class DefComp3(Component):
            template = '<div>{% slot "main" default %}Fallback{% endslot %}</div>'

        tmpl = Template('{% component "def_comp3" %}{% fill "main" %}Explicit fill{% endfill %}{% endcomponent %}')
        rendered = tmpl.render(Context())
        assert "Explicit fill" in rendered
        assert "Fallback" not in rendered


class TestScopedSlots:
    def setup_method(self):
        registry.clear()

    def teardown_method(self):
        registry.clear()

    def test_slot_passes_data_to_fill(self):
        @register("scoped")
        class ScopedComp(Component):
            template = '{% slot "info" greeting="Hello" %}Default{% endslot %}'

        tmpl = Template(
            '{% component "scoped" %}'
            '{% fill "info" data="slot_data" %}Got: {{ slot_data.greeting }}{% endfill %}'
            '{% endcomponent %}'
        )
        rendered = tmpl.render(Context())
        assert "Got: Hello" in rendered

    def test_scoped_slot_with_context_variable_data(self):
        @register("scoped2")
        class ScopedComp2(Component):
            template = '{% slot "info" label=label_val %}Default{% endslot %}'

            def get_template_data(self, args, kwargs, slots, context):
                return {"label_val": kwargs.get("label", "DEFAULT")}

        tmpl = Template(
            '{% component "scoped2" label="Dynamic" %}'
            '{% fill "info" data="sd" %}Label: {{ sd.label }}{% endfill %}'
            '{% endcomponent %}'
        )
        rendered = tmpl.render(Context())
        assert "Label: Dynamic" in rendered

    def test_scoped_slot_multiple_data_keys(self):
        @register("multi_scoped")
        class MultiScopedComp(Component):
            template = '{% slot "info" first="A" second="B" %}{% endslot %}'

        tmpl = Template(
            '{% component "multi_scoped" %}'
            '{% fill "info" data="d" %}{{ d.first }}-{{ d.second }}{% endfill %}'
            '{% endcomponent %}'
        )
        rendered = tmpl.render(Context())
        assert "A-B" in rendered


class TestFillFallbackAccess:
    def setup_method(self):
        registry.clear()

    def teardown_method(self):
        registry.clear()

    def test_fill_can_access_slot_fallback(self):
        @register("fb_comp")
        class FBComp(Component):
            template = '{% slot "main" %}Original Content{% endslot %}'

        tmpl = Template(
            '{% component "fb_comp" %}'
            '{% fill "main" fallback="fb" %}Modified: {{ fb }}{% endfill %}'
            '{% endcomponent %}'
        )
        rendered = tmpl.render(Context())
        assert "Modified: Original Content" in rendered

    def test_fill_fallback_is_empty_when_no_fallback(self):
        @register("fb_comp2")
        class FBComp2(Component):
            template = '{% slot "main" / %}'

        tmpl = Template(
            '{% component "fb_comp2" %}'
            '{% fill "main" fallback="fb" %}Fallback:[{{ fb }}]{% endfill %}'
            '{% endcomponent %}'
        )
        rendered = tmpl.render(Context())
        assert "Fallback:[]" in rendered or "Fallback:[None]" in rendered

    def test_fill_with_both_data_and_fallback(self):
        @register("both_comp")
        class BothComp(Component):
            template = '{% slot "main" color="red" %}Default Text{% endslot %}'

        tmpl = Template(
            '{% component "both_comp" %}'
            '{% fill "main" data="d" fallback="fb" %}Color={{ d.color }}, FB={{ fb }}{% endfill %}'
            '{% endcomponent %}'
        )
        rendered = tmpl.render(Context())
        assert "Color=red" in rendered
        assert "FB=Default Text" in rendered


class TestSelfClosingSlot:
    def setup_method(self):
        registry.clear()

    def teardown_method(self):
        registry.clear()

    def test_self_closing_slot_renders_empty(self):
        @register("sc_comp")
        class SCComp(Component):
            template = '<div>{% slot "main" / %}</div>'

        tmpl = Template('{% component "sc_comp" %}{% endcomponent %}')
        rendered = tmpl.render(Context())
        assert "<div>" in rendered

    def test_self_closing_slot_can_be_filled(self):
        @register("sc_comp2")
        class SCComp2(Component):
            template = '<div>{% slot "main" / %}</div>'

        tmpl = Template('{% component "sc_comp2" %}{% fill "main" %}Content{% endfill %}{% endcomponent %}')
        rendered = tmpl.render(Context())
        assert "Content" in rendered
