# Acceptance Criteria

## Task 1: Core Component class and registry
- [x] All criteria met (14/14)

## Task 2: Template tags (component, slot, fill)
- [x] All criteria met (9/9)

## Task 3: Advanced slot features
- [x] All criteria met (7/7)

## Task 4: HTML attribute formatting and merging

### Acceptance Criteria
- [ ] `format_attributes({"class": "foo", "id": "bar"})` returns `'class="foo" id="bar"'`
- [ ] `format_attributes({"required": True})` returns `"required"` (boolean attribute)
- [ ] `format_attributes({"disabled": False})` returns `""` (removed)
- [ ] `format_attributes({"data": None})` returns `""` (removed)
- [ ] Special characters in values are HTML-escaped, but SafeString values are not escaped
- [ ] `merge_attributes({"class": "a"}, {"class": "b"})` returns `{"class": "a b"}`
- [ ] `merge_attributes` handles class as dict: `{"class": {"active": True, "hidden": False}}` yields only truthy keys
- [ ] `merge_attributes` handles class as list: `{"class": ["a", "b"]}` joins them
- [ ] `merge_attributes` handles style merging: later styles override earlier property values
- [ ] Style with `None` value is ignored; style with `False` value removes the property
- [ ] Non-class/style attributes are concatenated with space separator
- [ ] An `{% html_attrs %}` template tag renders attributes in templates, accepting positional args for attr dicts and keyword args for individual attrs
- [ ] `{% html_attrs %}` supports a defaults dict that is overridden by explicit attrs
