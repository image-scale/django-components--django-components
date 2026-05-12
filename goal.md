# Goal

## Project
django-components — a python project.

## Description
A modular and extensible UI framework for Django that enables reusable, self-contained template components. Each component bundles its own HTML template, CSS, and JavaScript, similar to modern frontend frameworks like Vue or React. The framework provides a component registry for managing components, a slot system for content injection (including scoped slots), HTML attribute merging with Vue-like class/style handling, a provide/inject pattern for passing data through the component tree, JS/CSS dependency management, component rendering via template tags, and testing utilities. Users define components as Python classes, register them, and use them in Django templates with custom template tags.

## Scope
- ~15 production source files to implement
- ~12 test files to write
- Reproduce core source code, tests, and configuration

## Core Capabilities
1. Component class with template, CSS, JS support and rendering
2. Component registry with register/unregister/get/has/all/clear
3. Template tags: component, slot, fill, html_attrs, provide, component_css_dependencies, component_js_dependencies
4. Slot system with default content, required slots, named slots, default slots, and scoped slots (data passing)
5. HTML attribute formatting and merging with Vue-like class/style normalization
6. Provide/inject pattern for ancestor-to-descendant data passing
7. JS/CSS dependency management and rendering
8. Tag formatters for customizable template tag syntax
9. Component media (additional JS/CSS via Media inner class)
10. Settings/configuration system
11. Django app configuration (AppConfig)
12. Template loader for component templates
13. Static file finders for component assets
14. Testing utilities (djc_test decorator)
15. Context behavior modes (django vs isolated)
