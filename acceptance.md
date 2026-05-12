# Acceptance Criteria

## Task 1: Core Component class and registry
- [x] All criteria met (14/14)

## Task 2: Template tags (component, slot, fill)

### Acceptance Criteria
- [ ] A `{% component "name" %}{% endcomponent %}` template tag renders a registered component in a Django template
- [ ] The component tag passes keyword arguments to the component, e.g., `{% component "name" key="value" %}`
- [ ] A `{% slot "name" %}default content{% endslot %}` tag in a component template defines a slot with default/fallback content
- [ ] A `{% fill "name" %}custom content{% endfill %}` tag inside a component tag replaces the corresponding slot content
- [ ] If a slot is not filled, its default/fallback content is rendered
- [ ] Multiple named slots can coexist in a single component template
- [ ] Nested component rendering works (component A's template can render component B)
- [ ] Template tags are loadable via `{% load component_tags %}`
- [ ] Context variables from the parent template are accessible inside fill blocks
