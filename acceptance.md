# Acceptance Criteria

## Task 1-4: Previously completed
- [x] All criteria met

## Task 5: Provide/Inject pattern

### Acceptance Criteria
- [ ] `{% provide "name" key="val" another=1 %}...{% endprovide %}` makes data available to nested components
- [ ] `self.inject("name")` inside get_template_data returns an object with attributes matching the provide kwargs (e.g., `.key`, `.another`)
- [ ] `self.inject("name", default)` returns default if no provider found
- [ ] Provide data is scoped to the provide block (not accessible outside it)
- [ ] Multiple provides can coexist with different names
- [ ] Nested provides with the same name: inner overrides outer for components inside the inner block
- [ ] Self-closing provide tag works: `{% provide "name" key="val" / %}`
