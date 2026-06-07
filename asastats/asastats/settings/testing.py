"""Django settings module used in testing."""

from .base import *

DEBUG = False
ADMINS = [("Ivica", "ipaleka@hopemeet.me")]

ALLOWED_HOSTS = ["127.0.0.1", "192.168.1.125", "localhost", "webserver"]
INTERNAL_IPS = ("127.0.0.1",)

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6380/1",
        "OPTIONS": {
            "PASSWORD": f"{REDIS_AUTH}",
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
        "KEY_PREFIX": "asastats",
    }
}
CACHE_TTL = 60 * 90  # Cache time to live is 90 minutes.

ALGORAND_NODE_PATH = "/var/lib/algorand/"

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtppro.zoho.eu"
EMAIL_PORT = 587
EMAIL_HOST_USER = get_env_variable("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = get_env_variable("EMAIL_HOST_PASSWORD")
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
DEFAULT_FROM_EMAIL = "ASA Stats Support <support@asastats.com>"
