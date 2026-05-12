import pytest
from django.template import Context, Template
from django.utils.safestring import SafeString, mark_safe

from django_components import Component, register, registry
from django_components.attributes import format_attributes, merge_attributes


class TestFormatAttributes:
    def test_single_attribute(self):
        result = format_attributes({"foo": "bar"})
        assert result == 'foo="bar"'

    def test_multiple_attributes(self):
        result = format_attributes({"class": "foo", "style": "color: red;"})
        assert 'class="foo"' in result
        assert 'style="color: red;"' in result

    def test_boolean_attribute_true(self):
        result = format_attributes({"required": True})
        assert result == "required"

    def test_boolean_attribute_false(self):
        result = format_attributes({"disabled": False})
        assert result == ""

    def test_none_value_omitted(self):
        result = format_attributes({"data": None})
        assert result == ""

    def test_escapes_special_characters(self):
        result = format_attributes({"onclick": "alert('hi')"})
        assert "&#x27;" in result

    def test_safe_string_not_escaped(self):
        result = format_attributes({"foo": mark_safe("'bar'")})
        assert "'" in result
        assert "&#x27;" not in result

    def test_result_is_safe_string(self):
        result = format_attributes({"a": "b"})
        assert isinstance(result, SafeString)

    def test_multiple_bool_and_value_attrs(self):
        result = format_attributes({"id": "main", "required": True, "hidden": False})
        assert 'id="main"' in result
        assert "required" in result
        assert "hidden" not in result

    def test_integer_value(self):
        result = format_attributes({"data-count": 5})
        assert 'data-count="5"' in result


class TestMergeAttributes:
    def test_single_dict(self):
        result = merge_attributes({"foo": "bar"})
        assert result == {"foo": "bar"}

    def test_merge_non_class_non_style(self):
        result = merge_attributes({"foo": "bar"}, {"foo": "baz"})
        assert result == {"foo": "bar baz"}

    def test_merge_different_keys(self):
        result = merge_attributes({"a": "1"}, {"b": "2"})
        assert result == {"a": "1", "b": "2"}

    def test_merge_classes_strings(self):
        result = merge_attributes({"class": "a"}, {"class": "b"})
        assert result == {"class": "a b"}

    def test_merge_classes_dict_truthy(self):
        result = merge_attributes({"class": {"active": True, "hidden": False}})
        assert result["class"] == "active"

    def test_merge_classes_list(self):
        result = merge_attributes({"class": ["x", "y"]})
        assert "x" in result["class"]
        assert "y" in result["class"]

    def test_merge_classes_complex(self):
        result = merge_attributes(
            {"class": "foo"},
            {"class": ["bar", {"baz": True, "qux": False}]},
        )
        assert "foo" in result["class"]
        assert "bar" in result["class"]
        assert "baz" in result["class"]
        assert "qux" not in result["class"]

    def test_merge_styles_strings(self):
        result = merge_attributes(
            {"style": "color: red;"},
            {"style": "width: 100px;"},
        )
        assert "color: red" in result["style"]
        assert "width: 100px" in result["style"]

    def test_merge_styles_override(self):
        result = merge_attributes(
            {"style": "color: red;"},
            {"style": "color: blue;"},
        )
        assert "color: blue" in result["style"]
        assert "color: red" not in result["style"]

    def test_merge_styles_dict_false_removes(self):
        result = merge_attributes(
            {"style": "color: red; width: 100px;"},
            {"style": {"color": False}},
        )
        assert "color" not in result["style"]
        assert "width: 100px" in result["style"]

    def test_merge_styles_dict_none_ignored(self):
        result = merge_attributes(
            {"style": "color: red;"},
            {"style": {"color": None}},
        )
        assert "color: red" in result["style"]

    def test_merge_with_empty(self):
        result = merge_attributes({}, {"foo": "bar"})
        assert result == {"foo": "bar"}


class TestHtmlAttrsTag:
    def setup_method(self):
        registry.clear()

    def teardown_method(self):
        registry.clear()

    def test_html_attrs_basic_kwargs(self):
        @register("attrtag")
        class AttrComp(Component):
            template = '<div {% html_attrs class="my-class" id="main" %}></div>'

        tmpl = Template('{% component "attrtag" %}{% endcomponent %}')
        rendered = tmpl.render(Context())
        assert 'class="my-class"' in rendered
        assert 'id="main"' in rendered

    def test_html_attrs_with_positional_dict(self):
        @register("attrtag2")
        class AttrComp2(Component):
            template = '<div {% html_attrs attrs %}></div>'

            def get_template_data(self, args, kwargs, slots, context):
                return {"attrs": {"data-value": "123", "class": "extra"}}

        tmpl = Template('{% component "attrtag2" %}{% endcomponent %}')
        rendered = tmpl.render(Context())
        assert 'data-value="123"' in rendered
        assert 'class="extra"' in rendered

    def test_html_attrs_defaults_overridden(self):
        @register("attrtag3")
        class AttrComp3(Component):
            template = '<div {% html_attrs defaults:class="default-class" class="override-class" %}></div>'

        tmpl = Template('{% component "attrtag3" %}{% endcomponent %}')
        rendered = tmpl.render(Context())
        assert "default-class" in rendered
        assert "override-class" in rendered

    def test_html_attrs_merges_positional_and_kwargs(self):
        @register("attrtag4")
        class AttrComp4(Component):
            template = '<div {% html_attrs attrs class="extra" %}></div>'

            def get_template_data(self, args, kwargs, slots, context):
                return {"attrs": {"class": "base", "id": "main"}}

        tmpl = Template('{% component "attrtag4" %}{% endcomponent %}')
        rendered = tmpl.render(Context())
        assert "base" in rendered
        assert "extra" in rendered
        assert 'id="main"' in rendered
