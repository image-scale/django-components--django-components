# Acceptance Criteria

## Task 1-5: Previously completed
- [x] All criteria met

## Task 6: JS/CSS dependency management

### Acceptance Criteria
- [ ] A Script class represents a JavaScript dependency, supporting both inline content and external URLs
- [ ] A Style class represents a CSS dependency, supporting both inline content and external URLs
- [ ] Script(content="...") renders as `<script>...</script>`
- [ ] Script(url="/path/to/file.js") renders as `<script src="/path/to/file.js"></script>`
- [ ] Style(content="...") renders as `<style>...</style>`
- [ ] Style(url="/path/to/file.css") renders as `<link rel="stylesheet" href="/path/to/file.css">`
- [ ] Components can define a Media inner class with js and css lists of paths
- [ ] `{% component_css_dependencies %}` and `{% component_js_dependencies %}` template tags render collected dependencies
- [ ] Dependencies are collected from rendered components and deduplicated
- [ ] A render_dependencies function processes rendered HTML to insert JS/CSS at placeholder locations
