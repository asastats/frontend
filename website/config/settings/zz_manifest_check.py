from .automated_tests import *  # noqa: F401,F403

STORAGES = {
    **STORAGES,  # noqa: F405
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"
    },
}
if (BASE_DIR.parent / "static" / "build").is_dir():  # noqa: F405
    STATICFILES_DIRS.insert(0, BASE_DIR.parent / "static" / "build")  # noqa: F405
