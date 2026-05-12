from typing import Any, Optional

from django.utils.safestring import mark_safe


class Script:
    def __init__(self, content: Optional[str] = None, url: Optional[str] = None, attrs: Optional[dict] = None):
        self.content = content
        self.url = url
        self.attrs = attrs or {}

    def render(self) -> str:
        if self.url:
            extra = self._render_attrs()
            return f'<script src="{self.url}"{extra}></script>'
        if self.content:
            extra = self._render_attrs()
            return f'<script{extra}>{self.content}</script>'
        return ""

    def _render_attrs(self) -> str:
        if not self.attrs:
            return ""
        parts = []
        for key, val in self.attrs.items():
            if val is True:
                parts.append(f" {key}")
            elif val is not None and val is not False:
                parts.append(f' {key}="{val}"')
        return "".join(parts)

    def __eq__(self, other):
        if not isinstance(other, Script):
            return NotImplemented
        return self.content == other.content and self.url == other.url

    def __hash__(self):
        return hash(("script", self.content, self.url))

    def __repr__(self):
        if self.url:
            return f"Script(url={self.url!r})"
        return f"Script(content={self.content!r})"


class Style:
    def __init__(self, content: Optional[str] = None, url: Optional[str] = None, attrs: Optional[dict] = None):
        self.content = content
        self.url = url
        self.attrs = attrs or {}

    def render(self) -> str:
        if self.url:
            extra = self._render_attrs()
            return f'<link rel="stylesheet" href="{self.url}"{extra}>'
        if self.content:
            extra = self._render_attrs()
            return f'<style{extra}>{self.content}</style>'
        return ""

    def _render_attrs(self) -> str:
        if not self.attrs:
            return ""
        parts = []
        for key, val in self.attrs.items():
            if val is True:
                parts.append(f" {key}")
            elif val is not None and val is not False:
                parts.append(f' {key}="{val}"')
        return "".join(parts)

    def __eq__(self, other):
        if not isinstance(other, Style):
            return NotImplemented
        return self.content == other.content and self.url == other.url

    def __hash__(self):
        return hash(("style", self.content, self.url))

    def __repr__(self):
        if self.url:
            return f"Style(url={self.url!r})"
        return f"Style(content={self.content!r})"


_CSS_PLACEHOLDER = "<!-- COMPONENT_CSS_DEPENDENCIES -->"
_JS_PLACEHOLDER = "<!-- COMPONENT_JS_DEPENDENCIES -->"

_collected_scripts: list[Script] = []
_collected_styles: list[Style] = []


def reset_dependency_tracker():
    global _collected_scripts, _collected_styles
    _collected_scripts = []
    _collected_styles = []


def register_component_dependencies(component_cls):
    media_cls = getattr(component_cls, 'Media', None)
    if media_cls is None:
        return

    js_items = getattr(media_cls, 'js', None)
    css_items = getattr(media_cls, 'css', None)

    if js_items:
        if isinstance(js_items, str):
            js_items = [js_items]
        for item in js_items:
            if isinstance(item, Script):
                script = item
            elif isinstance(item, str):
                script = Script(url=item)
            else:
                continue
            if script not in _collected_scripts:
                _collected_scripts.append(script)

    if css_items:
        if isinstance(css_items, str):
            css_items = [css_items]
        if isinstance(css_items, dict):
            all_urls = []
            for media_type, urls in css_items.items():
                if isinstance(urls, str):
                    urls = [urls]
                all_urls.extend(urls)
            css_items = all_urls
        for item in css_items:
            if isinstance(item, Style):
                style = item
            elif isinstance(item, str):
                style = Style(url=item)
            else:
                continue
            if style not in _collected_styles:
                _collected_styles.append(style)


def render_collected_css() -> str:
    parts = []
    for style in _collected_styles:
        parts.append(style.render())
    return mark_safe("\n".join(parts))


def render_collected_js() -> str:
    parts = []
    for script in _collected_scripts:
        parts.append(script.render())
    return mark_safe("\n".join(parts))


def render_dependencies(html: str) -> str:
    if _CSS_PLACEHOLDER in html:
        html = html.replace(_CSS_PLACEHOLDER, render_collected_css())
    if _JS_PLACEHOLDER in html:
        html = html.replace(_JS_PLACEHOLDER, render_collected_js())
    return html
