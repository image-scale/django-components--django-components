import sys
from pathlib import Path

import django
from django.conf import settings


def setup_test_django():
    if settings.configured:
        return
    settings.configure(
        BASE_DIR=Path(__file__).resolve().parent,
        INSTALLED_APPS=["django.contrib.contenttypes"],
        TEMPLATES=[
            {
                "BACKEND": "django.template.backends.django.DjangoTemplates",
                "DIRS": [str(Path(__file__).resolve().parent / "templates")],
                "OPTIONS": {
                    "loaders": [
                        "django.template.loaders.filesystem.Loader",
                        "django.template.loaders.app_directories.Loader",
                    ],
                },
            },
        ],
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": ":memory:",
            },
        },
        SECRET_KEY="test-secret-key",
    )
    django.setup()


# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
