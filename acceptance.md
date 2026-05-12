# Acceptance Criteria

## Task 1: Core Component class and registry

### Acceptance Criteria
- [ ] A Component base class exists that users subclass to create components
- [ ] Components can define inline templates via a `template` class attribute (string)
- [ ] Components implement `get_template_data(self, args, kwargs, slots, context)` to return template context variables
- [ ] `Component.render(kwargs={"key": "value"})` returns rendered HTML string with variables interpolated
- [ ] `Component.render(args=[1, 2])` passes positional args to get_template_data
- [ ] A ComponentRegistry class exists with register(name, component), unregister(name), get(name), has(name), all(), and clear() methods
- [ ] A default global `registry` instance is available
- [ ] A `@register("name")` decorator registers a component with the global registry
- [ ] `@register("name", registry=custom_reg)` registers with a custom registry
- [ ] Registering a different component class under the same name raises AlreadyRegistered
- [ ] Re-registering the same component class under the same name is allowed (no error)
- [ ] Unregistering a name that doesn't exist raises NotRegistered
- [ ] Component.render() works without registration (standalone rendering)
- [ ] Components can access self.name, returning the registered name or class name as fallback
