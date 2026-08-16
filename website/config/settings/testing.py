"""Django settings module used in testing."""

from .base import *

DEBUG = True
ADMINS = [("Ivica", "ipaleka@hopemeet.me")]

ALLOWED_HOSTS = [
    "127.0.0.1",
    "192.168.1.102",
    "localhost",
    "webserver",
    f".{WEBSITE_BASE_DOMAIN}",
]
INTERNAL_IPS = ("127.0.0.1",)

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"redis://{REDIS_HOST}:{REDIS_PORT_LOCAL}/1",
        "OPTIONS": {
            "PASSWORD": f"{REDIS_AUTH}",
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
        "KEY_PREFIX": "website",
    }
}

CACHE_TTL = 60 * 90  # Cache time to live is 90 minutes.

ALGORAND_NODE_PATH = "/var/lib/algorand/"

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

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtppro.zoho.eu"
EMAIL_PORT = 587
EMAIL_HOST_USER = get_env_variable("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = get_env_variable("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
DEFAULT_FROM_EMAIL = f"{WEBSITE_NAME} Support <support@{WEBSITE_BASE_DOMAIN}>"

WALLET_TEST_MODE = True

# Content-hashed static filenames. See the STORAGES note in base.py: this is
# what makes `Cache-Control: immutable` correct rather than a gamble, and it is
# why templates name sources (`js/site.js`) rather than build outputs.
#
# static/build comes FIRST so collectstatic prefers the minified copy produced
# by ./build-static.sh over the readable source of the same name. When that
# directory is absent -- a checkout that has not run the build -- the source is
# collected instead and the site works, just larger.
STORAGES = {
    **STORAGES,
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"
    },
}

if (BASE_DIR.parent / "static" / "build").is_dir():
    STATICFILES_DIRS.insert(0, BASE_DIR.parent / "static" / "build")
