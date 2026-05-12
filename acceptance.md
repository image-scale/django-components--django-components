# Acceptance Criteria

## Task 1-7: Previously completed
- [x] All criteria met

## Task 8: Django app config, settings, template loader, finders

### Acceptance Criteria
- [ ] A ComponentsConfig AppConfig class exists with name="django_components"
- [ ] A ComponentsSettings class reads configuration from Django settings COMPONENTS dict
- [ ] Settings support: autodiscover (bool), dirs (list of paths), context_behavior ("django" or "isolated")
- [ ] A ContextBehavior enum/class has DJANGO and ISOLATED values
- [ ] A template loader (Loader class) loads templates from component directories
- [ ] A static file finder (ComponentFinder class) finds static files in component directories
- [ ] Default settings are used when COMPONENTS is not configured
- [ ] context_behavior setting affects how slot fills access component context (isolated mode restricts fill to outer context only)
