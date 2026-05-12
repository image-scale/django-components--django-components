import pytest
from django.http import HttpResponse
from django.template import Context, Template

from django_components import Component, register, registry
from django_components.slots import Slot, SlotContext


class TestRenderToResponse:
    def setup_method(self):
        registry.clear()

    def teardown_method(self):
        registry.clear()

    def test_returns_http_response(self):
        @register("resp_comp")
        class RespComp(Component):
            template = "<p>hello</p>"

        result = RespComp.render_to_response()
        assert isinstance(result, HttpResponse)
        assert b"<p>hello</p>" in result.content

    def test_response_kwargs_content_type(self):
        @register("ct_comp")
        class CtComp(Component):
            template = "<div>hi</div>"

        result = CtComp.render_to_response(content_type="text/plain")
        assert result["Content-Type"] == "text/plain"

    def test_render_to_response_with_kwargs(self):
        @register("kw_resp_comp")
        class KwRespComp(Component):
            template = "<p>{{ greeting }}</p>"

            def get_template_data(self, args, kwargs, slots, context):
                return {"greeting": kwargs.get("greeting", "default")}

        result = KwRespComp.render_to_response(kwargs={"greeting": "world"})
        assert b"<p>world</p>" in result.content

    def test_render_to_response_with_args(self):
        @register("args_resp")
        class ArgsResp(Component):
            template = "<span>{{ val }}</span>"

            def get_template_data(self, args, kwargs, slots, context):
                return {"val": args[0] if args else "none"}

        result = ArgsResp.render_to_response(args=["test_val"])
        assert b"test_val" in result.content

    def test_render_to_response_status_code(self):
        @register("status_comp")
        class StatusComp(Component):
            template = "<p>created</p>"

        result = StatusComp.render_to_response(status=201)
        assert result.status_code == 201


class TestComponentSelfReferencing:
    def setup_method(self):
        registry.clear()

    def teardown_method(self):
        registry.clear()

    def test_self_name(self):
        @register("named_comp")
        class NamedComp(Component):
            template = "<p>{{ comp_name }}</p>"

            def get_template_data(self, args, kwargs, slots, context):
                return {"comp_name": self.name}

        rendered = NamedComp.render()
        assert "named_comp" in rendered

    def test_self_name_unregistered(self):
        class UnregComp(Component):
            template = "<p>{{ comp_name }}</p>"

            def get_template_data(self, args, kwargs, slots, context):
                return {"comp_name": self.name}

        rendered = UnregComp.render()
        assert "UnregComp" in rendered

    def test_self_args(self):
        @register("args_comp")
        class ArgsComp(Component):
            template = "<p>{{ first_arg }}</p>"

            def get_template_data(self, args, kwargs, slots, context):
                assert self.args == [123, "str"]
                return {"first_arg": self.args[0]}

        rendered = ArgsComp.render(args=[123, "str"])
        assert "123" in rendered

    def test_self_kwargs(self):
        @register("kwargs_comp")
        class KwargsComp(Component):
            template = "<p>{{ v }}</p>"

            def get_template_data(self, args, kwargs, slots, context):
                assert self.kwargs == {"variable": "test", "another": 1}
                return {"v": self.kwargs["variable"]}

        rendered = KwargsComp.render(kwargs={"variable": "test", "another": 1})
        assert "test" in rendered

    def test_self_slots(self):
        @register("slots_self_comp")
        class SlotsSelfComp(Component):
            template = '{% slot "main" %}fallback{% endslot %}'

            def get_template_data(self, args, kwargs, slots, context):
                assert "main" in self.slots
                main_slot = self.slots["main"]
                assert callable(main_slot)
                return {}

        rendered = SlotsSelfComp.render(slots={"main": "FILLED"})
        assert "FILLED" in rendered

    def test_self_id_unique(self):
        ids = []

        @register("id_comp")
        class IdComp(Component):
            template = "<p>{{ comp_id }}</p>"

            def get_template_data(self, args, kwargs, slots, context):
                ids.append(self.id)
                return {"comp_id": self.id}

        IdComp.render()
        IdComp.render()
        assert len(ids) == 2
        assert ids[0] != ids[1]

    def test_self_request(self):
        @register("req_comp")
        class ReqComp(Component):
            template = "<p>{{ has_request }}</p>"

            def get_template_data(self, args, kwargs, slots, context):
                return {"has_request": self.request is not None}

        rendered = ReqComp.render(request="fake_request")
        assert "True" in rendered


class TestProgrammaticSlots:
    def setup_method(self):
        registry.clear()

    def teardown_method(self):
        registry.clear()

    def test_slot_as_string(self):
        @register("str_slot_comp")
        class StrSlotComp(Component):
            template = '<div>{% slot "content" %}default{% endslot %}</div>'

        rendered = StrSlotComp.render(slots={"content": "Hello World"})
        assert "Hello World" in rendered

    def test_slot_as_callable(self):
        @register("fn_slot_comp")
        class FnSlotComp(Component):
            template = '<div>{% slot "content" %}default{% endslot %}</div>'

        rendered = FnSlotComp.render(
            slots={"content": lambda ctx: "From Lambda"}
        )
        assert "From Lambda" in rendered

    def test_slot_as_slot_instance(self):
        @register("inst_slot_comp")
        class InstSlotComp(Component):
            template = '<div>{% slot "content" %}default{% endslot %}</div>'

        slot = Slot(content_func=lambda ctx: "From Slot Instance")
        rendered = InstSlotComp.render(slots={"content": slot})
        assert "From Slot Instance" in rendered

    def test_slot_fallback_when_no_fill(self):
        @register("fb_comp")
        class FbComp(Component):
            template = '<div>{% slot "content" %}FALLBACK{% endslot %}</div>'

        rendered = FbComp.render()
        assert "FALLBACK" in rendered

    def test_multiple_slots_programmatic(self):
        @register("multi_slot_comp")
        class MultiSlotComp(Component):
            template = '{% slot "header" %}h{% endslot %}|{% slot "footer" %}f{% endslot %}'

        rendered = MultiSlotComp.render(
            slots={"header": "HEAD", "footer": "FOOT"}
        )
        assert "HEAD" in rendered
        assert "FOOT" in rendered

    def test_slot_none_uses_fallback(self):
        @register("none_slot_comp")
        class NoneSlotComp(Component):
            template = '<p>{% slot "main" %}default{% endslot %}</p>'

        rendered = NoneSlotComp.render(slots={})
        assert "default" in rendered


class TestNestedComponentRendering:
    def setup_method(self):
        registry.clear()

    def teardown_method(self):
        registry.clear()

    def test_nested_render_in_template(self):
        @register("inner_tmpl")
        class InnerTmpl(Component):
            template = "<span>inner</span>"

        @register("outer_tmpl")
        class OuterTmpl(Component):
            template = '<div>{% component "inner_tmpl" / %}</div>'

        rendered = Template(
            '{% component "outer_tmpl" / %}'
        ).render(Context())
        assert "<span>inner</span>" in rendered
        assert "<div>" in rendered

    def test_nested_programmatic_render(self):
        @register("inner_prog")
        class InnerProg(Component):
            template = "<em>nested</em>"

        @register("outer_prog")
        class OuterProg(Component):
            template = "<div>{{ inner_html }}</div>"

            def get_template_data(self, args, kwargs, slots, context):
                inner_html = InnerProg.render()
                return {"inner_html": inner_html}

        rendered = OuterProg.render()
        assert "<em>nested</em>" in rendered
        assert "<div>" in rendered

    def test_nested_with_data_passing(self):
        @register("child_data")
        class ChildData(Component):
            template = "<b>{{ msg }}</b>"

            def get_template_data(self, args, kwargs, slots, context):
                return {"msg": kwargs.get("msg", "default")}

        @register("parent_data")
        class ParentData(Component):
            template = "<div>{{ child }}</div>"

            def get_template_data(self, args, kwargs, slots, context):
                child_html = ChildData.render(kwargs={"msg": "from parent"})
                return {"child": child_html}

        rendered = ParentData.render()
        assert "<b>from parent</b>" in rendered

    def test_three_level_nesting(self):
        @register("level3")
        class Level3(Component):
            template = "<i>L3</i>"

        @register("level2")
        class Level2(Component):
            template = '<span>{% component "level3" / %}</span>'

        @register("level1")
        class Level1(Component):
            template = '<div>{% component "level2" / %}</div>'

        rendered = Template('{% component "level1" / %}').render(Context())
        assert "<i>L3</i>" in rendered
        assert "<span>" in rendered
        assert "<div>" in rendered

    def test_nested_with_slots(self):
        @register("slotted_inner")
        class SlottedInner(Component):
            template = '<p>{% slot "body" %}empty{% endslot %}</p>'

        @register("slotted_outer")
        class SlottedOuter(Component):
            template = """
                <div>
                    {% component "slotted_inner" %}
                        {% fill "body" %}filled by outer{% endfill %}
                    {% endcomponent %}
                </div>
            """

        rendered = Template('{% component "slotted_outer" / %}').render(Context())
        assert "filled by outer" in rendered


class TestComponentRenderWithContext:
    def setup_method(self):
        registry.clear()

    def teardown_method(self):
        registry.clear()

    def test_render_with_context_dict(self):
        @register("ctx_dict_comp")
        class CtxDictComp(Component):
            template = "<p>{{ extra }}</p>"

            def get_template_data(self, args, kwargs, slots, context):
                return {}

        rendered = CtxDictComp.render(context={"extra": "from_context"})
        assert "from_context" in rendered

    def test_render_with_context_object(self):
        @register("ctx_obj_comp")
        class CtxObjComp(Component):
            template = "<p>{{ extra }}</p>"

            def get_template_data(self, args, kwargs, slots, context):
                return {}

        ctx = Context({"extra": "from_context_obj"})
        rendered = CtxObjComp.render(context=ctx)
        assert "from_context_obj" in rendered
