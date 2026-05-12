from enum import Enum
from typing import Any, Optional

from django.conf import settings


class ContextBehavior(Enum):
    DJANGO = "django"
    ISOLATED = "isolated"


class ComponentsSettings:
    def _raw(self):
        return getattr(settings, "COMPONENTS", {})

    @property
    def AUTODISCOVER(self) -> bool:
        return self._raw().get("autodiscover", True)

    @property
    def DIRS(self) -> list:
        return self._raw().get("dirs", [])

    @property
    def CONTEXT_BEHAVIOR(self) -> str:
        return self._raw().get("context_behavior", ContextBehavior.DJANGO.value)

    @property
    def TAG_FORMATTER(self) -> Any:
        return self._raw().get("tag_formatter", None)

    @property
    def MULTILINE_TAGS(self) -> bool:
        return self._raw().get("multiline_tags", True)

    @property
    def RELOAD_ON_FILE_CHANGE(self) -> bool:
        return self._raw().get("reload_on_file_change", False)

    def __getitem__(self, key: str) -> Any:
        return self._raw().get(key)

    def get(self, key: str, default: Any = None) -> Any:
        return self._raw().get(key, default)


app_settings = ComponentsSettings()
