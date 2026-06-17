"""Django settings module used in production."""

from .base import *

DEBUG = False
ADMINS = [("Ivica", "ipaleka@hopemeet.me")]
SERVER_EMAIL = "admin@asastats.com"

ALLOWED_HOSTS = [
    "127.0.0.1",
    "167.114.67.194",
    "167.114.67.118",
    "192.99.167.63",
    "46.4.59.234",
    "localhost",
    ".asastats.com",
]

CSRF_TRUSTED_ORIGINS = [
    "https://*.asastats.com",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "OPTIONS": {
            "service": "website_service",
            "passfile": get_env_variable("PGPASSFILE"),
        },
    }
}

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

SESSION_ENGINE = "django.contrib.sessions.backends.cache"

MESSAGE_STORAGE = "django.contrib.messages.storage.session.SessionStorage"

SITEMAP_PROTOCOL = "https"

CACHE_TTL = 59 * 90  # Cache time to live is 90 minutes.

COOKIE_ARGUMENTS = {"domain": f"{WEBSITE_DOMAIN}"}

ACCOUNT_DEFAULT_HTTP_PROTOCOL = "https"

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtppro.zoho.eu"
EMAIL_PORT = 587
EMAIL_HOST_USER = get_env_variable("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = get_env_variable("EMAIL_HOST_PASSWORD")
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
DEFAULT_FROM_EMAIL = "ASA Stats Support <support@asastats.com>"

# ALGORAND_NODE_PATH_LIQUIDITY = "/home/asastats/node/"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}
