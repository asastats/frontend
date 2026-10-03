"""Session engine: cache first, the database behind it, keeping sessions made before.

See docs/logbook.md (website/core/sessions.py, 2026-10-03).
"""

from django.contrib.sessions.backends.base import CreateError, UpdateError
from django.contrib.sessions.backends.cache import KEY_PREFIX as CACHE_ONLY_KEY_PREFIX
from django.contrib.sessions.backends.cached_db import SessionStore as CachedDbStore


class SessionStore(CachedDbStore):
    """`cached_db`, reading the cache keys the cache-only engine wrote.

    :var cache_key_prefix: the cache-only engine's prefix, so its sessions survive
    :type cache_key_prefix: str
    """

    cache_key_prefix = CACHE_ONLY_KEY_PREFIX

    def save(self, must_create=False):
        """Save, creating the database row a cache-only session never had.

        :param must_create: whether this save must create a new session
        :type must_create: Boolean
        """
        try:
            super().save(must_create)
        except UpdateError:
            try:
                super().save(must_create=True)
            except CreateError:
                # another request created the row in the meantime
                super().save(must_create=False)
