# Acceptance Criteria

## Task 1-6: Previously completed
- [x] All criteria met

## Task 7: Tag formatters

### Acceptance Criteria
- [ ] A TagFormatterABC abstract base class defines the interface for tag formatters with start_tag, end_tag, and parse methods
- [ ] A ComponentFormatter (default) generates `{% component "name" %}{% endcomponent %}` syntax
- [ ] A ShorthandComponentFormatter generates `{% name %}{% endname %}` shorthand syntax
- [ ] Tag formatters return a TagResult containing the component name and remaining tokens
- [ ] ComponentFormatter.start_tag("calendar") returns "component" and end_tag returns "endcomponent"
- [ ] ShorthandComponentFormatter.start_tag("calendar") returns "calendar" and end_tag returns "endcalendar"
- [ ] Formatters can be set per registry via RegistrySettings
- [ ] component_formatter and component_shorthand_formatter are pre-built formatter instances
