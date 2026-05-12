from django.apps import AppConfig


class ComponentsConfig(AppConfig):
    name = "django_components"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        pass
