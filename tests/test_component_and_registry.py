import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from tests.conftest import setup_test_django
setup_test_django()

import pytest
from django.template import Context, Template

from django_components import (
    AlreadyRegistered,
    Component,
    ComponentRegistry,
    NotRegistered,
    register,
    registry,
)


class TestComponentRendering:
    def test_render_inline_template(self):
        class Greeting(Component):
            template = "<p>Hello {{ name }}</p>"

            def get_template_data(self, args, kwargs, slots, context):
                return {"name": kwargs.get("name", "world")}

        rendered = Greeting.render(kwargs={"name": "Alice"})
        assert "Hello Alice" in rendered

    def test_render_default_template_data(self):
        class Empty(Component):
            template = "<div>static</div>"

        rendered = Empty.render()
        assert "static" in rendered

    def test_render_with_args(self):
        class ArgsComp(Component):
            template = "<span>{{ first }} {{ second }}</span>"

            def get_template_data(self, args, kwargs, slots, context):
                return {"first": args[0] if len(args) > 0 else "", "second": args[1] if len(args) > 1 else ""}

        rendered = ArgsComp.render(args=[42, "hello"])
        assert "42" in rendered
        assert "hello" in rendered

    def test_render_with_kwargs(self):
        class KwargsComp(Component):
            template = "<div>{{ color }} {{ size }}</div>"

            def get_template_data(self, args, kwargs, slots, context):
                return {"color": kwargs["color"], "size": kwargs["size"]}

        rendered = KwargsComp.render(kwargs={"color": "red", "size": 10})
        assert "red" in rendered
        assert "10" in rendered

    def test_render_returns_stripped_string(self):
        class Padded(Component):
            template = "   <p>content</p>   "

        rendered = Padded.render()
        assert rendered == "<p>content</p>"

    def test_render_without_template_raises(self):
        class NoTemplate(Component):
            pass

        with pytest.raises(ValueError, match="must define either"):
            NoTemplate.render()

    def test_component_name_fallback_to_class_name(self):
        class MySpecialComponent(Component):
            template = "<p>{{ comp_name }}</p>"

            def get_template_data(self, args, kwargs, slots, context):
                return {"comp_name": self.name}

        rendered = MySpecialComponent.render()
        assert "MySpecialComponent" in rendered

    def test_component_name_uses_registered_name(self):
        class NamedComp(Component):
            template = "<p>{{ comp_name }}</p>"

            def get_template_data(self, args, kwargs, slots, context):
                return {"comp_name": self.name}

        rendered = NamedComp.render(registered_name="my_widget")
        assert "my_widget" in rendered

    def test_render_multiple_variables(self):
        class Multi(Component):
            template = "<div>{{ a }}-{{ b }}-{{ c }}</div>"

            def get_template_data(self, args, kwargs, slots, context):
                return {"a": kwargs["a"], "b": kwargs["b"], "c": kwargs["c"]}

        rendered = Multi.render(kwargs={"a": "x", "b": "y", "c": "z"})
        assert "x-y-z" in rendered


class TestComponentRegistry:
    def setup_method(self):
        self.reg = ComponentRegistry()

    def test_register_and_get(self):
        class Comp(Component):
            template = "<div>hi</div>"

        self.reg.register("my_comp", Comp)
        assert self.reg.get("my_comp") is Comp

    def test_has_returns_true_when_registered(self):
        class Comp(Component):
            template = "<div>hi</div>"

        self.reg.register("comp1", Comp)
        assert self.reg.has("comp1") is True

    def test_has_returns_false_when_not_registered(self):
        assert self.reg.has("nonexistent") is False

    def test_all_returns_all_registered(self):
        class Comp1(Component):
            template = "<div>1</div>"

        class Comp2(Component):
            template = "<div>2</div>"

        self.reg.register("comp1", Comp1)
        self.reg.register("comp2", Comp2)
        result = self.reg.all()
        assert result == {"comp1": Comp1, "comp2": Comp2}

    def test_unregister_removes_component(self):
        class Comp(Component):
            template = "<div>hi</div>"

        self.reg.register("comp", Comp)
        self.reg.unregister("comp")
        assert self.reg.has("comp") is False
        assert self.reg.all() == {}

    def test_unregister_nonexistent_raises(self):
        with pytest.raises(NotRegistered):
            self.reg.unregister("not_there")

    def test_duplicate_name_different_class_raises(self):
        class Comp1(Component):
            template = "<div>1</div>"

        class Comp2(Component):
            template = "<div>2</div>"

        self.reg.register("widget", Comp1)
        with pytest.raises(AlreadyRegistered):
            self.reg.register("widget", Comp2)

    def test_duplicate_name_same_class_allowed(self):
        class Comp(Component):
            template = "<div>hi</div>"

        self.reg.register("widget", Comp)
        self.reg.register("widget", Comp)
        assert self.reg.get("widget") is Comp

    def test_clear_removes_all(self):
        class Comp1(Component):
            template = "<div>1</div>"

        class Comp2(Component):
            template = "<div>2</div>"

        self.reg.register("a", Comp1)
        self.reg.register("b", Comp2)
        self.reg.clear()
        assert self.reg.all() == {}

    def test_get_nonexistent_raises(self):
        with pytest.raises(NotRegistered):
            self.reg.get("missing")


class TestRegisterDecorator:
    def setup_method(self):
        registry.clear()

    def teardown_method(self):
        registry.clear()

    def test_decorator_registers_to_global_registry(self):
        @register("decorated_comp")
        class DecComp(Component):
            template = "<div>decorated</div>"

        assert registry.has("decorated_comp")
        assert registry.get("decorated_comp") is DecComp

    def test_decorator_registers_to_custom_registry(self):
        custom_reg = ComponentRegistry()

        @register("custom_comp", registry=custom_reg)
        class CustomComp(Component):
            template = "<div>custom</div>"

        assert custom_reg.has("custom_comp")
        assert not registry.has("custom_comp")

    def test_decorator_returns_original_class(self):
        @register("deco_test")
        class MyComp(Component):
            template = "<div>test</div>"

        assert MyComp.template == "<div>test</div>"

    def test_registered_component_render_uses_name(self):
        @register("greeting")
        class GreetComp(Component):
            template = "<p>{{ comp_name }}</p>"

            def get_template_data(self, args, kwargs, slots, context):
                return {"comp_name": self.name}

        rendered = GreetComp.render()
        assert "greeting" in rendered


class TestComponentStandaloneRender:
    def test_render_without_registration(self):
        class Standalone(Component):
            template = "<div>standalone</div>"

        rendered = Standalone.render()
        assert "standalone" in rendered

    def test_render_preserves_html_structure(self):
        class Nested(Component):
            template = "<div><span>{{ value }}</span></div>"

            def get_template_data(self, args, kwargs, slots, context):
                return {"value": kwargs.get("value", "")}

        rendered = Nested.render(kwargs={"value": "inner"})
        assert "<div><span>inner</span></div>" in rendered

    def test_render_with_context_dict(self):
        class CtxComp(Component):
            template = "<p>{{ existing_var }}</p>"

            def get_template_data(self, args, kwargs, slots, context):
                return {}

        rendered = CtxComp.render(context={"existing_var": "from_context"})
        assert "from_context" in rendered

    def test_args_default_to_empty_list(self):
        class CheckArgs(Component):
            template = "<div>{{ count }}</div>"

            def get_template_data(self, args, kwargs, slots, context):
                return {"count": len(args)}

        rendered = CheckArgs.render()
        assert "0" in rendered

    def test_kwargs_default_to_empty_dict(self):
        class CheckKwargs(Component):
            template = "<div>{{ count }}</div>"

            def get_template_data(self, args, kwargs, slots, context):
                return {"count": len(kwargs)}

        rendered = CheckKwargs.render()
        assert "0" in rendered
