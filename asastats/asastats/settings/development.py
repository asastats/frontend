"""Django settings module used in development."""

from pathlib import Path

from dotenv import load_dotenv
from redis import ConnectionPool

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")


from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

MIDDLEWARE.remove("core.middleware.CustomMinifyHtmlMiddleware")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": get_env_variable("DATABASE_NAME"),
        "USER": get_env_variable("DATABASE_USER"),
        "PASSWORD": get_env_variable("DATABASE_PASSWORD"),
        "HOST": "127.0.0.1",
        "PORT": "",  # '5432',
        # 'CONN_MAX_AGE': 600,  # keeps connections alive for seconds provided
    }
}

# # debug_toolbar
# INSTALLED_APPS += [
#     "debug_toolbar",
#     "template_profiler_panel",
# ]

# MIDDLEWARE.insert(2, "debug_toolbar.middleware.DebugToolbarMiddleware")

# INTERNAL_IPS = ("127.0.0.1",)

# DEBUG_TOOLBAR_PANELS = [
#     # "debug_toolbar.panels.history.HistoryPanel",
#     "debug_toolbar.panels.versions.VersionsPanel",
#     "debug_toolbar.panels.timer.TimerPanel",
#     "debug_toolbar.panels.settings.SettingsPanel",
#     "debug_toolbar.panels.headers.HeadersPanel",
#     "debug_toolbar.panels.request.RequestPanel",
#     "debug_toolbar.panels.sql.SQLPanel",
#     # 'debug_toolbar.panels.staticfiles.StaticFilesPanel',
#     "debug_toolbar.panels.templates.TemplatesPanel",
#     "debug_toolbar.panels.alerts.AlertsPanel",
#     "debug_toolbar.panels.cache.CachePanel",
#     "debug_toolbar.panels.signals.SignalsPanel",
#     "debug_toolbar.panels.redirects.RedirectsPanel",
#     "debug_toolbar.panels.profiling.ProfilingPanel",
#     "template_profiler_panel.panels.template.TemplateProfilerPanel",
# ]
# # debug_toolbar

# # django_cprofile_middleware
# # https://cfpb.github.io/consumerfinance.gov/profiling-django/#profiling-django
# # http://127.0.0.1:8000/2EVGZ4BGOSL3J64UYDE2BUGTNTBZZZLI54VUQQNZZLYCDODLY33UGXNSIU?prof&sort=cumtime
# # http://127.0.0.1:8000/2EVGZ4BGOSL3J64UYDE2BUGTNTBZZZLI54VUQQNZZLYCDODLY33UGXNSIU?prof&download

# DJANGO_CPROFILE_MIDDLEWARE_REQUIRE_STAFF = False
# MIDDLEWARE += [
#     "django_cprofile_middleware.middleware.ProfilerMiddleware",
# ]
# # django_cprofile_middleware

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = "ASA Stats Support <support@asastats.com>"

STATICFILES_DIRS = [
    BASE_DIR.parent / "static",
    "/mnt/data/backup/work/asastats/backup/static/",
]

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    }
}

# CACHES = {
#     "default": {
#         "BACKEND": "django_redis.cache.RedisCache",
#         "LOCATION": f"redis://{REDIS_HOST}:{REDIS_PORT_LOCAL}/1",
#         "OPTIONS": {
#             "PASSWORD": f"{REDIS_AUTH}",
#             "CLIENT_CLASS": "django_redis.client.DefaultClient",
#         },
#         "KEY_PREFIX": "asastats",
#     }
# }

CACHE_TTL = 60 * 90  # Cache time to live is 90 minutes.

USE_CACHED_NODE_DATA = False

# ALGORAND_NODE_PATH = "/opt/node/data/"

# REDIS_PORT = 6380
REDIS_PRIMARY_HOST = "localhost"
REDIS_AUTH = "maysmple1pass3-word"
REDIS_PORT_LOCAL = 6379

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [f"redis://:{REDIS_AUTH}@{REDIS_HOST}:{REDIS_PORT_LOCAL}/0"],
        },
    },
}
