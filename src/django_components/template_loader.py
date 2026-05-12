import os
from typing import List, Optional

from django.template import Origin, TemplateDoesNotExist
from django.template.loaders.base import Loader as BaseLoader


class Loader(BaseLoader):
    def get_dirs(self) -> List[str]:
        from django_components.app_settings import app_settings
        return app_settings.DIRS

    def get_template_sources(self, template_name: str, template_dirs: Optional[List[str]] = None):
        dirs = template_dirs or self.get_dirs()
        for d in dirs:
            filepath = os.path.join(d, template_name)
            yield Origin(
                name=filepath,
                template_name=template_name,
                loader=self,
            )

    def get_contents(self, origin: Origin) -> str:
        try:
            with open(origin.name, encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            raise TemplateDoesNotExist(origin)
