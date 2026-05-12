# Acceptance Criteria

## Task 1: Core Component class and registry
- [x] All criteria met (14/14)

## Task 2: Template tags (component, slot, fill)
- [x] All criteria met (9/9)

## Task 3: Advanced slot features

### Acceptance Criteria
- [ ] Required slots (`{% slot "name" required %}`) raise a TemplateSyntaxError when not filled
- [ ] Default slot flag (`{% slot "name" default %}`) captures non-fill content from the component body as the default slot fill
- [ ] Scoped slots: slot tags accept keyword data args (`{% slot "name" data1="val" %}`), and fill tags can receive them via a data variable (`{% fill "name" data="slot_data" %}` then `{{ slot_data.data1 }}`)
- [ ] Fill tags can access slot fallback content via a fallback variable (`{% fill "name" fallback="fb" %}` then `{{ fb }}`)
- [ ] Slots can be self-closing (`{% slot "name" / %}`)
- [ ] Required slots don't raise if they ARE filled
- [ ] Scoped slot data is resolved from context variables, not just literal strings
