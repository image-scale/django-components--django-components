import os
from typing import List, Tuple

from django.contrib.staticfiles.finders import BaseFinder
from django.core.files.storage import FileSystemStorage


class ComponentFinder(BaseFinder):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.storages = {}

    def _get_component_dirs(self) -> List[str]:
        from django_components.app_settings import app_settings
        return app_settings.DIRS

    def find(self, path: str, all: bool = False) -> str | List[str]:
        matches = []
        for component_dir in self._get_component_dirs():
            full_path = os.path.join(component_dir, path)
            if os.path.isfile(full_path):
                if not all:
                    return full_path
                matches.append(full_path)
        return matches if all else ""

    def list(self, ignore_patterns: List[str] | None = None) -> List[Tuple[str, FileSystemStorage]]:
        results = []
        for component_dir in self._get_component_dirs():
            if not os.path.isdir(component_dir):
                continue
            storage = FileSystemStorage(location=component_dir)
            for root, dirs, files in os.walk(component_dir):
                for f in files:
                    rel_path = os.path.relpath(os.path.join(root, f), component_dir)
                    if ignore_patterns:
                        skip = False
                        for pattern in ignore_patterns:
                            if rel_path.startswith(pattern):
                                skip = True
                                break
                        if skip:
                            continue
                    results.append((rel_path, storage))
        return results
