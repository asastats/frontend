"""Django settings module used in production."""

from redis import ConnectionPool

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
    ".asastats.link",
]

CSRF_TRUSTED_ORIGINS = [
    "https://*.asastats.com",
    "https://*.asastats.link",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "OPTIONS": {
            "service": "asastats_service",
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
        "KEY_PREFIX": "asastats",
    }
}

SESSION_ENGINE = "django.contrib.sessions.backends.cache"

MESSAGE_STORAGE = "django.contrib.messages.storage.session.SessionStorage"

SITEMAP_PROTOCOL = "https"

CACHE_TTL = 59 * 90  # Cache time to live is 90 minutes.

COOKIE_ARGUMENTS = {"domain": "www.asastats.com"}

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

connection_pool = ConnectionPool(
    host=REDIS_PRIMARY_HOST, port=REDIS_PORT, password=REDIS_AUTH, max_connections=20
)
HUEY = {
    # 'huey_class': 'huey.RedisHuey',  # Huey implementation to use.
    # 'name': settings.DATABASES['default']['NAME'],  # Use db name for huey.
    "name": "tax-processing",
    # 'results': True,  # Store return values of tasks.
    # 'store_none': False,  # If a task returns None, do not save to results.
    # "immediate": False,  # If DEBUG=True, run synchronously.
    # 'utc': True,  # Use UTC for all times internally.
    # 'blocking': False,  # Perform blocking pop rather than poll Redis.
    "connection": {
        # 'host': REDIS_PRIMARY_HOST,
        # 'port': REDIS_PORT,
        # 'db': 0,
        "connection_pool": connection_pool,  # Definitely you should use pooling!
        # ... tons of other options, see redis-py for details.
        # huey-specific connection parameters.
        # 'read_timeout': 1,  # If not polling (blocking pop), use timeout.
        # 'url': None,  # Allow Redis config via a DSN.
    },
    "consumer": {
        "workers": 10,
        "worker_type": "thread",  # "worker_type": "greenlet", "thread"
        # 'initial_delay': 0.1,  # Smallest polling interval, same as -d.
        # 'backoff': 1.15,  # Exponential backoff using this rate, -b.
        # 'max_delay': 10.0,  # Max possible polling interval, -m.
        # 'scheduler_interval': 1,  # Check schedule every second, -s.
        # 'periodic': True,  # Enable crontab feature.
        # 'check_worker_health': True,  # Enable worker health checks.
        # 'health_check_interval': 1,  # Check worker health every second.
    },
}
