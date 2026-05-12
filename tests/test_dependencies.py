import pytest
from django.template import Context, Template

from django_components import Component, Script, Style, register, registry, render_dependencies
from django_components.dependencies import (
    _CSS_PLACEHOLDER,
    _JS_PLACEHOLDER,
    render_collected_css,
    render_collected_js,
    reset_dependency_tracker,
)


class TestScript:
    def test_script_with_url(self):
        s = Script(url="/static/app.js")
        assert s.render() == '<script src="/static/app.js"></script>'

    def test_script_with_content(self):
        s = Script(content="console.log('hello');")
        assert s.render() == "<script>console.log('hello');</script>"

    def test_script_with_attrs(self):
        s = Script(url="/app.js", attrs={"async": True, "type": "module"})
        rendered = s.render()
        assert "async" in rendered
        assert 'type="module"' in rendered

    def test_script_equality(self):
        a = Script(url="/app.js")
        b = Script(url="/app.js")
        c = Script(url="/other.js")
        assert a == b
        assert a != c

    def test_script_empty(self):
        s = Script()
        assert s.render() == ""


class TestStyle:
    def test_style_with_url(self):
        s = Style(url="/static/style.css")
        assert s.render() == '<link rel="stylesheet" href="/static/style.css">'

    def test_style_with_content(self):
        s = Style(content=".container { color: red; }")
        assert s.render() == "<style>.container { color: red; }</style>"

    def test_style_with_attrs(self):
        s = Style(url="/style.css", attrs={"media": "print"})
        rendered = s.render()
        assert 'media="print"' in rendered

    def test_style_equality(self):
        a = Style(url="/style.css")
        b = Style(url="/style.css")
        c = Style(url="/other.css")
        assert a == b
        assert a != c

    def test_style_empty(self):
        s = Style()
        assert s.render() == ""


class TestMediaCollection:
    def setup_method(self):
        registry.clear()
        reset_dependency_tracker()

    def teardown_method(self):
        registry.clear()
        reset_dependency_tracker()

    def test_component_media_js(self):
        @register("media_comp")
        class MediaComp(Component):
            template = "<div>content</div>"
            class Media:
                js = ["app.js", "lib.js"]

        tmpl = Template('{% component "media_comp" %}{% endcomponent %}')
        tmpl.render(Context())

        js_html = render_collected_js()
        assert '<script src="app.js"></script>' in js_html
        assert '<script src="lib.js"></script>' in js_html

    def test_component_media_css(self):
        @register("css_comp")
        class CssComp(Component):
            template = "<div>styled</div>"
            class Media:
                css = ["base.css", "theme.css"]

        tmpl = Template('{% component "css_comp" %}{% endcomponent %}')
        tmpl.render(Context())

        css_html = render_collected_css()
        assert '<link rel="stylesheet" href="base.css">' in css_html
        assert '<link rel="stylesheet" href="theme.css">' in css_html

    def test_deduplication(self):
        @register("dup_comp")
        class DupComp(Component):
            template = "<div>dup</div>"
            class Media:
                js = ["shared.js"]

        tmpl = Template('{% component "dup_comp" %}{% endcomponent %}{% component "dup_comp" %}{% endcomponent %}')
        tmpl.render(Context())

        js_html = render_collected_js()
        assert js_html.count("shared.js") == 1


class TestDependencyTags:
    def setup_method(self):
        registry.clear()
        reset_dependency_tracker()

    def teardown_method(self):
        registry.clear()
        reset_dependency_tracker()

    def test_css_dependencies_tag(self):
        @register("styled")
        class StyledComp(Component):
            template = "<div>styled</div>"
            class Media:
                css = ["main.css"]

        tmpl = Template('{% component "styled" %}{% endcomponent %}{% component_css_dependencies %}')
        rendered = tmpl.render(Context())
        assert '<link rel="stylesheet" href="main.css">' in rendered

    def test_js_dependencies_tag(self):
        @register("scripted")
        class ScriptedComp(Component):
            template = "<div>scripted</div>"
            class Media:
                js = ["main.js"]

        tmpl = Template('{% component "scripted" %}{% endcomponent %}{% component_js_dependencies %}')
        rendered = tmpl.render(Context())
        assert '<script src="main.js"></script>' in rendered


class TestRenderDependencies:
    def setup_method(self):
        reset_dependency_tracker()

    def teardown_method(self):
        reset_dependency_tracker()

    def test_render_dependencies_replaces_placeholders(self):
        from django_components.dependencies import _collected_scripts, _collected_styles
        _collected_styles.append(Style(url="style.css"))
        _collected_scripts.append(Script(url="app.js"))

        html = f"<head>{_CSS_PLACEHOLDER}</head><body>Content{_JS_PLACEHOLDER}</body>"
        result = render_dependencies(html)
        assert '<link rel="stylesheet" href="style.css">' in result
        assert '<script src="app.js"></script>' in result
        assert _CSS_PLACEHOLDER not in result
        assert _JS_PLACEHOLDER not in result

    def test_render_dependencies_no_placeholders(self):
        html = "<div>No deps</div>"
        result = render_dependencies(html)
        assert result == html
