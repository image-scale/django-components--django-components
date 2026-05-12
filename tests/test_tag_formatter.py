import pytest

from django_components import (
    ComponentFormatter,
    ShorthandComponentFormatter,
    TagFormatterABC,
    TagResult,
    component_formatter,
    component_shorthand_formatter,
    RegistrySettings,
)


class TestComponentFormatter:
    def test_start_tag(self):
        f = ComponentFormatter()
        assert f.start_tag("calendar") == "component"
        assert f.start_tag("button") == "component"

    def test_end_tag(self):
        f = ComponentFormatter()
        assert f.end_tag("calendar") == "endcomponent"
        assert f.end_tag("button") == "endcomponent"

    def test_parse_quoted_name(self):
        f = ComponentFormatter()
        result = f.parse(['"calendar"', 'key="val"'])
        assert result.component_name == "calendar"
        assert result.tokens == ['key="val"']

    def test_parse_unquoted_name(self):
        f = ComponentFormatter()
        result = f.parse(["calendar", 'key="val"'])
        assert result.component_name == "calendar"
        assert result.tokens == ['key="val"']

    def test_parse_single_quotes(self):
        f = ComponentFormatter()
        result = f.parse(["'my_comp'"])
        assert result.component_name == "my_comp"

    def test_parse_empty_tokens_raises(self):
        f = ComponentFormatter()
        with pytest.raises(ValueError):
            f.parse([])


class TestShorthandFormatter:
    def test_start_tag(self):
        f = ShorthandComponentFormatter()
        assert f.start_tag("calendar") == "calendar"
        assert f.start_tag("button") == "button"

    def test_end_tag(self):
        f = ShorthandComponentFormatter()
        assert f.end_tag("calendar") == "endcalendar"
        assert f.end_tag("button") == "endbutton"

    def test_parse_returns_empty_name(self):
        f = ShorthandComponentFormatter()
        result = f.parse(['key="val"'])
        assert result.component_name == ""
        assert result.tokens == ['key="val"']


class TestTagFormatterABC:
    def test_cannot_instantiate_abc(self):
        with pytest.raises(TypeError):
            TagFormatterABC()

    def test_subclass_must_implement_methods(self):
        class Incomplete(TagFormatterABC):
            pass

        with pytest.raises(TypeError):
            Incomplete()


class TestTagResult:
    def test_tag_result_is_named_tuple(self):
        r = TagResult(component_name="test", tokens=["a", "b"])
        assert r.component_name == "test"
        assert r.tokens == ["a", "b"]
        assert r[0] == "test"
        assert r[1] == ["a", "b"]


class TestPrebuiltInstances:
    def test_component_formatter_instance(self):
        assert isinstance(component_formatter, ComponentFormatter)
        assert component_formatter.start_tag("x") == "component"

    def test_shorthand_formatter_instance(self):
        assert isinstance(component_shorthand_formatter, ShorthandComponentFormatter)
        assert component_shorthand_formatter.start_tag("x") == "x"


class TestRegistrySettingsFormatter:
    def test_registry_settings_accepts_formatter(self):
        settings = RegistrySettings(tag_formatter=component_shorthand_formatter)
        assert settings.tag_formatter is component_shorthand_formatter

    def test_registry_settings_default_formatter_none(self):
        settings = RegistrySettings()
        assert settings.tag_formatter is None
