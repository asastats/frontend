"""Pluggable DAO voting backend for the open frontend; see docs/logbook.md.

Named by ``settings.DAO_PROVIDER`` and resolved lazily, like the permission
provider, so the frontend boots without the Voting dApp submodule.
"""

from functools import lru_cache

from django.conf import settings
from django.dispatch import receiver
from django.test.signals import setting_changed
from django.utils.module_loading import import_string


class DaoProvider:
    """Default backend: no voting on this site. Every method degrades safely."""

    network = ""
    app_id = None
    permission_app_id = None

    def available(self):
        """Return True if this site reads a deployed Voting dApp.

        :return: Boolean
        """
        return False

    def current_round(self):
        """Return the network's latest round, None if unknown.

        :return: int
        """
        return None

    def session_count(self):
        """Return how many sessions the Voting dApp has created.

        :return: int
        """
        return 0

    def session(self, session_id):
        """Return the decoded session box, None if there is no such session.

        :param session_id: voting session identifier
        :type session_id: int
        :return: dict
        """
        return None

    def ballots(self, session_id):
        """Return the session's decoded ballot boxes keyed by seat address.

        :param session_id: voting session identifier
        :type session_id: int
        :return: dict
        """
        return {}

    def seat_votes(self):
        """Return every governor seat's maximum votes, keyed by address.

        :return: dict
        """
        return {}

    def vote_method(self):
        """Return the ARC-4 signature of the dApp's `vote` method, None if unknown.

        :return: str
        """
        return None

    def document(self, session_id, name):
        """Return a session's published file (``proposal.md``, ``final.json``, ``sofar.json``).

        :param session_id: voting session identifier
        :type session_id: int
        :param name: file name
        :type name: str
        :return: bytes, or None when it is not published on this site
        """
        return None


@lru_cache(maxsize=1)
def get_dao_provider():
    """Return the configured DAO provider instance, built once.

    :var dotted: dotted path to the provider class, or empty
    :type dotted: str
    :return: :class:`DaoProvider`
    """
    dotted = getattr(settings, "DAO_PROVIDER", None)
    if not dotted:
        return DaoProvider()

    return import_string(dotted)()


@receiver(setting_changed)
def _reset_dao_provider_cache(*, setting, **kwargs):
    """Clear the cached provider when a DAO setting changes, e.g. in tests.

    :param setting: name of the changed setting
    :type setting: str
    :return: None
    """
    if setting.startswith("DAO_"):
        get_dao_provider.cache_clear()
