# Acceptance Criteria

## Task 1-7: Previously completed
- [x] All criteria met

## Task 8: Django app config, settings, template loader, finders
- [x] A ComponentsConfig AppConfig class exists with name="django_components"
- [x] A ComponentsSettings class reads configuration from Django settings COMPONENTS dict
- [x] Settings support: autodiscover (bool), dirs (list of paths), context_behavior ("django" or "isolated")
- [x] A ContextBehavior enum/class has DJANGO and ISOLATED values
- [x] A template loader (Loader class) loads templates from component directories
- [x] A static file finder (ComponentFinder class) finds static files in component directories
- [x] Default settings are used when COMPONENTS is not configured
- [x] context_behavior setting affects how slot fills access component context (isolated mode restricts fill to outer context only)

## Task 9: Testing utilities
- [x] djc_test decorator manages component registry state between tests
- [x] Supports django_settings and components_settings overrides
- [x] Supports parametrize for testing with different settings configurations
- [x] Ensures test isolation (registry save/restore, settings override)
- [x] setup_test_config function for configuring Django settings in test environments
- [x] Works on both functions and classes (including nested classes)

## Task 10: Programmatic rendering features
- [x] render_to_response creates Django HttpResponse with response kwargs (content_type, status)
- [x] Component self-referencing (self.name, self.args, self.kwargs, self.slots, self.id, self.request)
- [x] Passing slots as Python objects (strings, callables, Slot instances) to render()
- [x] Nested component rendering in templates and programmatically
- [x] Slot fallback content when no fill provided
